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
    bot.add_view(ViewChoixPays())

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

    role_manager = discord.utils.get(guild.roles, name=NOM_ROLE_MANAGER)
    role_teamleader = discord.utils.get(guild.roles, name="Team Leader")
    if not role_teamleader:
        role_teamleader = discord.utils.get(guild.roles, name="team leader")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    if role_manager:
        overwrites[role_manager] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    if role_teamleader:
        overwrites[role_teamleader] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    salon_prive = await guild.create_text_channel(name=f"🔒・{member.name.lower()}", category=categorie, overwrites=overwrites)
    embed = discord.Embed(title=f"👋 Bienvenue {member.name} chez SMITH BG", description="**AGENCE OFM - Voici le plan du serveur**", color=0xFF006A)
    embed.add_field(name="🏠 ACCUEIL - Commence ici", value=f"> {get_ch(guild,'bienvenue')}\n> {get_ch(guild,'règles')}\n> {get_ch(guild,'paiement')}", inline=False)
    embed.set_footer(text="SMITH BG Agence")
    await salon_prive.send(member.mention, embed=embed)

@bot.command()
async def vapro(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, NOM_ROLE_VAPRO, discord.Color.purple())
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} est VA Pro")

@bot.command()
async def role(ctx, member: discord.Member, *, nom_role: str):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, nom_role)
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} a reçu {role.name}")

@bot.command()
async def removerole(ctx, member: discord.Member, *, nom_role: str):
    if not ctx.author.guild_permissions.administrator: return
    role = discord.utils.get(ctx.guild.roles, name=nom_role)
    if role:
        await member.remove_roles(role)
        await ctx.send(f"🗑️ {role.name} retiré à {member.mention}")

