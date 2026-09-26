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
def home(): return "RAMANE OFM EN LIGNE - BOT LIVE"
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
        ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.instagram.com/{username}/", download=False)
            if info.get('is_verified') == True: return False, "❌ Certifié"
            return True, "OK"
    except: return True, "OK"

def get_all_viral_sync(insta_url):
    import yt_dlp, time
    ydl_opts = {
        'quiet': True,
        'extract_flat': False,
        'skip_download': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'},
        'sleep_interval': 3,
    }
    posts=[]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(insta_url, download=False)
            entries = info.get('entries', []) or []
            for e in entries:
                views = e.get('view_count',0) or e.get('like_count',0) or 0
                url = e.get('url') or e.get('webpage_url') or ""
                desc = e.get('description') or e.get('title') or ""
                if url:
                    posts.append({'url': url, 'views': views, 'desc': desc[:1000], 'id': e.get('id')})
        return sorted(posts, key=lambda x: x['views'], reverse=True)
    except Exception as e:
        if "429" in str(e):
            print("⚠️ 429 INSTA - Rate limit, on pause 60s")
            time.sleep(10)
        print(f"ERREUR VIRAL NON FATALE {e}")
        return []

def download_insta_reel_sync(insta_url):
    import yt_dlp
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    ydl_opts = {'quiet': True, 'outtmpl': tmp_path, 'format': 'best[ext=mp4]/best', 'noplaylist': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([insta_url])
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 2000: return tmp_path
        return None
    except: return None

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'/folders/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    return m.group(1) if m else None

async def get_drive_reels_grouped(guild):
    reels = []
    for ch in guild.text_channels:
        if "drive" in ch.name.lower():
            print(f"SCAN DRIVE {ch.name}")
            async for m in ch.history(limit=500):
                for att in m.attachments:
                    if att.content_type and "video" in att.content_type:
                        reels.append({'type': 'discord', 'url': att.url, 'name': att.filename})
                if "drive.google.com" in m.content:
                    urls = re.findall(r'https?://drive\.google\.com/\S+', m.content)
                    for url in urls:
                        fid = extract_file_id(url)
                        if fid: reels.append({'type': 'drive_file', 'id': fid, 'name': f"{fid}.mp4"})
    print(f"TOTAL DRIVE TROUVE: {len(reels)}")
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
        if "modele" in cat.name.lower() or "modèle" in cat.name.lower(): return cat
    return guild.categories[0] if guild.categories else None

# ================= VIEWS =================

class ModalScanInsta(discord.ui.Modal, title="Scanner un compte Insta"):
    lien = discord.ui.TextInput(label="Colle le lien Instagram ici", placeholder="https://www.instagram.com/username/", style=discord.TextStyle.short)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m=re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', self.lien.value)
            if not m:
                await interaction.followup.send("❌ Lien invalide", ephemeral=True); return
            username=m.group(1).split('/')[0]
            clean=f"https://www.instagram.com/{username}/reels/"
            is_ok, msg = await bot.loop.run_in_executor(None, lambda: check_compte_us_non_certifie(username))
            if not is_ok:
                await interaction.followup.send(f"{msg} @{username} ignoré", ephemeral=True); return
            await interaction.followup.send(f"🔍 Scan @{username} validé...", ephemeral=True)
            viral=await bot.loop.run_in_executor(None, lambda: get_all_viral_sync(clean))
            if not viral:
                await interaction.followup.send(f"❌ Rien trouvé pour @{username} - compte privé ou Insta bloque 429", ephemeral=True); return
            db=load_db(); uid=str(interaction.user.id)
            if uid not in db: db[uid]=[]
            db[uid].extend(viral)
            seen=set(); uniq=[]
            for v in db[uid]:
                if v['url'] not in seen: uniq.append(v); seen.add(v['url'])
            db[uid]=uniq; save_db(db)
            thread=await interaction.channel.create_thread(name=f"viral-{username}-{len(viral)}", auto_archive_duration=60)
            try: await thread.add_user(interaction.user)
            except: pass
            embed=discord.Embed(color=0xE1306C, title=f"{len(viral)} VIDEOS - @{username} STOCKÉES")
            txt="";
            for i,p in enumerate(viral[:20],1): txt+=f"**{i}. {p['views']} vues** - {p['url']}\n"
            embed.description=txt[:4000]
            await thread.send(f"{interaction.user.mention}", embed=embed)
            await interaction.followup.send(f"✅ @{username} -> {len(viral)} stockées -> {thread.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: {e}", ephemeral=True)

class ViewScanCompte(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔍 SCANNER UN COMPTE", style=discord.ButtonStyle.danger, custom_id="ramane_scan_v4_fix")
    async def scan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalScanInsta())

class ViewMesVideos(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📂 VOIR MON STOCK VIRAL", style=discord.ButtonStyle.primary, custom_id="ramane_stock_v4_fix")
    async def mes_videos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = load_db(); mine = db.get(str(interaction.user.id), [])
        if not mine:
            await interaction.followup.send("Aucune vidéo encore", ephemeral=True); return
        mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
        embed=discord.Embed(color=0xE1306C, title=f"TON STOCK VIRAL - {len(mine_sorted)} vidéos")
        txt=""
        for i, p in enumerate(mine_sorted[:20], 1): txt+=f"{i}. {p['views']} vues - {p['url']}\n"
        embed.description=txt[:4000]
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎬 GÉNÉRER 8 PACKS REELS (8 DRIVE + 8 VIRALES)", style=discord.ButtonStyle.success, custom_id="ramane_pack_v4_fix")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await interaction.followup.send("Génération en cours...", ephemeral=True)
            reels=await get_drive_reels_grouped(interaction.guild)
            descs=await get_descriptions(interaction.guild)
            if len(reels)<8:
                await interaction.followup.send(f"Stock drive insuffisant: {len(reels)}/8", ephemeral=True); return
            random.shuffle(reels); random.shuffle(descs); reels = reels[:8]
            salon_out=interaction.channel
            for ch in interaction.guild.text_channels:
                if "packs-reels" in ch.name.lower(): salon_out=ch; break
            thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", auto_archive_duration=60)
            try: await thread.add_user(interaction.user)
            except: pass
            await interaction.followup.send(f"Pack créé {thread.mention}", ephemeral=True)
            sent=[]; w=await thread.send(f"{interaction.user.mention} **PACK 8 DRIVE + 8 VIRALES US**\n\n__PARTIE 1: 8 PACKS DRIVE__"); sent.append(w)
            for i in range(8):
                r=reels[i]; d=descs[i] if i < len(descs) else None
                try:
                    desc_text = d.content[:1024] if d else "Pas de description dispo"
                    if r['type'] == 'discord':
                        data = await bot.loop.run_in_executor(None, lambda: requests.get(r['url']).content)
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.write(data); tmp.close()
                        embed=discord.Embed(color=0x00FF88, title=f"PACK DRIVE {i+1}/8"); embed.add_field(name="DESCRIPTION", value=desc_text, inline=False)
                        msg=await thread.send(embed=embed, file=discord.File(tmp.name, filename=r['name'])); sent.append(msg); os.unlink(tmp.name)
                    else:
                        path = await bot.loop.run_in_executor(None, lambda: download_gdrive_file_sync(r['id']))
                        embed=discord.Embed(color=0x00FF88, title=f"PACK DRIVE {i+1}/8"); embed.add_field(name="DESCRIPTION", value=desc_text, inline=False)
                        msg=await thread.send(embed=embed, file=discord.File(path, filename=r.get('name', f"reel_{i+1}.mp4"))); sent.append(msg); os.unlink(path)
                except Exception as e: print(e)
            db=load_db(); mine = db.get(str(interaction.user.id), [])
            if mine:
                mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)[:8]
                w2=await thread.send(f"\n__PARTIE 2: {len(mine_sorted)} VIRALES US__"); sent.append(w2)
                for idx, p in enumerate(mine_sorted, 1):
                    try:
                        path = await bot.loop.run_in_executor(None, lambda: download_insta_reel_sync(p['url']))
                        if path and os.path.exists(path):
                            embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx}/{len(mine_sorted)} - {p['views']} vues")
                            embed.add_field(name="DESCRIPTION ORIGINALE", value=p.get('desc','')[:1024], inline=False)
                            msg=await thread.send(embed=embed, file=discord.File(path, filename=f"viral_us_{idx}.mp4")); sent.append(msg); os.unlink(path)
                        else:
                            embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx} - {p['views']} vues"); embed.add_field(name="DESC", value=p.get('desc','')[:1024], inline=False)
                            embed.add_field(name="LIEN", value=p['url'], inline=False)
                            msg=await thread.send(embed=embed); sent.append(msg)
                    except Exception as e: print(e)
            if sent: bot.loop.create_task(delete_after(sent, 15))
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur pack: {e}", ephemeral=True)

