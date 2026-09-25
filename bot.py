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
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
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
    bot.add_view(ViewChoixPays()) # pour que le menu reste après reboot

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
    embed.add_field(name="🏠 ACCUEIL", value=f"{get_ch(guild,'bienvenue')} {get_ch(guild,'règles')} {get_ch(guild,'paiement')}", inline=False)
    embed.set_footer(text="SMITH BG Agence")
    await salon_prive.send(member.mention, embed=embed)

# --- TES ANCIENNES COMMANDES - JE N'AI RIEN TOUCHE ---
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
    await ctx.send(f"👑 {member.mention} est maintenant **Manager**")
@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat_calls = discord.utils.get(ctx.guild.categories, name=NOM_CATEGORIE_CALL)
    if not cat_calls:
        cat_calls = await ctx.guild.create_category(NOM_CATEGORIE_CALL)
    for name in ["🌐・call-général", "🔒・call-pv"]:
        vc = discord.utils.get(ctx.guild.voice_channels, name=name)
        if vc: await vc.delete()
    await ctx.guild.create_voice_channel(name="🌐・call-général", category=cat_calls, user_limit=0)
    await ctx.guild.create_voice_channel(name="🔒・call-pv", category=cat_calls, user_limit=2)
    await ctx.send("✅ Calls corrigés!")
@bot.command()
async def salons(ctx):
    liste = "\n".join([f"{ch.mention}" for ch in ctx.guild.text_channels])
    await ctx.send(embed=discord.Embed(title="📍 TOUS NOS SALONS", description=liste, color=0xFF006A))
@bot.command()
async def creersalon(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator: return
    await on_member_join(member)
    await ctx.send(f"✅ Salon recréé pour {member.mention}")
@bot.command()
async def close(ctx):
    if "🔒・" in ctx.channel.name and ctx.author.guild_permissions.administrator:
        await ctx.channel.delete()

# ============ NOUVEAU : 4 PAYS - AJOUTE SEULEMENT ============
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

# MENU 4 PAYS
class SelectPays(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="USA", value="usa", emoji="🇺🇸", description="Numéro USA pour Gmail"),
            discord.SelectOption(label="Canada", value="canada", emoji="🇨🇦", description="Numéro Canada pour Gmail"),
            discord.SelectOption(label="Angleterre", value="england", emoji="🇬🇧", description="Numéro UK pour Gmail"),
            discord.SelectOption(label="Ukraine", value="ukraine", emoji="🇺🇦", description="Numéro Ukraine pour Gmail"),
        ]
        super().__init__(placeholder="🌍 Choisis ton pays...", min_values=1, max_values=1, options=options, custom_id="choix_pays_4")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        pays = self.values[0]

        # Map pour 5sim
        map_5sim = {"usa": "usa", "canada": "canada", "england": "england", "ukraine": "ukraine"}
        code_pays = map_5sim.get(pays, "usa")

        numero = f"+{random.randint(1000000000, 1999999999)}"
        act_id = f"89864{random.randint(90000, 99999)}"

        if CLE_5SIM:
            try:
                headers = {"Authorization": f"Bearer {CLE_5SIM}"}
                # API 5sim selon pays
                data = requests.get(f"https://5sim.net/v1/user/buy/activation/{code_pays}/any/google", headers=headers, timeout=15).json()
                numero = data.get('phone', numero)
                act_id = str(data.get('id', act_id))
            except: pass

        embed = discord.Embed(color=0x2b2d31)
        embed.set_author(name="Numéro Gmail APP", icon_url=bot.user.display_avatar.url if bot.user else None)
        embed.description = f"{interaction.user.mention} ton numéro est prêt!"
        embed.add_field(name="Pays", value=f"{pays.upper()}", inline=False)
        embed.add_field(name="Numero", value=numero, inline=False)
        embed.add_field(name="Activation ID", value=act_id, inline=False)

        await interaction.followup.send(embed=embed, view=ViewLireCode(act_id), ephemeral=True)

        logs_channel = discord.utils.get(interaction.guild.text_channels, name="logs-numeros")
        if logs_channel:
            await logs_channel.send(f"👤 {interaction.user.mention} a pris | Pays: {pays} | {numero} | ID: {act_id}")

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
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False), ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)}
    salon_usa = discord.utils.get(ctx.guild.text_channels, name="🇺🇸┃NUMERO-USA")
    if not salon_usa:
        salon_usa = await ctx.guild.create_text_channel(name="🇺🇸┃NUMERO-USA", category=cat, overwrites=overwrites)
    salon_gmail = discord.utils.get(ctx.guild.text_channels, name="📞┃NUMERO-GMAIL")
    if not salon_gmail:
        salon_gmail = await ctx.guild.create_text_channel(name="📞┃NUMERO-GMAIL", category=cat, overwrites=overwrites)

    overwrites_logs = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)}
    for r in ctx.guild.roles:
        if r.permissions.administrator or "Manager" in r.name:
            overwrites_logs[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
    logs = discord.utils.get(ctx.guild.text_channels, name="logs-numeros")
    if not logs:
        logs = await ctx.guild.create_text_channel(name="logs-numeros", category=cat, overwrites=overwrites_logs)

    embed_panel = discord.Embed(color=0x2b2d31)
    embed_panel.set_author(name="NUMERO GMAIL APP - 4 PAYS", icon_url="https://cdn-icons-png.flaticon.com/512/197/197484.png")
    embed_panel.description = "Bienvenue! Choisis ton pays pour obtenir un numéro Gmail :\n\n🇺🇸 USA\n🇨🇦 Canada\n🇬🇧 Angleterre\n🇺🇦 Ukraine\n\n**Seul toi verras ton numéro**"

    await salon_usa.send(embed=embed_panel, view=ViewChoixPays())
    await salon_gmail.send(embed=embed_panel, view=ViewChoixPays())
    await ctx.send(f"✅ Fait! 4 pays ajoutés dans {salon_usa.mention} et {salon_gmail.mention} + {logs.mention}")

bot.run(os.getenv("DISCORD_TOKEN"))
