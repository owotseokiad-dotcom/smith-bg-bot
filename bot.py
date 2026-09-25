import discord, os, re, asyncio
from discord.ext import commands, tasks
from openai import OpenAI
from datetime import datetime, timedelta
from collections import defaultdict

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mémoire des activités
derniere_activite = defaultdict(lambda: datetime.now())
deja_relance = {}

# MAP de tous tes salons
SALONS = {
    "bienvenue": "bienvenue",
    "entraide": "entraide-général",
    "bilan": "bilan-session-de-problème",
    "support": "support-créer",
    "reel": "reel-dessa",
    "ciblage": "correction-mauvais-ciblage",
    "creation": "création-compte",
    "tuto": "tutoriel-création",
    "bio": "bio",
    "pseudos": "pseudos",
    "photo": "photo-de-profil",
    "story": "story-cta",
    "caption": "caption-story-cta",
    "comptes": "comptes-à-suivre",
    "formation": "formation-écrite",
}

SYSTEM_PROMPT = f"""
Tu es Smith BG, le MANAGER TOTAL de l'agence RAMANE OFM. Tu remplaces le boss à 100%.

SALONS DISPONIBLES : {SALONS}

TON JOB :
1. Tu réponds à TOUT : Gmail qui se fait bloquer, création compte Insta, Reels 0 vues, bio, pseudo, photo, shadowban, bloqué, paiement.
2. Tu donnes la solution en 2-3 étapes claires et directes.
3. Tu rediriges TOUJOURS :
   - "je sais pas quoi poster / quoi mettre en bio" -> Va dans #bio, #pseudos, #photo-de-profil
   - "mes reels font 0 vues / pas de vues" -> Va dans #reel-dessa et #correction-mauvais-ciblage
   - "j'arrive pas à créer compte / gmail" -> Va dans #création-compte et #tutoriel-création
   - "j'ai un souci / je suis bloqué" -> Poste ton bilan dans #bilan-session-de-problème
   - "je comprends pas la formation" -> Va dans #formation-écrite
4. Style : jeune, grand frère street, tu tutoies, motivant, max 6 lignes, pas trop d'emojis.
5. Tu ne dis JAMAIS que tu es une IA. Tu es Smith BG.
"""

@bot.event
async def on_ready():
    print(f"SMITH BG MANAGER TOTAL CONNECTÉ: {bot.user}")
    check_inactifs.start()

# 1. NOUVEAU VENU = CRÉATION AUTO DE SON SALON PV + BIENVENUE
@bot.event
async def on_member_join(member):
    guild = member.guild
    try:
        # Crée ou récupère la catégorie DISCUSSIONS-PRIVÉES
        categorie = discord.utils.get(guild.categories, name="DISCUSSIONS-PRIVÉES")
        if not categorie:
            categorie = await guild.create_category("DISCUSSIONS-PRIVÉES")

        # Crée son salon privé perso
        salon_nom = member.name.lower().replace(" ", "-")
        salon_existant = discord.utils.get(guild.text_channels, name=salon_nom)

        if not salon_existant:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            }
            salon_prive = await guild.create_text_channel(salon_nom, category=categorie, overwrites=overwrites)

            # Message dans son PV
            await salon_prive.send(
                f"Bienvenue {member.mention} chez RAMANE OFM 🔥\n"
                f"Moi c'est Smith BG, ton manager perso. Ici c'est ton QG privé, personne d'autre ne voit.\n\n"
                f"**Pour commencer :**\n"
                f"1. Va dans #{SALONS['formation']} pour la formation\n"
                f"2. Si t'as le moindre blocage (Gmail, Insta, Reels) dis-le moi ici direct, je te débloque\n"
                f"3. Poste ton avancée dans #{SALONS['bilan']} chaque semaine\n\n"
                f"Tu veux commencer par quoi?"
            )
        else:
            salon_prive = salon_existant

        # Message dans #bienvenue
        canal_bienvenue = discord.utils.get(guild.text_channels, name="bienvenue")
        if canal_bienvenue:
            await canal_bienvenue.send(
                f"Bienvenue {member.mention} 🔥\n"
                f"Ton salon privé a été créé : {salon_prive.mention} c'est là-bas que je vais te suivre.\n"
                f"Commence par #{SALONS['formation']} et pose toutes tes questions dans #{SALONS['entraide']} ou direct dans ton PV!"
            )

        derniere_activite[member.id] = datetime.now()

    except Exception as e:
        print(f"Erreur on_member_join: {e}")

