import discord, os
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} connecté!")
    try:
        await bot.tree.sync()
    except:
        pass

@bot.command()
async def ping(ctx):
    await ctx.send("Smith BG est en ligne! 🏆 Tous les rôles actifs!")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"Bienvenue {member.mention} sur RAMANE OFM! 🔥")

bot.run(os.getenv("TOKEN"))
