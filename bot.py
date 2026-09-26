import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import yt_dlp
import asyncio
import random

app = Flask(__name__)
@app.route('/')
def home():
    return "Smith BG LIVE"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="r", intents=intents, help_command=None)

# --- CONFIG YT-DLP AVEC COOKIES ---
def get_ydl_opts():
    opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    # Si ton fichier cookies.txt est à côté de bot.py, il va l'utiliser auto
    if os.path.exists("instagram.com_cookies.txt"):
        opts['cookiefile'] = "instagram.com_cookies.txt"
    elif os.path.exists("cookies.txt"):
        opts['cookiefile'] = "cookies.txt"
    return opts

# --- PARTIE NUMERO ---
NUMEROS = {
    "USA": ["+1 234 567 8901", "+1 323 555 0199"],
    "Canada": ["+1 514 555 0123"],
    "Angleterre": ["+44 7700 900123"],
    "Ukraine": ["+380 50 123 4567"],
}

class SelectPays(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="USA", emoji="🇺🇸"),
            discord.SelectOption(label="Canada", emoji="🇨🇦"),
            discord.SelectOption(label="Angleterre", emoji="🇬🇧"),
            discord.SelectOption(label="Ukraine", emoji="🇺🇦"),
        ]
        super().__init__(placeholder="Choisis ton pays...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        pays = self.values[0]
        num = random.choice(NUMEROS.get(pays, ["Erreur"]))
        await interaction.followup.send(f"📞 **{pays}** : `{num}`", ephemeral=True)

class PaysView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPays())

@bot.command(name="numero")
async def numero_cmd(ctx):
    embed = discord.Embed(title="📞 Choisis ton numéro", description="🇺🇸 USA\n🇨🇦 Canada\n🇬🇧 Angleterre\n🇺🇦 Ukraine", color=0x3498db)
    await ctx.send(embed=embed, view=PaysView())

# --- PARTIE INSTA ---
@bot.command(name="insta", aliases=["ig", "reel"])
async def insta_cmd(ctx, url: str = None):
    if url is None:
        await ctx.send("Envoie le lien: `rinsta https://www.instagram.com/reel/...`")
        return

    await ctx.send("⏳ Téléchargement...")
    try:
        opts = get_ydl_opts()
        opts['outtmpl'] = 'video.%(ext)s'

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await ctx.send(file=discord.File(filename))
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await ctx.send(f"Erreur: `{str(e)[:500]}`\nVérifie que `instagram.com_cookies.txt` est bien à côté de `bot.py` sur GitHub")

@bot.event
async def on_ready():
    print(f"EN LIGNE {bot.user}")

keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD")
bot.run(TOKEN)
