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
NOM_ROLE_VAPRO = "VA Pro"
NOM_ROLE_MANAGER = "Manager"
NOM_CATEGORIE = "📈 CLIENTS"
NOM_CATEGORIE_CALL = "🔊 CALLS"

def get_ch(guild, name_contains):
    """Trouve un salon par son nom"""
    for ch in guild.text_channels:
        if name_contains in ch.name.lower():
            return ch.mention
    return f"#{name_contains}"

async def get_or_create_role(guild, name, colour=discord.Colour.default()):
    role = discord.utils.get(guild.roles, name=name)
    if not role:
        role = await guild.create_role(name=name, colour=colour)
    return role

@bot.event
async def on_ready():
    print(f"✅ SMITH BG EN LIGNE {bot.user}")

@bot.event
async def on_member_join(member):
    guild = member.guild

    # Role auto
    role = await get_or_create_role(guild, NOM_ROLE_CLIENT, discord.Colour.pink())
    await member.add_roles(role)

    # Catégorie clients TEXT
    categorie = discord.utils.get(guild.categories, name=NOM_CATEGORIE)
    if not categorie:
        categorie = await guild.create_category(NOM_CATEGORIE)

    # Catégorie CALLS + Call général
    cat_calls = discord.utils.get(guild.categories, name=NOM_CATEGORIE_CALL)
    if not cat_calls:
        cat_calls = await guild.create_category(NOM_CATEGORIE_CALL)
    
    call_general = discord.utils.get(guild.voice_channels, name="🌐・call-général")
    if not call_general:
        await guild.create_voice_channel(name="🌐・call-général", category=cat_calls)

    # Overwrites privé
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, connect=True)
    }
    
    # Salon privé TEXT = juste son nom
    salon_prive = await guild.create_text_channel(
        name=f"🔒・{member.name.lower()}",
        category=categorie,
        overwrites=overwrites
    )
    # Salon privé VOCAL
    vocal_prive = await guild.create_voice_channel(
        name=f"🔒・vocal-{member.name.lower()}",
        category=cat_calls,
        overwrites=overwrites
    )

    # --- TON ANCIEN TEXTE COMPLET QUE TU AVAIS REMPLI ---
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

    embed.add_field(name="🔒 TON SALON PRIVÉ", value=f"Tu es ici {salon_prive.mention}\nVocal privé: {vocal_prive.mention}\nEnvoie ton @ Insta et tape ton besoin :\n**1** Followers | **2** Vues/Likes | **3** Reels | **4** Gestion | **5** Devis", inline=False)
    
    embed.set_footer(text="SMITH BG Agence • Lis #règles puis #formation-écrite")

    await salon_prive.send(member.mention, embed=embed)

# --- COMMANDES QUE TU AS DEMANDÉ ---

@bot.command()
async def vapro(ctx, member: discord.Member):
    role = await get_or_create_role(ctx.guild, NOM_ROLE_VAPRO, discord.Color.purple())
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} est maintenant **{NOM_ROLE_VAPRO}** !")

@bot.command()
async def role(ctx, member: discord.Member, *, nom_role: str):
    """Donner n'importe quel rôle sur ton choix"""
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, nom_role)
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} a reçu **{role.name}**")

@bot.command()
async def removerole(ctx, member: discord.Member, *, nom_role: str):
    role = discord.utils.get(ctx.guild.roles, name=nom_role)
    if role:
        await member.remove_roles(role)
        await ctx.send(f"🗑️ Rôle **{role.name}** retiré à {member.mention}")

@bot.command()
async def manager(ctx, member: discord.Member):
    """C'est toi qui désigne le manager"""
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, NOM_ROLE_MANAGER, discord.Color.gold())
    await member.add_roles(role)
    try:
        await member.edit(nick=f"Manager | {member.name}")
    except:
        pass
    await ctx.send(f"👑 {member.mention} est maintenant **Manager | {member.name}**")

@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("🔧 Je crée les salons privés + vocaux manquants...")
    count = 0
    categorie = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE)
    cat_calls = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE_CALL)
    if not categorie: categorie = await ctx.guild.create_category(NOM_CATEGORIE)
    if not cat_calls: cat_calls = await guild.create_category(NOM_CATEGORIE_CALL) if (guild:=ctx.guild) else None

    for member in ctx.guild.members:
        if member.bot: continue
        existe = discord.utils.get(ctx.guild.text_channels, name=f"🔒・{member.name.lower()}")
        if not existe:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, connect=True)
            }
            await ctx.guild.create_text_channel(name=f"🔒・{member.name.lower()}", category=categorie, overwrites=overwrites)
            await ctx.guild.create_voice_channel(name=f"🔒・vocal-{member.name.lower()}", category=cat_calls, overwrites=overwrites)
            count += 1
    await ctx.send(f"✅ Terminé ! {count} salons créés.")

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
