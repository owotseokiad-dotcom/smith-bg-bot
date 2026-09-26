try:
    import audioop
except ModuleNotFoundError:
    import sys
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop

from flask import Flask
import threading, os, discord, requests, random, re, tempfile, asyncio, json
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE OFM EN LIGNE"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.instagram.com/{username}/", download=False)
            if info.get('is_verified') == True:
                return False, "❌ Compte certifié"
            return True, "OK"
    except:
        return True, "OK"

def get_all_viral_sync(insta_url):
    import yt_dlp
    ydl_opts = {'quiet': True, 'extract_flat': False, 'skip_download': True}
    posts=[]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(insta_url, download=False)
            entries = info.get('entries', []) or []
            for e in entries:
                views = e.get('view_count',0) or e.get('like_count',0) or 0
                url = e.get('url') or e.get('webpage_url') or f"https://www.instagram.com/reel/{e.get('id')}/"
                desc = e.get('description') or e.get('title') or ""
                posts.append({'url': url, 'views': views, 'desc': desc[:1000], 'id': e.get('id')})
        posts = sorted(posts, key=lambda x: x['views'], reverse=True)
        return posts
    except Exception as e:
        print(f"ERREUR VIRAL {e}"); return []

# NOUVEAU : Télécharge la vraie vidéo Insta en mp4
def download_insta_reel_sync(insta_url):
    import yt_dlp
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    ydl_opts = {
        'quiet': True,
        'outtmpl': tmp_path,
        'format': 'best[ext=mp4]/best',
        'noplaylist': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([insta_url])
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
            return tmp_path
        return None
    except Exception as e:
        print(f"DOWNLOAD INSTA FAIL {e}")
        return None

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'/folders/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    return m.group(1) if m else None

async def get_drive_reels_grouped(guild):
    salons_drive = [ch for ch in guild.text_channels if "drive" in ch.name.lower()]
    if not salons_drive: return []
    salon_choisi = random.choice(salons_drive)
    reels=[]
    async for m in salon_choisi.history(limit=500):
        for att in m.attachments:
            if att.content_type and "video" in att.content_type:
                reels.append({'type': 'discord', 'url': att.url, 'name': att.filename})
        if "drive.google.com" in m.content:
            urls = re.findall(r'https?://drive\.google\.com/\S+', m.content)
            for url in urls:
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
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    session = requests.Session()
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
        if "modele" in cat.name.lower() or "modèle" in cat.name.lower(): return cat
    return guild.categories[0] if guild.categories else None

class ModalScanInsta(discord.ui.Modal, title="Scanner un compte Insta"):
    lien = discord.ui.TextInput(label="Colle le lien Instagram ici", placeholder="https://www.instagram.com/username/", style=discord.TextStyle.short)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        m=re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', self.lien.value)
        if not m:
            await interaction.followup.send("❌ Lien invalide", ephemeral=True); return
        username=m.group(1).split('/')[0]
        clean=f"https://www.instagram.com/{username}/reels/"
        is_ok, msg = await bot.loop.run_in_executor(None, lambda: check_compte_us_non_certifie(username))
        if not is_ok:
            await interaction.followup.send(f"{msg} @{username} ignoré", ephemeral=True); return
        await interaction.followup.send(f"🔍 Scan @{username} en cours...", ephemeral=True)
        viral=await bot.loop.run_in_executor(None, lambda: get_all_viral_sync(clean))
        if not viral:
            await interaction.channel.send(f"❌ Rien trouvé pour @{username}"); return
        db=load_db(); uid=str(interaction.user.id)
        if uid not in db: db[uid]=[]
        db[uid].extend(viral)
        seen=set(); uniq=[]
        for v in db[uid]:
            if v['url'] not in seen:
                uniq.append(v); seen.add(v['url'])
        db[uid]=uniq; save_db(db)
        thread=await interaction.channel.create_thread(name=f"viral-{username}-{len(viral)}", auto_archive_duration=60)
        try: await thread.add_user(interaction.user)
        except: pass
        embed=discord.Embed(color=0xE1306C, title=f"{len(viral)} VIDEOS - @{username} STOCKÉES [US NON CERTIFIÉ]", description="Trié du plus vu au moins vu")
        txt=""
        for i,p in enumerate(viral[:20],1): txt+=f"{i}. {p['views']} vues - {p['url']}\n{p['desc'][:50]}...\n\n"
        embed.description=txt[:4000]
        await thread.send(f"{interaction.user.mention}", embed=embed)
        await interaction.channel.send(f"✅ @{username} -> {len(viral)} stockées -> {thread.mention}")

class ViewScanCompte(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔍 SCANNER UN COMPTE", style=discord.ButtonStyle.danger, custom_id="btn_scan_insta_final_v3")
    async def scan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalScanInsta())

class ViewMesVideos(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="MES VIDEOS VIRALES", style=discord.ButtonStyle.primary, custom_id="btn_mes_videos_v3")
    async def mes_videos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        db = load_db(); mine = db.get(str(interaction.user.id), [])
        if not mine: await interaction.followup.send("Aucune vidéo encore", ephemeral=True); return
        mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
        embed=discord.Embed(color=0xE1306C, title=f"TON STOCK VIRAL - {len(mine_sorted)}")
        txt=""
        for i, p in enumerate(mine_sorted[:20], 1): txt+=f"{i}. {p['views']} vues - {p['url']}\n"
        embed.description=txt[:4000]
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Generer 8 Packs Reels", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final_v5")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Génération en cours... 8 DRIVE + 8 VIRALES (vraies vidéos)", ephemeral=True)
        reels=await get_drive_reels_grouped(interaction.guild)
        descs=await get_descriptions(interaction.guild)
        if len(reels)<8:
            await interaction.followup.send(f"Stock drive insuffisant: {len(reels)}/8 videos", ephemeral=True); return
        random.shuffle(reels); random.shuffle(descs)
        reels = reels[:8]
        salon_out=None
        for ch in interaction.guild.text_channels:
            if "packs-reels" in ch.name.lower(): salon_out=ch; break
        if not salon_out: salon_out=interaction.channel
        thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", auto_archive_duration=60)
        try: await thread.add_user(interaction.user)
        except: pass
        await interaction.followup.send(f"Pack créé {thread.mention}", ephemeral=True)
        sent=[]
        w=await thread.send(f"{interaction.user.mention} **PACK 8 DRIVE + VIRALES**\n\n__PARTIE 1: 8 PACKS DRIVE (minimum 8)__"); sent.append(w)
        # PARTIE 1 : 8 DRIVE
        for i in range(8):
            r=reels[i]; d=descs[i] if i < len(descs) else None
            try:
                desc_text = d.content[:1024] if d else "Pas de description dispo"
                if r['type'] == 'discord':
                    data = await bot.loop.run_in_executor(None, lambda: requests.get(r['url']).content)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.write(data); tmp.close()
                    embed=discord.Embed(color=0x00FF88, title=f"PACK DRIVE {i+1}/8")
                    embed.add_field(name="DESCRIPTION DRIVE", value=desc_text, inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(tmp.name, filename=r['name'])); sent.append(msg); os.unlink(tmp.name)
                else:
                    path = await bot.loop.run_in_executor(None, lambda: download_gdrive_file_sync(r['id']))
                    embed=discord.Embed(color=0x00FF88, title=f"PACK DRIVE {i+1}/8")
                    embed.add_field(name="DESCRIPTION DRIVE", value=desc_text, inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(path, filename=r.get('name', f"reel_{i+1}.mp4"))); sent.append(msg); os.unlink(path)
            except Exception as e: print(e)

        # PARTIE 2 : 8 VIRALES - VRAIES VIDEOS MP4 PAS DE LIENS
        db=load_db(); mine = db.get(str(interaction.user.id), [])
        if mine:
            mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
            to_send = mine_sorted[:8] if len(mine_sorted)>=8 else mine_sorted
            w2=await thread.send(f"\n__PARTIE 2: {len(to_send)} VIDEOS VIRALES US QUI PERCENT VRAIMENT (vidéo + description) - PAS DE LIEN__"); sent.append(w2)
            for idx, p in enumerate(to_send, 1):
                try:
                    await thread.send(f"⬇️ Téléchargement VIRAL {idx}/{len(to_send)} - {p['views']} vues en cours...")
                    path = await bot.loop.run_in_executor(None, lambda: download_insta_reel_sync(p['url']))
                    if path and os.path.exists(path):
                        embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx}/{len(to_send)} - {p['views']} vues")
                        embed.add_field(name="DESCRIPTION INSTA ORIGINALE", value=p.get('desc','Pas de desc')[:1024], inline=False)
                        embed.add_field(name="INFOS", value=f"Vues: {p['views']}\nUS: Oui\nCertifié: Non", inline=False)
                        msg=await thread.send(embed=embed, file=discord.File(path, filename=f"viral_us_{idx}.mp4")); sent.append(msg)
                        os.unlink(path)
                    else:
                        embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx}/{len(to_send)} - {p['views']} vues")
                        embed.add_field(name="DESCRIPTION INSTA ORIGINALE", value=p.get('desc','Pas de desc')[:1024], inline=False)
                        embed.add_field(name="VIDÉO", value=f"⚠️ Téléchargement échoué, voici le lien temporaire: {p['url']}", inline=False)
                        msg=await thread.send(embed=embed); sent.append(msg)
                except Exception as e:
                    print(e)
        else:
            await thread.send("⚠️ Aucune vidéo virale stockée. Va scanner des comptes dans #comptes-instagram d'abord")

        if sent:
            bot.loop.create_task(delete_after(sent, 15))

