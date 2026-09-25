from flask import Flask
import threading
import os
import discord
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "SMITH BG EN LIGNE"
def run_web(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_web).start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

NOM_ROLE_CLIENT = "Client Insta"
NOM_CATEGORIE = "📈 CLIENTS"

def get_ch(guild, name_contains):
    """Trouve un salon par son nom"""
    for ch in guild.text_channels:
        if name_contains in ch.name.lower():
            return ch.mention
    return f"#{name_contains}"

@bot.event
async def on_ready():
    print(f"✅ SMITH BG EN LIGNE {bot.user}")

@bot.event
async def on_member_join(member):
    guild = member.guild

    # Role auto
    role = discord.utils.get(guild.roles, name=NOM_ROLE_CLIENT)
    if not role:
        role = await guild.create_role(name=NOM_ROLE_CLIENT, colour=discord.Colour.pink())
    await member.add_roles(role)

    # Catégorie clients
    categorie = discord.utils.get(guild.categories, name=NOM_CATEGORIE)
    if not categorie:
        categorie = await guild.create_category(NOM_CATEGORIE)

    # Salon privé = juste son nom
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    salon_prive = await guild.create_text_channel(
        name=f"🔒・{member.name.lower()}",
        category=categorie,
        overwrites=overwrites
    )

    # --- PRESENTATION PRO DE TES SALONS (comme sur tes photos) ---
    embed = discord.Embed(
        title=f"👋 Bienvenue {member.name} chez SMITH BG",
        description="**AGENCE OFM - Voici le plan du serveur**",
        color=0xFF006A
    )

    embed.add_field(name="🏠 ACCUEIL - Commence ici", value=f"""
> {get_ch(guild,'bienvenue')} - Message de bienvenue
> {get_ch(guild,'règles')} - Règles du serveur
> {get_ch(guild,'paiement')} - Infos paiement
> {get_ch(guild,'période-dessai')} - Ta période d'essai
> {get_ch(guild,'parrainage')} - Parrainage
> {get_ch(guild,'support-créer')} - Créer un ticket
""", inline=False)

    embed.add_field(name="📢 ANNONCES OFFICIELLES", value=f"""
> {get_ch(guild,'annonces-officielles')} - Annonces importantes
> {get_ch(guild,'résultats-clics')} - Résultats des membres
> {get_ch(guild,'bilan-session')} - Bilan prospection
> {get_ch(guild,'preuves-paiement')} - Preuves de paiement
""", inline=False)

    embed.add_field(name="🎓 FORMATION", value=f"""
> {get_ch(guild,'formation-écrite')} - Formation écrite complète
> {get_ch(guild,'création-compte')} - Créer un compte Insta
> {get_ch(guild,'story-cta')} - Story qui vend
> {get_ch(guild,'tutoriel-création')} - Tutoriel création
> {get_ch(guild,'reel-dessai')} - Test tes Reels
> {get_ch(guild,'correction-mauvais')} - Correction d'erreurs
""", inline=False)

    embed.add_field(name="💎 CONTENU - Le plus important", value=f"""
> {get_ch(guild,'pseudos')} - Idées de pseudos
> {get_ch(guild,'bio')} - Bio parfaite
> {get_ch(guild,'comptes-à-suivre')} - Comptes modèles
> {get_ch(guild,'caption-story')} - Textes de vente
> {get_ch(guild,'photos-story')} - Photos Story CTA
> {get_ch(guild,'description')} - Descriptions
> {get_ch(guild,'drive')} - Drive avec toutes les ressources
""", inline=False)

    embed.add_field(name="🔒 TON SALON PRIVÉ", value=f"Tu es ici {salon_prive.mention}\nEnvoie ton @ Insta et tape ton besoin :\n**1** Followers | **2** Vues/Likes | **3** Reels | **4** Gestion | **5** Devis", inline=False)
    
    embed.set_footer(text="SMITH BG Agence • Lis #règles puis #formation-écrite")

    await salon_prive.send(member.mention, embed=embed)

@bot.command()
async def salons(ctx):
    liste = "\n".join([f"{ch.mention}" for ch in ctx.guild.text_channels if "🔒・" not in ch.name])
    embed = discord.Embed(title="📍 TOUS NOS SALONS SMITH BG", description=liste, color=0xFF006A)
    await ctx.send(embed=embed)

@bot.command()
async def close(ctx):
    if "🔒・" in ctx.channel.name and ctx.author.guild_permissions.administrator:
        await ctx.channel.delete()

bot.run(os.getenv("DISCORD_TOKEN"))
