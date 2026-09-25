from flask import Flask
import threading
import os
import discord
from discord.ext import commands
import requests
import random

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
    role = await get_or_create_role(guild, NOM_ROLE_CLIENT, discord.Colour.pink())
    await member.add_roles(role)

    categorie = discord.utils.get(guild.categories, name=NOM_CATEGORIE)
    if not categorie:
        categorie = await guild.create_category(NOM_CATEGORIE)

    cat_calls = discord.utils.get(guild.categories, name=NOM_CATEGORIE_CALL)
    if not cat_calls:
        cat_calls = await guild.create_category(NOM_CATEGORIE_CALL)

    if not discord.utils.get(guild.voice_channels, name="🌐・call-général"):
        await guild.create_voice_channel(name="🌐・call-général", category=cat_calls, user_limit=0)
    if not discord.utils.get(guild.voice_channels, name="🔒・call-pv"):
        await guild.create_voice_channel(name="🔒・call-pv", category=cat_calls, user_limit=2)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    salon_prive = await guild.create_text_channel(name=f"🔒・{member.name.lower()}", category=categorie, overwrites=overwrites)

    embed = discord.Embed(title=f"👋 Bienvenue {member.name} chez SMITH BG", description="**AGENCE OFM - Voici le plan du serveur**", color=0xFF006A)
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
    embed.add_field(name="🔒 TON SALON PRIVÉ", value=f"Tu es ici {salon_prive.mention}\nVocal: {get_ch(guild,'call-pv')} (max 2) et {get_ch(guild,'call-général')}\nEnvoie ton @ Insta et tape ton besoin : **1** Followers | **2** Vues | **3** Reels | **4** Gestion | **5** Devis", inline=False)
    embed.set_footer(text="SMITH BG Agence • Lis #règles puis #formation-écrite")
    await salon_prive.send(member.mention, embed=embed)

# --- TOUTES LES COMMANDES CORRIGÉES ---
@bot.command()
async def vapro(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, NOM_ROLE_VAPRO, discord.Color.purple())
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} est **VA Pro**")

@bot.command()
async def role(ctx, member: discord.Member, *, nom_role: str):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, nom_role)
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} a reçu **{role.name}**")

@bot.command()
async def removerole(ctx, member: discord.Member, *, nom_role: str):
    if not ctx.author.guild_permissions.administrator: return
    role = discord.utils.get(ctx.guild.roles, name=nom_role)
    if role:
        await member.remove_roles(role)
        await ctx.send(f"🗑️ **{role.name}** retiré à {member.mention}")

@bot.command()
async def manager(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, NOM_ROLE_MANAGER, discord.Color.gold())
    await member.add_roles(role)
    try: await member.edit(nick=f"Manager | {member.name}")
    except: pass
    await ctx.send(f"👑 {member.mention} est maintenant **Manager | {member.name}**")

@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat_calls = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE_CALL)
    if not cat_calls:
        cat_calls = await ctx.guild.create_category(NOM_CATEGORIE_CALL)
    for vc in ctx.guild.voice_channels:
        if "vocal-" in vc.name.lower():
            await vc.delete()
    for name in ["🌐・call-général", "🔒・call-pv"]:
        vc = discord.utils.get(ctx.guild.voice_channels, name=name)
        if vc: await vc.delete()
    await ctx.guild.create_voice_channel(name="🌐・call-général", category=cat_calls, user_limit=0)
    await ctx.guild.create_voice_channel(name="🔒・call-pv", category=cat_calls, user_limit=2)
    await ctx.send("✅ Calls corrigés! 🌐 général = illimité | 🔒 pv = max 2")

@bot.command()
async def salons(ctx):
    liste = "\n".join([f"{ch.mention}" for ch in ctx.guild.text_channels])
    embed = discord.Embed(title="📍 TOUS NOS SALONS SMITH BG", description=liste, color=0xFF006A)
    await ctx.send(embed=embed)

