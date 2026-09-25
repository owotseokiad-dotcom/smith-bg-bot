import discord, os, re, asyncio, threading
from discord.ext import commands, tasks
from openai import OpenAI
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask

# --- FIX RENDER: Garde le service en vie ---
app = Flask(__name__)
@app.route('/')
def home(): return "Smith BG MANAGER TOTAL is alive!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()
# --- FIN FIX RENDER ---

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

derniere_activite = defaultdict(lambda: datetime.now())
deja_relance = {}
last_reply = {}

SALONS = {
    "bienvenue": "bienvenue",
    "entraide": "entraide-général",
    "bilan": "bilan-session-de-progression",
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
1. Tu réponds à TOUT : Gmail bloqué, création compte Insta, Reels 0 vues, bio, pseudo, photo, shadowban, bloqué, paiement.
2. Tu donnes la solution en 2-3 étapes claires et directes.
3. Tu rediriges TOUJOURS vers le bon salon avec un vrai tag.
4. Style : jeune, grand frère street, tu tutoies, motivant, max 6 lignes.
5. Tu ne dis JAMAIS que tu es une IA. Tu es Smith BG.
"""

@bot.event
async def on_ready():
    print(f"SMITH BG MANAGER TOTAL CONNECTÉ: {bot.user}")
    check_inactifs.start()

@bot.event
async def on_member_join(member):
    guild = member.guild
    try:
        categorie = discord.utils.get(guild.categories, name="DISCUSSIONS-PRIVÉES")
        if not categorie:
            categorie = await guild.create_category("DISCUSSIONS-PRIVÉES")

        # On cherche les vrais salons pour avoir des tags BLEUS cliquables
        form_chan = discord.utils.get(guild.text_channels, name=SALONS["formation"])
        bilan_chan = discord.utils.get(guild.text_channels, name=SALONS["bilan"])

        form_mention = form_chan.mention if form_chan else f"#{SALONS['formation']}"
        bilan_mention = bilan_chan.mention if bilan_chan else f"#{SALONS['bilan']}"

        salon_nom = member.name.lower().replace(" ", "-")
        salon_existant = discord.utils.get(guild.text_channels, name=salon_nom)
        if not salon_existant:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, manage_channels=True)
            }
            salon_prive = await guild.create_text_channel(salon_nom, category=categorie, overwrites=overwrites)
            await salon_prive.send(f"Bienvenue {member.mention} chez RAMANE OFM 🔥\nMoi c'est Smith BG, ton manager perso. Ici c'est ton QG privé.\n1. Va dans {form_mention}\n2. Si t'es bloqué dis-le ici direct\n3. Poste ton avancée dans {bilan_mention}")
        derniere_activite[member.id] = datetime.now()
    except Exception as e:
        print(f"Erreur on_member_join: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    derniere_activite[message.author.id] = datetime.now()

    key = f"{message.author.id}_{message.content}"
    if key in last_reply and (datetime.now() - last_reply[key]).seconds < 15:
        return
    last_reply[key] = datetime.now()

    msg_lower = message.content.lower()
    keywords = ["insta","instagram","reel","story","vues","abonné","follower","algo","shadowban","compte","bloqué","banni","piraté","gmail","créer","création","bio","pseudo","photo","caption","paiement","aide","problème","souci","quoi poster"]

    doit_repondre = (bot.user in message.mentions or any(k in msg_lower for k in keywords) or message.channel.name in ["entraide-général", "bilan-session-de-progression"] or (message.channel.category and message.channel.category.name == "DISCUSSIONS-PRIVÉES"))

    if doit_repondre:
        async with message.channel.typing():
            try:
                prompt_user = re.sub(f"<@!?{bot.user.id}>", "", message.content).strip()
                completion = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Salon: #{message.channel.name} | {message.author.display_name} dit: {prompt_user}"}],
                    max_tokens=350, temperature=0.9
                )
                await message.reply(completion.choices[0].message.content)
            except Exception as e:
                print(f"Erreur IA: {e}")
                await message.reply(f"Yes {message.author.mention} je suis là 🔥 Dis-moi exactement où t'es bloqué et je te débloque direct. Check #{SALONS['formation']} en attendant 👀")

    await bot.process_commands(message)

@tasks.loop(hours=12)
async def check_inactifs():
    print("Check inactifs...")
    for guild in bot.guilds:
        categorie = discord.utils.get(guild.categories, name="DISCUSSIONS-PRIVÉES")
        if not categorie: continue
        for salon in categorie.text_channels:
            try:
                member = guild.get_member_named(salon.name) or discord.utils.get(guild.members, name=salon.name.lower())
                if not member or member.bot: continue
                last_active = derniere_activite.get(member.id)
                if not last_active: continue
                if datetime.now().replace(tzinfo=None) - last_active.replace(tzinfo=None) > timedelta(days=2):
                    if deja_relance.get(salon.id) and datetime.now() - deja_relance[salon.id] < timedelta(days=2): continue
                    await salon.send(f"{member.mention} Yo ça fait 2 jours sans news 👀 Ça évolue comment? T'es bloqué où?")
                    deja_relance[salon.id] = datetime.now()
            except Exception as e:
                print(f"Erreur relance: {e}")

# CORRECTION ICI -> DISCORD_TOKEN
bot.run(os.getenv("DISCORD_TOKEN"))
