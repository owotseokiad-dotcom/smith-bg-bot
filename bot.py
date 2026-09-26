import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import yt_dlp
import asyncio

# --- PARTIE WEB POUR RENDER (garde le bot allumé) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Ramane | OFM EST EN LIGNE"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- PARTIE BOT DISCORD ---
intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="r", intents=intents)

# Options pour yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f"EN LIGNE {bot.user} | Ramane | OFM")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="rhelp | OFM"))

@bot.command(name="join")
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("Boss tu dois être en vocal d'abord.")

@bot.command(name="play", aliases=["p"])
async def play(ctx, *, url):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Va en vocal boss.")
            return

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f'🎵 En lecture: **{player.title}** | OFM Boss Ramane')

@bot.command(name="leave", aliases=["stop", "dc"])
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("OFM a quitté le vocal.")
    else:
        await ctx.send("Je suis pas en vocal boss.")

@bot.command(name="help", aliases=["h"])
async def help_cmd(ctx):
    embed = discord.Embed(title="Ramane | OFM Bot", color=0xFF0000, description="Bot musique OFM")
    embed.add_field(name="rplay <lien/nom>", value="Joue une musique", inline=False)
    embed.add_field(name="rleave / rstop", value="Quitte le vocal", inline=False)
    embed.add_field(name="rjoin", value="Rejoint ton vocal", inline=False)
    await ctx.send(embed=embed)

# LANCE TOUT
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("FATAL: DISCORD_TOKEN manquant dans Render Environment")
else:
    bot.run(TOKEN)
