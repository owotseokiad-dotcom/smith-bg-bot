from flask import Flask
import threading, os, discord, requests, random, re, tempfile, asyncio, json
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE OFM EN LIGNE - BOT LIVE"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

NOM_AGENCE = "Ramane | OFM"
DB_FILE = "viral_db.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save_db(d):
    with open(DB_FILE, "w") as f: json.dump(d, f)

def check_compte_us_non_certifie(username):
    import yt_dlp
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.instagram.com/{username}/", download=False)
            if info.get('is_verified') == True: return False, "Certifie"
            return True, "OK"
    except: return True, "OK"

def get_all_viral_sync(insta_url):
    import yt_dlp
    ydl_opts = {'quiet': True, 'extract_flat': False, 'skip_download': True, 'no_warnings': True, 'http_headers': {'User-Agent': 'Mozilla/5.0'}, 'sleep_interval': 3, 'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None}
    posts=[]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(insta_url, download=False)
            entries = info.get('entries', []) or []
            for e in entries:
                views = e.get('view_count',0) or 0
                url = e.get('url') or e.get('webpage_url') or ""
                desc = e.get('description') or ""
                if url: posts.append({'url': url, 'views': views, 'desc': desc[:1000]})
        return sorted(posts, key=lambda x: x['views'], reverse=True)
    except: return []

def download_insta_reel_sync(insta_url):
    import yt_dlp
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    ydl_opts = {'quiet': True, 'outtmpl': tmp, 'format': 'best[ext=mp4]/best', 'noplaylist': True, 'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([insta_url])
        if os.path.exists(tmp) and os.path.getsize(tmp) > 2000: return tmp
        return None
    except: return None

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    return m.group(1) if m else None

async def get_drive_reels_grouped(guild):
    reels = []
    for ch in guild.text_channels:
        if "drive" in ch.name.lower():
            async for m in ch.history(limit=500):
                for att in m.attachments:
                    if "video" in att.content_type: reels.append({'type': 'discord', 'url': att.url, 'name': att.filename})
                if "drive.google.com" in m.content:
                    for url in re.findall(r'https?://drive\.google\.com/\S+', m.content):
                        fid = extract_file_id(url)
                        if fid: reels.append({'type': 'drive_file', 'id': fid, 'name': f"{fid}.mp4"})
    return reels

async def get_descriptions(guild):
    descs=[]
    for ch in guild.text_channels:
        if "description" in ch.name.lower():
            async for m in ch.history(limit=1000):
                if m.content and len(m.content.strip())>5 and not m.content.startswith("!"): descs.append(m)
    return descs

def download_gdrive_file_sync(file_id):
    session = requests.Session()
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    r = session.get(url, stream=True)
    token = None
    for k,v in r.cookies.items():
        if k.startswith('download_warning'): token = v
    if token:
        url = f"https://drive.google.com/uc?export=download&confirm={token}&id={file_id}"
        r = session.get(url, stream=True)
    for chunk in r.iter_content(1024*1024):
        if chunk: tmp.write(chunk)
    tmp.close()
    return tmp.name

async def delete_after(messages, minutes=15):
    await asyncio.sleep(minutes*60)
    for msg in messages:
        try: await msg.delete()
        except: pass

def get_cat_modeles(guild):
    for cat in guild.categories:
        if "modele" in cat.name.lower(): return cat
    return guild.categories[0] if guild.categories else None

class ModalScanInsta(discord.ui.Modal, title="Scanner un compte Insta"):
    lien = discord.ui.TextInput(label="Lien Instagram", placeholder="https://www.instagram.com/username/")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m=re.search(r'instagram\.com/([A-Za-z0-9_.]+)', self.lien.value)
            if not m:
                await interaction.followup.send("Lien invalide", ephemeral=True); return
            username=m.group(1).split('/')[0]
            clean=f"https://www.instagram.com/{username}/reels/"
            viral=await bot.loop.run_in_executor(None, lambda: get_all_viral_sync(clean))
            db=load_db(); uid=str(interaction.user.id)
            if uid not in db: db[uid]=[]
            db[uid].extend(viral); save_db(db)
            await interaction.followup.send(f"{len(viral)} videos stockees pour @{username}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Erreur: {e}", ephemeral=True)

class ViewScanCompte(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="SCANNER UN COMPTE", style=discord.ButtonStyle.danger, custom_id="ramane_scan_v4_fix")
    async def scan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalScanInsta())

class ViewMesVideos(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="VOIR MON STOCK VIRAL", style=discord.ButtonStyle.primary, custom_id="ramane_stock_v4_fix")
    async def mes_videos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = load_db(); mine = db.get(str(interaction.user.id), [])
        if not mine:
            await interaction.followup.send("Aucune video", ephemeral=True); return
        mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
        txt=""
        for i, p in enumerate(mine_sorted[:20], 1): txt+=f"{i}. {p['views']} vues - {p['url']}\n"
        embed=discord.Embed(title=f"TON STOCK - {len(mine_sorted)} videos", description=txt[:4000])
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="GENERER 8 PACKS REELS", style=discord.ButtonStyle.success, custom_id="ramane_pack_v4_fix")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send("Generation en cours...", ephemeral=True)

