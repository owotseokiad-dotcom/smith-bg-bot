from flask import Flask
import threading
import os
import discord
from discord.ext import commands
import requests
import random
# --- AJOUTS POUR TES 2 SALONS (je touche pas au reste) ---
import re
import io
import yt_dlp

app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE OFM EN LIGNE"
def run_web(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_web).start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

NOM_AGENCE = "Ramane |OFM"
NOM_CATEGORIE = "📈 CLIENTS"
NOM_CATEGORIE_CALL = "🔊 CALLS"
NOM_ROLE_CLIENT = "Client Insta"
NOM_ROLE_MANAGER = "Manager"

NOMS_FILLES = ["Sophie","Mia","Emma","Lina","Chloe","Luna","Ava","Sofia","Lily","Nina","Eva","Ruby","Bella","Zoe","Maya","Lea","Jade","Mila","Sara","Elisa","Noa","Lola","Ines","Camille","Julie"]
SUFFIXES = ["rose","dream","love","sweet","babe","doll","angel","honey","bliss","vibe","bloom","glow","petal","charm"]

async def get_bios_from_salon(guild):
    salon_bio = None
    for ch in guild.text_channels:
        if "bio" in ch.name.lower():
            salon_bio = ch
            break
    if not salon_bio:
        return ["19 🎀 sweet girl next door | DM me 💌", "20 💋 your fav blonde | let's chat"]
    bios = []
    async for msg in salon_bio.history(limit=200):
        if msg.content and len(msg.content) > 10:
            if not msg.content.startswith("!") and not msg.content.startswith("?"):
                bios.append(msg.content)
    if not bios:
        bios = ["19 🎀 sweet girl next door | DM me 💌"]
    return bios

async def get_photos_from_salon(guild):
    salon_photo = None
    for ch in guild.text_channels:
        name = ch.name.lower()
        if "photo" in name or "pdp" in name or "pfp" in name or "profil" in name or "avatar" in name:
            if "pseudo" not in name:
                salon_photo = ch
                break
    if not salon_photo:
        return []
    photos = []
    async for msg in salon_photo.history(limit=200):
        if msg.attachments:
            for att in msg.attachments:
                if att.content_type and "image" in att.content_type:
                    photos.append(att.url)
        if msg.content and "http" in msg.content and ("cdn.discord" in msg.content or "tenor" not in msg.content):
            photos.append(msg.content.split()[0])
    return photos

def generer_pseudo_inutilise():
    prenom = random.choice(NOMS_FILLES).lower()
    suffix = random.choice(SUFFIXES)
    lettres = ''.join(random.choices("abcdefghijkmnopqrstuvwxyz", k=2))
    pseudo_sans_point = f"{prenom}{suffix}{lettres}"
    pseudo_avec_point = f"{prenom}.{suffix}{lettres}"
    chiffre = random.randint(10, 99)
    pseudo_avec_chiffre = f"{prenom}{suffix}{chiffre}{lettres}"
    return pseudo_sans_point, pseudo_avec_point, pseudo_avec_chiffre

@bot.event
async def on_ready():
    print(f"✅ {NOM_AGENCE} EN LIGNE {bot.user}")
    bot.add_view(ViewPseudosFilles())
    bot.add_view(ViewChoixPays())

@bot.event
async def on_member_join(member):
    guild = member.guild
    role = discord.utils.get(guild.roles, name=NOM_ROLE_CLIENT)
    if not role:
        role = await guild.create_role(name=NOM_ROLE_CLIENT, colour=discord.Colour.pink())
    await member.add_roles(role)
    categorie = discord.utils.get(guild.categories, name=NOM_CATEGORIE)
    if not categorie:
        categorie = await guild.create_category(NOM_CATEGORIE)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    salon_prive = await guild.create_text_channel(name=f"🔒・{member.name.lower()}", category=categorie, overwrites=overwrites)
    await salon_prive.send(f"Bienvenue {member.mention} chez {NOM_AGENCE}")

