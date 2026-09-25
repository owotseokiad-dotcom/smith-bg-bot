import discord, os
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ SMITH BG EN LIGNE: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot: return
    
    if message.content.strip().lower() in ["!creer_prives", "!creer_prive", "!prives", "creer_prives"]:
        await message.reply("🔧 Je lance la création des salons privés manquants...")
        guild = message.guild
        cat = discord.utils.get(guild.categories, name="💬 DISCUSSIONS-PRIVÉES")
        if not cat:
            cat = await guild.create_category("💬 DISCUSSIONS-PRIVÉES")
        
        crees = 0
        for member in guild.members:
            if member.bot: continue
            # Vérifie si il a déjà un salon (peu importe le nom)
            a_salon = False
            for chan in guild.text_channels:
                if member.name.lower() in chan.name.lower() and chan.category and "PRIVÉES" in str(chan.category.name).upper():
                    a_salon = True
                    break
            
            if not a_salon:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                salon = await guild.create_text_channel(f"prive-{member.name}", category=cat, overwrites=overwrites)
                await salon.send(f"Salut {member.mention}, espace privé **Ramane | OFM** créé. On est 3 ici.")
                crees += 1
        
        await message.channel.send(f"✅ Terminé ! {crees} salons privés créés.")
        return

    if client.user in message.mentions:
        await message.reply("Utilise `!prives` pour créer les salons privés.")

client.run(os.getenv("DISCORD_TOKEN"))