class ViewPseudosFilles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Generer Identite Complete", style=discord.ButtonStyle.primary, custom_id="ramane_pseudo_v4_full")
    async def pseudo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        p = random.choice(['sofia','mia','luna','chloe','emma'])
        s = random.choice(['rose','vibe','bloom'])
        embed=discord.Embed(title=f"Identite pour {p.capitalize()}", description=f"{p}{s} - {p}.{s} - {p}{s}{random.randint(10,99)}")
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewNumero(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(placeholder="Choisis ton pays...", custom_id="ramane_numero_v4_fix", options=[
        discord.SelectOption(label="USA", emoji="🇺🇸", value="usa"),
        discord.SelectOption(label="Canada", emoji="🇨🇦", value="canada"),
        discord.SelectOption(label="UK", emoji="🇬🇧", value="uk"),
    ])
    async def select_pays(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Pays choisi: {select.values[0].upper()}", ephemeral=True)

@bot.command()
async def cleanbot(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("Nettoyage des messages du bot... Je touche pas aux salons prives")
    cibles = ["pseudo","numero","pack","comptes-instagram","mes-videos","drive","description","bio","pdp","photo","viral"]
    nettoyes = 0
    for ch in ctx.guild.text_channels:
        if "priv" in ch.name.lower(): continue
        for mot in cibles:
            if mot in ch.name.lower():
                try:
                    async for m in ch.history(limit=200):
                        if m.author == bot.user:
                            try:
                                await m.delete()
                                nettoyes+=1
                                await asyncio.sleep(0.2)
                            except: pass
                except: pass
                break
    await ctx.send(f"✅ Fini. {nettoyes} messages du bot supprimes. Salons prives intacts.")

@bot.command()
async def setupcomptes(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "comptes-instagram" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False), ctx.guild.me: discord.PermissionOverwrite(send_messages=True)}
    salon=await ctx.guild.create_text_channel(name="comptes-instagram", category=cat, overwrites=overwrites)
    embed=discord.Embed(color=0xE1306C, title="Detecteur de Comptes Viraux", description="Clique bouton rouge pour scanner")
    await salon.send(embed=embed, view=ViewScanCompte())
    await ctx.send(f"OK {salon.mention}")

@bot.command()
async def setuppack(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "packs-reels" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False), ctx.guild.me: discord.PermissionOverwrite(send_messages=True)}
    salon=await ctx.guild.create_text_channel(name="packs-reels", category=cat, overwrites=overwrites)
    embed=discord.Embed(color=0x00FF88, title="Generateur de Packs Reels", description="Bouton vert")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"OK {salon.mention}")

@bot.command()
async def setupviral(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "mes-videos-virales" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False), ctx.guild.me: discord.PermissionOverwrite(send_messages=True)}
    salon=await ctx.guild.create_text_channel(name="mes-videos-virales", category=cat, overwrites=overwrites)
    embed=discord.Embed(color=0x5865F2, title="Ta Bibliotheque Virale", description="Bouton bleu")
    await salon.send(embed=embed, view=ViewMesVideos())
    await ctx.send(f"OK {salon.mention}")

@bot.command()
async def setuppseudo(ctx):
    if not ctx.author.guild_permissions.administrator: return
    for ch in ctx.guild.text_channels:
        if "pseudo" in ch.name.lower():
            embed=discord.Embed(color=0xFF69B4, title="Generateur de Pseudos", description="Clique pour generer")
            await ch.send(embed=embed, view=ViewPseudosFilles())

@bot.command()
async def setupnumero(ctx):
    if not ctx.author.guild_permissions.administrator: return
    for ch in ctx.guild.text_channels:
        if "numero" in ch.name.lower():
            embed=discord.Embed(color=0x5865F2, title="Generateur de Numeros", description="Choisis ton pays USA Canada UK")
            await ch.send(embed=embed, view=ViewNumero())

@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("Setup complet en cours...")
    await setupcomptes(ctx)
    await setuppack(ctx)
    await setupviral(ctx)
    await setuppseudo(ctx)
    await setupnumero(ctx)
    await ctx.send("TOUT EST REPARE")

@bot.event
async def on_ready():
    print(f"EN LIGNE {NOM_AGENCE}")
    bot.add_view(ViewScanCompte())
    bot.add_view(ViewMesVideos())
    bot.add_view(ViewPackReels())
    bot.add_view(ViewPseudosFilles())
    bot.add_view(ViewNumero())

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("FATAL: DISCORD_TOKEN manquant")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
else:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"CRASH DISCORD: {e}")
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