@bot.command()
async def setupcomptes(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "comptes-instagram" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    salon=await ctx.guild.create_text_channel(name="comptes-instagram", category=cat, overwrites=overwrites)
    embed=discord.Embed(color=0xE1306C, title="Ramane | OFM - Détecteur", description="🚫 ÉCRITURE BLOQUÉE\nClique le bouton, colle le lien Insta US non certifié, je stocke ses tops qui percent")
    await salon.send(embed=embed, view=ViewScanCompte())
    await ctx.send(f"OK {salon.mention} bloqué ✅")

@bot.command()
async def setuppack(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "packs-reels" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    salon=await ctx.guild.create_text_channel(name="packs-reels", category=cat, overwrites=overwrites)
    embed = discord.Embed(color=0x00FF88, title="Générateur de Packs", description="🚫 ÉCRITURE BLOQUÉE\nClique le bouton vert - Il t'envoie 8 DRIVE + 8 VIRALES US (vraies vidéos + descriptions, pas de liens)")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"OK {salon.mention} bloqué ✅")

@bot.command()
async def setupviral(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat = get_cat_modeles(ctx.guild)
    for ch in list(ctx.guild.text_channels):
        if "mes-videos-virales" in ch.name.lower():
            try: await ch.delete()
            except: pass
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    salon=await ctx.guild.create_text_channel(name="mes-videos-virales", category=cat, overwrites=overwrites)
    await salon.send(embed=discord.Embed(color=0xE1306C, title="Stock Viral"), view=ViewMesVideos())
    await ctx.send(f"OK {salon.mention} bloqué ✅")

@bot.event
async def on_ready():
    print(f"EN LIGNE {NOM_AGENCE}")
    bot.add_view(ViewScanCompte())
    bot.add_view(ViewMesVideos())
    bot.add_view(ViewPackReels())

bot.run(os.getenv("DISCORD_TOKEN"))
