import discord, os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

# Fonction pour taguer un salon en bleu cliquable
def mention(guild, nom):
    for c in guild.text_channels:
        if nom in c.name.lower():
            return c.mention
    return f"#{nom}"

@client.event
async def on_ready():
    print(f"SMITH BG MANAGER CONNECTÉ: {client.user}")

@client.event
async def on_member_join(member):
    guild = member.guild
    
    # --- OPTION 1 : GESTION DISCUSSIONS PRIVÉES ---
    cat = discord.utils.get(guild.categories, name="💬 DISCUSSIONS-PRIVÉES")
    if not cat:
        cat = await guild.create_category("💬 DISCUSSIONS-PRIVÉES")

    # Salon privé visible par 3 personnes seulement
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    salon_prive = await guild.create_text_channel(f"prive-{member.name}", category=cat, overwrites=overwrites)

    # Message de bienvenue court et sage
    bienvenue = discord.utils.get(guild.text_channels, name="bienvenue")
    if bienvenue:
        await bienvenue.send(
            f"Bienvenue {member.mention} dans **Ramane | OFM** !\n"
            f"👉 Lis {mention(guild, 'règles')} puis commence par {mention(guild, 'formation-écrite')}\n"
            f"Tes vidéos sont dans {mention(guild, 'drive-3')} (le plus complet) + {mention(guild, 'drive')} et {mention(guild, 'drive-2')}\n"
            f"Ton espace privé avec la direction : {salon_prive.mention}\n"
            f"On reste simple et respectueux, pas de palabres ni d'injures."
        )
    
    await salon_prive.send(
        f"Salut {member.mention}, bienvenue chez **Ramane | OFM**.\n"
        f"Ici c'est ton espace privé avec la direction (on est 3 ici).\n"
        f"Besoin d'aide ? Écris ici."
    )

@client.event
async def on_message(message):
    if message.author.bot: 
        return
    if client.user not in message.mentions:
        return

    guild = message.guild
    txt = message.content.lower()

    # --- OPTION 2 : REDIRECTION VERS LES BONS SALONS (sans répondre au problème) ---
    if "drive" in txt or "vidéo" in txt:
        await message.reply(f"Check {mention(guild, 'drive-3')} c'est le plus complet, sinon {mention(guild, 'drive')} et {mention(guild, 'drive-2')}")
    elif "insta" in txt or "compte" in txt:
        await message.reply(f"Va dans ton privé et regarde {mention(guild, 'création-compte')} + {mention(guild, 'tutoriel-création')}")
    elif "bio" in txt or "pseudo" in txt:
        await message.reply(f"Tout est dans {mention(guild, 'pseudos')} et {mention(guild, 'bio')}")
    elif "story" in txt or "reel" in txt:
        await message.reply(f"Regarde {mention(guild, 'story-cta')} et {mention(guild, 'reel-dessai')}")
   