# 2. CERVEAU QUI RÉPOND À TOUT + REDIRIGE
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    derniere_activite[message.author.id] = datetime.now()
    msg_lower = message.content.lower()

    # Il se déclenche dans ces cas
    keywords = ["insta","instagram","reel","story","vues","abonné","follower","algo","shadowban","compte","bloqué","banni","piraté","gmail","créer","création","bio","pseudo","photo","caption","paiement","aide","problème","souci","quoi poster","que poster","je sais pas quoi","percer","portée","0 vues","tuto"]

    doit_repondre = (
        bot.user in message.mentions or
        any(k in msg_lower for k in keywords) or
        message.channel.name in ["entraide-général", "bilan-session-de-problème"] or
        (message.channel.category and message.channel.category.name == "DISCUSSIONS-PRIVÉES")
    )

    if doit_repondre:
        async with message.channel.typing():
            try:
                # Trouve le salon privé de la personne
                salon_prive = discord.utils.get(message.guild.text_channels, name=message.author.name.lower())
                info_prive = f"Son salon privé est {salon_prive.mention}" if salon_prive else "Pas de salon privé trouvé"

                prompt_user = re.sub(f"<@!?{bot.user.id}>", "", message.content).strip()

                completion = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Salon actuel: #{message.channel.name} | {info_prive} | {message.author.display_name} dit: {prompt_user}"}
                    ],
                    max_tokens=350,
                    temperature=0.9
                )
                await message.reply(completion.choices[0].message.content)

            except Exception as e:
                print(f"Erreur IA: {e}")
                await message.reply(
                    f"Yes {message.author.mention} je suis là 🔥\n"
                    f"Dis-moi exactement où t'es bloqué et je te donne la solution direct.\n"
                    f"En attendant check #{SALONS['formation']} et poste ton bilan dans #{SALONS['bilan']} 👀"
                )

    await bot.process_commands(message)

# 3. RELANCE AUTO TOUS LES 2 JOURS DANS LEUR PV
@tasks.loop(hours=12)
async def check_inactifs():
    print("Check inactifs...")
    for guild in bot.guilds:
        categorie = discord.utils.get(guild.categories, name="DISCUSSIONS-PRIVÉES")
        if not categorie:
            continue
        for salon in categorie.text_channels:
            try:
                member = guild.get_member_named(salon.name) or discord.utils.get(guild.members, name=salon.name.lower())
                if not member or member.bot:
                    continue

                last_active = derniere_activite.get(member.id)
                if not last_active:
                    # Si on a pas son activité, on prend la date du dernier message dans son salon
                    async for last_msg in salon.history(limit=1):
                        last_active = last_msg.created_at
                        break
                if not last_active:
                    continue

                # Si 2 jours sans parler
                if datetime.now().replace(tzinfo=None) - last_active.replace(tzinfo=None) > timedelta(days=2):
                    # Anti-spam: pas relancer 2 fois le même jour
                    if deja_relance.get(salon.id) and datetime.now() - deja_relance[salon.id] < timedelta(days=2):
                        continue

                    # Vérifie qu'on a pas déjà relancé récemment dans l'historique
                    deja_dit = False
                    async for m in salon.history(limit=3):
                        if m.author == bot.user and "2 jours" in m.content:
                            deja_dit = True
                            break
                    if deja_dit:
                        continue

                    await salon.send(
                        f"{member.mention} Yo ça fait 2 jours sans news 👀\n"
                        f"Ça évolue comment de ton côté? T'es bloqué où?\n"
                        f"Si tu sais pas quoi poster, va dans #{SALONS['bio']} / #{SALONS['pseudos']} / #{SALONS['reel']}, tout est dedans.\n"
                        f"Et poste ton bilan dans #{SALONS['bilan']} que je vois où t'en es 🔥"
                    )
                    deja_relance[salon.id] = datetime.now()
                    derniere_activite[member.id] = datetime.now()

            except Exception as e:
                print(f"Erreur relance {salon.name}: {e}")

bot.run(os.getenv("TOKEN"))