class ViewPseudosFilles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎀 Pseudo", style=discord.ButtonStyle.primary, custom_id="btn_pseudo_fille_final")
    async def pseudo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        pseudo_sans, pseudo_point, pseudo_chiffre = generer_pseudo_inutilise()
        bios = await get_bios_from_salon(interaction.guild)
        photos = await get_photos_from_salon(interaction.guild)
        bio_choisie = random.choice(bios) if bios else "19 🎀 sweet girl | DM me"
        photo_choisie = random.choice(photos) if photos else None
        embed = discord.Embed(color=0xFF69B4, title="🎀 Identité générée depuis ton serveur", description="**Seule toi vois ce message** - Données prises dans tes salons")
        embed.add_field(name="👤 Pseudo SANS chiffre SANS point (RECOMMANDÉ - unique)", value=f"`{pseudo_sans}`", inline=False)
        embed.add_field(name="👤 Pseudo avec point", value=f"`{pseudo_point}`", inline=False)
        embed.add_field(name="🔢 Pseudo avec chiffres (si sans chiffre pris)", value=f"`{pseudo_chiffre}`", inline=False)
        embed.add_field(name="📝 Bio piquée dans #bio", value=f"```{bio_choisie[:1000]}```", inline=False)
        if photo_choisie:
            embed.set_image(url=photo_choisie)
            embed.add_field(name="📸 Photo de profil piquée", value="Photo ci-dessus vient de ton salon photo/pdp", inline=False)
        else:
            embed.add_field(name="📸 Photo de profil", value="⚠️ J'ai pas trouvé de salon photo. Mets tes PDP dans un salon qui s'appelle `photos` ou `pdp`", inline=False)
        embed.set_footer(text=f"{NOM_AGENCE} | Pseudo généré pour être non-utilisé sur Insta")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logs = discord.utils.get(interaction.guild.text_channels, name="logs-pseudos")
        if logs:
            await logs.send(f"👤 {interaction.user.mention} a généré `{pseudo_sans}` | bio + photo piquées")

@bot.command()
async def setupfilles(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = discord.utils.get(ctx.guild.categories, name="🎀 MODELES")
    if not cat:
        cat = await ctx.guild.create_category("🎀 MODELES")
    for ch in list(ctx.guild.text_channels):
        if "pseudos-filles" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    }
    salon = await ctx.guild.create_text_channel(name="🎀┃pseudos-filles", category=cat, overwrites=overwrites)
    logs = discord.utils.get(ctx.guild.text_channels, name="logs-pseudos")
    if not logs:
        overwrites_logs = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)}
        for r in ctx.guild.roles:
            if r.permissions.administrator or "Manager" in r.name or "Team Leader" in r.name:
                overwrites_logs[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
        logs = await ctx.guild.create_text_channel(name="logs-pseudos", category=cat, overwrites=overwrites_logs)
    embed_panel = discord.Embed(color=0xFF69B4, title="🎀 Générateur d'identités OFM", description="Le bot va piocher AUTOMATIQUEMENT dans tes salons existants :\n\n📝 **Bios** -> dans le salon qui contient `bio`\n📸 **Photos** -> dans le salon qui contient `photo` / `pdp` / `profil`\n\nClique sur **🎀 Pseudo** en bas et tu reçois :\n✅ Pseudo SANS chiffre SANS point (unique, non utilisé)\n✅ Bio de ton agence\n✅ Photo de profil de ton agence")
    await salon.send(embed=embed_panel, view=ViewPseudosFilles())
    await ctx.send(f"✅ Salon créé : {salon.mention} - il va piquer dans tes salons bio + photo existants")

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
            await interaction.followup.send(f"⏳ Pas encore, reclique 30s", ephemeral=True)

class SelectPays(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="USA", value="usa", emoji="🇺🇸"), discord.SelectOption(label="Canada", value="canada", emoji="🇨🇦"), discord.SelectOption(label="Angleterre", value="england", emoji="🇬🇧"), discord.SelectOption(label="Ukraine", value="ukraine", emoji="🇺🇦")]
        super().__init__(placeholder="🌍 Choisis ton pays...", options=options, custom_id="choix_pays_final")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Numéro généré (logique 5sim ici)", ephemeral=True)