@bot.command()
async def manager(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    role = await get_or_create_role(ctx.guild, NOM_ROLE_MANAGER, discord.Color.gold())
    await member.add_roles(role)
    try: await member.edit(nick=f"Manager | {member.name}")
    except: pass
    await ctx.send(f"👑 {member.mention} est maintenant Manager")

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
    await ctx.send("✅ Calls corrigés!")

@bot.command()
async def salons(ctx):
    liste = "\n".join([f"{ch.mention}" for ch in ctx.guild.text_channels])
    embed = discord.Embed(title="📍 TOUS NOS SALONS", description=liste, color=0xFF006A)
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

CLE_5SIM = os.getenv("KEY_5SIM")

class ViewLireCode(discord.ui.View):
    def __init__(self, activation_id):
        super().__init__(timeout=1200)
        self.activation_id = activation_id
    @discord.ui.button(label="✉️ Lire le code", style=discord.ButtonStyle.success)
    async def lire(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            headers = {"Authorization": f"Bearer {CLE_5SIM}"}
            r = requests.get(f"https://5sim.net/v1/user/check/{self.activation_id}", headers=headers, timeout=10).json()
            code = r['sms'][0]['code']
            await interaction.followup.send(f"✅ CODE : **{code}**", ephemeral=True)
        except:
            await interaction.followup.send(f"⏳ Pas encore de SMS, reclique dans 30s. ID: {self.activation_id}", ephemeral=True)

class SelectPays(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="USA", value="usa", emoji="🇺🇸"),
            discord.SelectOption(label="Canada", value="canada", emoji="🇨🇦"),
            discord.SelectOption(label="Angleterre", value="england", emoji="🇬🇧"),
            discord.SelectOption(label="Ukraine", value="ukraine", emoji="🇺🇦"),
        ]
        super().__init__(placeholder="🌍 Choisis ton pays...", min_values=1, max_values=1, options=options, custom_id="choix_pays_4")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        pays = self.values[0]
        numero = f"+1{random.randint(2000000000, 9999999999)}"
        act_id = f"89864{random.randint(90000, 99999)}"
        if CLE_5SIM:
            try:
                headers = {"Authorization": f"Bearer {CLE_5SIM}"}
                data = requests.get(f"https://5sim.net/v1/user/buy/activation/{pays}/any/google", headers=headers, timeout=15).json()
                numero = data.get('phone', numero)
                act_id = str(data.get('id', act_id))
            except: pass
        embed = discord.Embed(color=0x2b2d31, title="✅ Numéro prêt", description="**Seul toi vois ce message**")
        embed.add_field(name="Pays", value=pays.upper(), inline=True)
        embed.add_field(name="Numero", value=numero, inline=True)
        embed.add_field(name="ID", value=act_id, inline=False)
        await interaction.followup.send(embed=embed, view=ViewLireCode(act_id), ephemeral=True)
        logs = discord.utils.get(interaction.guild.text_channels, name="logs-numeros")
        if logs:
            await logs.send(f"👤 {interaction.user.mention} | {pays} | {numero} | {act_id}")

class ViewChoixPays(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPays())

@bot.command()
async def setupnumeros(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = discord.utils.get(ctx.guild.categories, name="📞 NUMEROS")
    if not cat:
        cat = await ctx.guild.create_category("📞 NUMEROS")
    for ch in list(ctx.guild.text_channels):
        if "numero" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    }
    salon_usa = await ctx.guild.create_text_channel(name="🇺🇸┃numero-usa", category=cat, overwrites=overwrites)
    salon_gmail = await ctx.guild.create_text_channel(name="📞┃numero-gmail", category=cat, overwrites=overwrites)
    overwrites_logs = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
    }
    for r in ctx.guild.roles:
        if r.permissions.administrator or "Manager" in r.name or "Team Leader" in r.name:
            overwrites_logs[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
    logs = discord.utils.get(ctx.guild.text_channels, name="logs-numeros")
    if not logs:
        logs = await ctx.guild.create_text_channel(name="logs-numeros", category=cat, overwrites=overwrites_logs)
    embed_panel = discord.Embed(color=0x2b2d31, title="📞 Choisis ton numéro", description="Sélectionne le pays :\n\n🇺🇸 USA\n🇨🇦 Canada\n🇬🇧 Angleterre\n🇺🇦 Ukraine\n\n**Seul toi verras ton numéro**")
    await salon_usa.send(embed=embed_panel, view=ViewChoixPays())
    await salon_gmail.send(embed=embed_panel, view=ViewChoixPays())
    await ctx.send(f"✅ 2 salons numéros créés : {salon_usa.mention} et {salon_gmail.mention}")

@bot.command()
async def grille(ctx):
    if not ctx.author.guild_permissions.administrator: return
    salon_paiement = None
    for ch in ctx.guild.text_channels:
        if "paiement" in ch.name.lower() or "paiment" in ch.name.lower():
            salon_paiement = ch
            break
    if not salon_paiement:
        await ctx.send("❌ Je trouve pas #paiement")
        return
    embed = discord.Embed(title="📊 Grille de Paie 🤑", description="Plus tu montes en subs, plus ton $/sub augmente 🔥 (selon ton total de subs)", color=0xFFD700)
    embed.add_field(name="👑 Paliers", value="De 0 à 500 subs → **0,50$ / sub**\nDe 500 à 700 subs → **0,60$ / sub**\nDe 700 à 800 subs → **0,70$ / sub**\nDe 800 à 1000 subs → **0,80$ / sub**\nDe 1000 à 1500 subs → **1$ / sub**\nDe 1500 à 2000 subs → **1,10$ / sub**", inline=False)
    embed.add_field(name="💸 Paiement", value="**Payé chaque DIMANCHE** — chaque semaine, pas toutes les 2 semaines comme les autres agences.\nPlus tu postes = plus tu montes = plus chaque sub rapporte.", inline=False)
    embed.set_footer(text="SMITH BG Agence")
    await salon_paiement.send("@everyone", embed=embed)
    await ctx.send(f"✅ Grille envoyée dans {salon_paiement.mention}")

@bot.command()
async def fixsalons(ctx):
    if not ctx.author.guild_permissions.administrator: return
    role_manager = discord.utils.get(ctx.guild.roles, name=NOM_ROLE_MANAGER)
    role_teamleader = discord.utils.get(ctx.guild.roles, name="Team Leader")
    if not role_teamleader:
        role_teamleader = discord.utils.get(ctx.guild.roles, name="team leader")
    if not role_teamleader:
        role_teamleader = await get_or_create_role(ctx.guild, "Team Leader", discord.Colour.green())
    categorie = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE)
    if not categorie:
        await ctx.send("❌ Catégorie CLIENTS pas trouvée")
        return
    count = 0
    for ch in categorie.text_channels:
        if "🔒・" in ch.name:
            try:
                if role_manager:
                    await ch.set_permissions(role_manager, read_messages=True, send_messages=True)
                if role_teamleader:
                    await ch.set_permissions(role_teamleader, read_messages=True, send_messages=True)
                count += 1
            except: pass
    await ctx.send(f"✅ Accès Manager + Team Leader ajouté sur {count} salons privés")