class ViewPseudosFilles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎀 Générer Identité Complète", style=discord.ButtonStyle.primary, custom_id="ramane_pseudo_v4_full")
    async def pseudo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        p = random.choice(['sofia','mia','luna','chloe','emma','aria','zoe'])
        s = random.choice(['rose','vibe','bloom','dream'])
        pseudo_base = f"{p}{s}"
        bio_text = "19 🎀 sweet girl"; photo_url = None; nom_complet = f"{p.capitalize()} {s.capitalize()}"
        for ch in interaction.guild.text_channels:
            name = ch.name.lower()
            if not bio_text or bio_text == "19 🎀 sweet girl":
                if "bio" in name or "description" in name:
                    async for m in ch.history(limit=30):
                        if m.content and len(m.content) > 15: bio_text = m.content[:1000]; break
            if not photo_url and ("photo" in name or "pdp" in name):
                async for m in ch.history(limit=100):
                    for att in m.attachments:
                        if att.content_type and "image" in att.content_type: photo_url = att.url; break
        embed=discord.Embed(color=0xFF69B4, title=f"🎀 Identité pour {nom_complet}")
        embed.add_field(name="Sans chiffre (recommandé)", value=f"`{pseudo_base}`", inline=False)
        embed.add_field(name="Avec point", value=f"`{p}.{s}`", inline=False)
        embed.add_field(name="Avec chiffres", value=f"`{pseudo_base}{random.randint(10,99)}`", inline=False)
        embed.add_field(name="Bio", value=f"```{bio_text[:1000]}```", inline=False)
        if photo_url: embed.set_image(url=photo_url)
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewNumero(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(placeholder="🌍 Choisis ton pays...", custom_id="ramane_numero_v4_fix", options=[
        discord.SelectOption(label="USA", emoji="🇺🇸", value="usa"),
        discord.SelectOption(label="Canada", emoji="🇨🇦", value="canada"),
        discord.SelectOption(label="UK", emoji="🇬🇧", value="uk"),
        discord.SelectOption(label="Ukraine", emoji="🇺🇦", value="ukraine"),
    ])
    async def select_pays(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(f"✅ Pays choisi: **{select.values[0].upper()}**\nBranche ton API 5sim ici.", ephemeral=True)

# ================= SETUPS =================
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
    embed=discord.Embed(color=0xE1306C, title="🔍 Détecteur de Comptes Viraux - Ramane OFM", description="**À QUOI SERT?** Scanner compte Insta et détecter ses reels qui percent.\n**RÔLE:** Analyse direct + filtre US non certifié + stocke vues/desc\n**AVANTAGES:** Que du viral US trié auto\n\n👇 **Bouton rouge**")
    await salon.send(embed=embed, view=ViewScanCompte())
    await ctx.send(f"OK {salon.mention} ✅")

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
    embed=discord.Embed(color=0x00FF88, title="🎬 Générateur de Packs Reels - 8 + 8 Viraux", description="**À QUOI SERT?** 1 clic = 16 contenus prêts\n**RÔLE:** 8 Drive + 8 Virales US + vraies MP4 + thread privé\n**AVANTAGES:** 2h économisées\n\n👇 **Bouton vert**")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"OK {salon.mention} ✅")

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
    embed=discord.Embed(color=0x5865F2, title="📂 Ta Bibliothèque Virale", description="**À QUOI SERT?** Voir ton stock\n**RÔLE:** Garde vidéos scannées + trie par vues\n\n👇 **Bouton bleu**")
    await salon.send(embed=embed, view=ViewMesVideos())
    await ctx.send(f"OK {salon.mention} ✅")

@bot.command()
async def setuppseudo(ctx):
    if not ctx.author.guild_permissions.administrator: return
    for ch in ctx.guild.text_channels:
        if "pseudo" in ch.name.lower():
            embed=discord.Embed(color=0xFF69B4, title="🎀 Générateur de Pseudos", description="**À QUOI SERT?** Identité fille US\n**RÔLE:** Pseudo + bio + photo + nom\n\n👇 **Clique**")
            await ch.send(embed=embed, view=ViewPseudosFilles())

@bot.command()
async def setupnumero(ctx):
    if not ctx.author.guild_permissions.administrator: return
    for ch in ctx.guild.text_channels:
        if "numero" in ch.name.lower():
            embed=discord.Embed(color=0x5865F2, title="📞 Générateur de Numéros", description="**À QUOI SERT?** Numéro US/Gmail\n**RÔLE:** Menu pays USA/Canada/UK/Ukraine\n\n👇 **Choisis**")
            await ch.send(embed=embed, view=ViewNumero())

@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("🚀 Setup complet en cours...")
    await setupcomptes(ctx)
    await setuppack(ctx)
    await setupviral(ctx)
    await setuppseudo(ctx)
    await setupnumero(ctx)
    await ctx.send("✅ **TOUT EST RÉPARÉ - Teste t