class ViewChoixPays(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPays())

# ============================================================
# ===== CODE AJOUTÉ - 2 SALONS AUTO QUE TU AS DEMANDÉ ========
# ============================================================
def scan_insta_viral(url):
    ydl_opts = {'quiet': True, 'extract_flat': False, 'skip_download': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            videos = []
            entries = info.get('entries', [info])
            for e in entries:
                if not e: continue
                views = e.get('view_count', 0) or e.get('like_count', 0) or 0
                videos.append({
                    'url': e.get('webpage_url') or url,
                    'desc': e.get('description','') or e.get('title',''),
                    'views': views,
                })
            videos = sorted(videos, key=lambda x: x['views'], reverse=True)
            return videos[:8]
    except Exception as ex:
        print(ex)
        return []

@bot.command()
async def setupauto(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    for ch in list(ctx.guild.text_channels):
        if "comptes-instagram" in ch.name.lower() or "videos-recues" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True), ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)}
    salon1 = await ctx.guild.create_text_channel(name="📥┃comptes-instagram", category=cat, overwrites=overwrites)
    salon2 = await ctx.guild.create_text_channel(name="📤┃videos-recues", category=cat, overwrites=overwrites)
    await salon1.send("📥 **COLLE ICI LES LIENS INSTA QUI ONT PERCÉ**\nExemple: `https://www.instagram.com/nom_du_compte/`\nLe bot va auto envoyer les 8 vidéos virales dans 📤┃videos-recues")
    await salon2.send("📤 **ICI TU REÇOIS LES VIDÉOS**\nCe salon reçoit auto les 8 vidéos (même fille, triées par vues)")
    await ctx.send(f"✅ C'est fait: {salon1.mention} -> {salon2.mention}")

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    if "instagram.com" in message.content and ("comptes" in message.channel.name.lower() or "insta" in message.channel.name.lower()):
        if "videos-recues" in message.channel.name.lower() or "banque" in message.channel.name.lower():
            await bot.process_commands(message)
            return
        urls = re.findall(r'https?://(?:www\.)?instagram\.com/\S+', message.content)
        if urls:
            url = urls[0]
            await message.channel.send(f"⏳ Je scanne `{url}`... J'envoie les 8 vidéos dans 📤┃videos-recues")
            videos = scan_insta_viral(url)
            salon_recoit = discord.utils.get(message.guild.text_channels, name="📤┃videos-recues")
            if not salon_recoit:
                cat = discord.utils.get(message.guild.categories, name="🎀 MODELES")
                salon_recoit = await message.guild.create_text_channel(name="📤┃videos-recues", category=cat)
            if not videos:
                await salon_recoit.send(f"❌ Impossible de scanner {url} - compte privé ou Insta bloque.")
                await bot.process_commands(message)
                return
            file_content = f"PACK VIRAL DE {url}\n"
            for i, v in enumerate(videos, 1):
                file_content += f"{i}. {v['url']} - {v['views']} vues\n"
            file_bytes = io.BytesIO(file_content.encode('utf-8'))
            discord_file = discord.File(file_bytes, filename=f"PACK_{random.randint(100,999)}.txt")
            embed = discord.Embed(color=0x00FF88, title=f"📤 Pack reçu depuis {message.channel.name}", description=f"Source : {url}\nPar {message.author.mention}\n**8 vidéos même fille, triées par viralité**")
            for i, v in enumerate(videos, 1):
                embed.add_field(name=f"{i}. {v['views']} vues", value=f"{v['url']}", inline=False)
            await salon_recoit.send(embed=embed, file=discord_file)
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
