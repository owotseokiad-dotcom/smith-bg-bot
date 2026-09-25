from flask import Flask
import threading
import os
import discord
from discord.ext import commands

# --- Petit serveur pour que Render ne coupe pas ---
app = Flask(__name__)
@app.route('/')
def home(): return "SMITH BG BOT EN LIGNE"

def run_web():
    app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_web).start()

# --- Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ SMITH BG EN LIGNE - TOUS SALONS - {bot.user}")

@bot.command()
async def bienvenue(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Admin seulement")
    msg = """👋 **BIENVENUE SUR SMITH BG** 👋

C'est ton serveur d'entraide gaming 🔥

📍 **TOUS NOS SALONS :**
<#134...Mets tes vrais ID ici> - Entraide générale
Ajoute les autres liens...

✅ Reste actif, respecte les règles, et amuse-toi !

Tape !help si tu as besoin."""
    # Envoie dans TOUS les salons texte
    for channel in ctx.guild.text_channels:
        try:
            await channel.send(msg)
        except:
            pass
    await ctx.send("✅ Message de bienvenue envoyé partout !")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN manquant")