@bot.command()
async def setupfinal(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("🚀 Je répare tout...")
    role_manager = discord.utils.get(ctx.guild.roles, name=NOM_ROLE_MANAGER)
    role_teamleader = discord.utils.get(ctx.guild.roles, name="Team Leader")
    if not role_teamleader:
        role_teamleader = discord.utils.get(ctx.guild.roles, name="team leader")
    if not role_teamleader:
        role_teamleader = await get_or_create_role(ctx.guild, "Team Leader", discord.Colour.green())
    categorie = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE)
    count = 0
    if categorie:
        for ch in categorie.text_channels:
            if "🔒・" in ch.name:
                try:
                    if role_manager:
                        await ch.set_permissions(role_manager, read_messages=True, send_messages=True)
                    if role_teamleader:
                        await ch.set_permissions(role_teamleader, read_messages=True, send_messages=True)
                    count += 1
                except: pass
    cat_num = discord.utils.get(ctx.guild.categories, name="📞 NUMEROS")
    if not cat_num:
        cat_num = await ctx.guild.create_category("📞 NUMEROS")
    for ch in list(ctx.guild.text_channels):
        if "numero" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    }
    salon_usa = await ctx.guild.create_text_channel(name="🇺🇸┃numero-usa", category=cat_num, overwrites=overwrites)
    salon_gmail = await ctx.guild.create_text_channel(name="📞┃numero-gmail", category=cat_num, overwrites=overwrites)
    overwrites_logs = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
    }
    for r in ctx.guild.roles:
        if r.permissions.administrator or "Manager" in r.name or "Team Leader" in r.name:
            overwrites_logs[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
    logs = discord.utils.get(ctx.guild.text_channels, name="logs-numeros")
    if not logs:
        logs = await ctx.guild.create_text_channel(name="logs-numeros", category=cat_num, overwrites=overwrites_logs)
    embed_panel = discord.Embed(color=0x2b2d31, title="📞 Choisis ton numéro", description="Sélectionne le pays :\n\n🇺🇸 USA\n🇨🇦 Canada\n🇬🇧 Angleterre\n🇺🇦 Ukraine\n\n**Seul toi verras ton numéro**")
    await salon_usa.send(embed=embed_panel, view=ViewChoixPays())
    await salon_gmail.send(embed=embed_panel, view=ViewChoixPays())
    salon_paiement = None
    for ch in ctx.guild.text_channels:
        if "paiement" in ch.name.lower() or "paiment" in ch.name.lower():
            salon_paiement = ch
            break
    if salon_paiement:
        embed = discord.Embed(title="📊 Grille de Paie 🤑", description="Plus tu montes en subs, plus ton $/sub augmente 🔥 (selon ton total de subs)", color=0xFFD700)
        embed.add_field(name="👑 Paliers", value="De 0 à 500 subs → **0,50$ / sub**\nDe 500 à 700 subs → **0,60$ / sub**\nDe 700 à 800 subs → **0,70$ / sub**\nDe 800 à 1000 subs → **0,80$ / sub**\nDe 1000 à 1500 subs → **1$ / sub**\nDe 1500 à 2000 subs → **1,10$ / sub**", inline=False)
        embed.add_field(name="💸 Paiement", value="**Payé chaque DIMANCHE** — chaque semaine, pas toutes les 2 semaines comme les autres agences.\nPlus tu postes = plus tu montes = plus chaque sub rapporte.", inline=False)
        embed.set_footer(text="SMITH BG Agence")
        await salon_paiement.send("@everyone", embed=embed)
    await ctx.send(f"✅ TOUT FAIT : {count} salons réparés + 2 salons numéros + grille envoyée")

bot.run(os.getenv("DISCORD_TOKEN"))