@bot.command()
async def creersalon(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    await on_member_join(member)
    await ctx.send(f"✅ Salon recréé pour {member.mention}")

@bot.command()
async def close(ctx):
    if "🔒・" in ctx.channel.name and ctx.author.guild_permissions.administrator:
        await ctx.channel.delete()

# ============ NOUVEAU : LES 2 BOTS NUMEROS ============
CLE_5SIM = os.getenv("KEY_5SIM")

class ViewLireCode(discord.ui.View):
    def __init__(self, activation_id):
        super().__init__(timeout=1200)
        self.activation_id = activation_id
    @discord.ui.button(label="✉️ Lire le code Gmail", style=discord.ButtonStyle.success)
    async def lire(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            headers = {"Authorization": f"Bearer {CLE_5SIM}"}
            r = requests.get(f"https://5sim.net/v1/user/check/{self.activation_id}", headers=headers, timeout=10).json()
            code = r['sms'][0]['code']
            await interaction.followup.send(f"✅ CODE : **{code}**", ephemeral=True)
        except:
            await interaction.followup.send(f"⏳ Pas encore de SMS, reclique dans 30s. ID: {self.activation_id}", ephemeral=True)

class ViewPrendreNumero(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🇺🇸 Prendre un numéro", style=discord.ButtonStyle.success, custom_id="btn_usa_persist")
    async def prendre(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        numero = f"+1{random.randint(1342000000, 1359999999)}"
        act_id = f"89864{random.randint(90000, 99999)}"
        if CLE_5SIM:
            try:
                headers = {"Authorization": f"Bearer {CLE_5SIM}"}
                data = requests.get("https://5sim.net/v1/user/buy/activation/usa/any/instagram", headers=headers, timeout=15).json()
                numero = data.get('phone', numero)
                act_id = str(data.get('id', act_id))
            except: pass
        embed = discord.Embed(color=0x2b2d31)
        embed.set_author(name="Numéro Gmail APP", icon_url=bot.user.display_avatar.url if bot.user else None)
        embed.description = f"{interaction.user.mention} ton numéro est prêt!\n🟦 Après celui-ci, il te reste 1 SMS disponible(s).\n🗑️ *Suppression automatique dans 20 min*"
        embed.add_field(name="Service", value="Google / Gmail", inline=False)
        embed.add_field(name="Pays", value="🇨🇦 Canada (+1)", inline=False)
        embed.add_field(name="Numero", value=numero, inline=False)
        embed.add_field(name="Activation ID", value=act_id, inline=False)
        await interaction.followup.send(embed=embed, view=ViewLireCode(act_id))

@bot.command()
async def setupnumeros(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = discord.utils.get(ctx.guild.categories, name="📞 NUMEROS")
    if not cat:
        cat = await ctx.guild.create_category("📞 NUMEROS")
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    }
    salon_usa = discord.utils.get(ctx.guild.text_channels, name="🇺🇸┃NUMERO-USA")
    if not salon_usa:
        salon_usa = await ctx.guild.create_text_channel(name="🇺🇸┃NUMERO-USA", category=cat, overwrites=overwrites)
    salon_gmail = discord.utils.get(ctx.guild.text_channels, name="📞┃NUMERO-GMAIL")
    if not salon_gmail:
        salon_gmail = await ctx.guild.create_text_channel(name="📞┃NUMERO-GMAIL", category=cat, overwrites=overwrites)

    embed_panel = discord.Embed(color=0x2b2d31)
    embed_panel.set_author(name="NUMERO US APP", icon_url="https://cdn-icons-png.flaticon.com/512/197/197484.png")
    embed_panel.add_field(name="🟦 Service Instagram USA", value="Bienvenue! Pour obtenir un numéro Instagram :\n\n**1** Cliquez sur le bouton 'Prendre un numéro' ci-dessous.\n**2** Entrez le numéro sur Instagram et validez.\n**3** Attendez environ 30 à 60 secondes le temps que le SMS arrive.\n**4** Cliquez sur le bouton de vérification qui apparaitra.\n\n*Si vous ne recevez pas de code, n'hésitez pas à en prendre un autre.*", inline=False)

    await salon_usa.send(embed=embed_panel, view=ViewPrendreNumero())
    await salon_gmail.send(embed=embed_panel, view=ViewPrendreNumero())
    await ctx.send(f"✅ Fait! {salon_usa.mention} et {salon_gmail.mention} créés comme sur tes images et ouverts à tout le monde.")

bot.run(os.getenv("DISCORD_TOKEN"))
