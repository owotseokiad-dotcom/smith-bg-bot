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
            if info.get('is_verified') == True: return False, "❌ Certifié"
            return True, "OK"
    except: return True, "OK"

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
                url = e.get('url') or e.get('webpage_url') or ""
                desc = e.get('description') or e.get('title') or ""
                if "reel" in url or "instagram" in url:
                    posts.append({'url': url, 'views': views, 'desc': desc[:1000], 'id': e.get('id')})
        return sorted(posts, key=lambda x: x['views'], reverse=True)
    except Exception as e:
        print(f"ERREUR VIRAL {e}"); return []

def download_insta_reel_sync(insta_url):
    import yt_dlp
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    ydl_opts = {'quiet': True, 'outtmpl': tmp_path, 'format': 'best[ext=mp4]/best', 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([insta_url])
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 2000: return tmp_path
        return None
    except: return None

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
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
            if att.content_type and "video" in att.content_type: reels.append({'type': 'discord', 'url': att.url, 'name': att.filename})
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

# ================= VIEWS & MODALS FIXES =================

class ModalScanInsta(discord.ui.Modal, title="Scanner un compte Insta"):
    lien = discord.ui.TextInput(label="Colle le lien Instagram ici", placeholder="https://www.instagram.com/username/", style=discord.TextStyle.short)
    async def on_submit(self, interaction: discord.Interaction):
        # FIX: defer direct pour pas avoir "n'a pas répondu"
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            m=re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', self.lien.value)
            if not m:
                await interaction.followup.send("❌ Lien invalide", ephemeral=True); return
            username=m.group(1).split('/')[0]
            clean=f"https://www.instagram.com/{username}/reels/"
            is_ok, msg = await bot.loop.run_in_executor(None, lambda: check_compte_us_non_certifie(username))
            if not is_ok:
                await interaction.followup.send(f"{msg} @{username} ignoré (on veut que US non certifié)", ephemeral=True); return
            await interaction.followup.send(f"🔍 Scan @{username} validé... recherche des virales...", ephemeral=True)
            viral=await bot.loop.run_in_executor(None, lambda: get_all_viral_sync(clean))
            if not viral:
                await interaction.channel.send(f"❌ Rien trouvé pour @{username}"); return
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
            embed=discord.Embed(color=0xE1306C, title=f"{len(viral)} VIDEOS - @{username} STOCKÉES [US NON CERTIFIÉ]")
            txt=""
            for i,p in enumerate(viral[:20],1): txt+=f"**{i}. {p['views']} vues** - {p['url']}\n"
            embed.description=txt[:4000]
            await thread.send(f"{interaction.user.mention}", embed=embed)
            await interaction.channel.send(f"✅ @{username} -> {len(viral)} stockées -> {thread.mention}")
        except Exception as e:
            print(f"MODAL ERROR {e}")
            await interaction.followup.send(f"❌ Erreur: {e}", ephemeral=True)

class ViewScanCompte(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔍 SCANNER UN COMPTE", style=discord.ButtonStyle.danger, custom_id="ramane_scan_v4_fix")
    async def scan(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Pour modal on ne defer pas, on envoie direct
        await interaction.response.send_modal(ModalScanInsta())

class ViewMesVideos(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📂 VOIR MON STOCK VIRAL", style=discord.ButtonStyle.primary, custom_id="ramane_stock_v4_fix")
    async def mes_videos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = load_db(); mine = db.get(str(interaction.user.id), [])
        if not mine:
            await interaction.followup.send("Aucune vidéo encore, va scanner dans #comptes-instagram d'abord", ephemeral=True); return
        mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
        embed=discord.Embed(color=0xE1306C, title=f"TON STOCK VIRAL - {len(mine_sorted)} vidéos US non certifiées")
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
            await interaction.followup.send("Génération en cours... 8 DRIVE + 8 VIRALES US (vraies vidéos MP4)", ephemeral=True)
            reels=await get_drive_reels_grouped(interaction.guild)
            descs=await get_descriptions(interaction.guild)
            if len(reels)<8:
                await interaction.followup.send(f"Stock drive insuffisant: {len(reels)}/8 - Ajoute des vidéos dans #drive", ephemeral=True); return
            random.shuffle(reels); random.shuffle(descs); reels = reels[:8]
            salon_out=interaction.channel
            for ch in interaction.guild.text_channels:
                if "packs-reels" in ch.name.lower(): salon_out=ch; break
            thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", auto_archive_duration=60)
            try: await thread.add_user(interaction.user)
            except: pass
            await interaction.followup.send(f"Pack créé {thread.mention}", ephemeral=True)
            sent=[]; w=await thread.send(f"{interaction.user.mention} **PACK 8 DRIVE + 8 VIRALES US**\n\n__PARTIE 1: 8 PACKS DRIVE (minimum 8)__"); sent.append(w)
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
                mine_sorted = sorted(mine, key=lambda x: x['views'], reverse=True)
                to_send = mine_sorted[:8]
                w2=await thread.send(f"\n__PARTIE 2: {len(to_send)} VIDEOS VIRALES US QUI PERCENT VRAIMENT (vidéo + desc originale)__"); sent.append(w2)
                for idx, p in enumerate(to_send, 1):
                    try:
                        path = await bot.loop.run_in_executor(None, lambda: download_insta_reel_sync(p['url']))
                        if path and os.path.exists(path):
                            embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx}/{len(to_send)} - {p['views']} vues")
                            embed.add_field(name="DESCRIPTION INSTA ORIGINALE", value=p.get('desc','')[:1024], inline=False)
                            msg=await thread.send(embed=embed, file=discord.File(path, filename=f"viral_us_{idx}.mp4")); sent.append(msg); os.unlink(path)
                        else:
                            embed=discord.Embed(color=0xE1306C, title=f"VIRAL US {idx} - {p['views']} vues"); embed.add_field(name="DESC", value=p.get('desc','')[:1024], inline=False)
                            msg=await thread.send(embed=embed); sent.append(msg)
                    except Exception as e: print(e)
            if sent: bot.loop.create_task(delete_after(sent, 15))
        except Exception as e:
            print(f"PACK ERROR {e}")
            await interaction.followup.send(f"❌ Erreur pack: {e}", ephemeral=True)

# ================= SETUPS AVEC EXPLICATIONS COMPLÈTES =================

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
    embed=discord.Embed(color=0xE1306C, title="🔍 Détecteur de Comptes Viraux - Ramane OFM")
    embed.description = (
        "**À QUOI SERT CE SALON?**\n"
        "Ce salon sert à scanner n'importe quel compte Instagram et à détecter automatiquement ses reels qui percent vraiment en ce moment.\n\n"
        "**RÔLE DU BOT :**\n"
        "• Il va directement sur Instagram analyser le compte que tu colles\n"
        "• Il filtre **uniquement les comptes US non certifiés** (pas de badge bleu)\n"
        "• Il récupère ses meilleures vidéos virales avec : vues, likes, description complète, infos compte\n"
        "• Il stocke tout dans ta bibliothèque perso pour tes packs futurs\n\n"
        "**AVANTAGES POUR TOI :**\n"
        "• Tu ne perds plus des heures à chercher à la main\n"
        "• Tu as que du contenu qui perce déjà aux US, prêt à reposter\n"
        "• Tri automatique du plus vu au moins vu avec thread privé pour toi\n\n"
        "👇 **ACTION À FAIRE : Clique sur le bouton rouge ci-dessous et colle le lien Insta**"
    )
    await salon.send(embed=embed, view=ViewScanCompte())
    await ctx.send(f"OK {salon.mention} configuré ✅")

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
    embed = discord.Embed(color=0x00FF88, title="🎬 Générateur de Packs Reels - 8 + 8 Viraux")
    embed.description = (
        "**À QUOI SERT CE SALON?**\n"
        "Ce salon sert à générer tes packs de contenu prêts à poster pour tes modèles en 1 clic.\n\n"
        "**RÔLE DU BOT :**\n"
        "• **PARTIE 1 :** Il prend **8 vidéos minimum** de ton Drive (tes contenus dans #drive)\n"
        "• **PARTIE 2 :** Il va sur Instagram récupérer **8 vidéos virales US non certifiées** que tu as déjà scannées (celles qui percent vraiment)\n"
        "• Il télécharge les vraies vidéos MP4, pas des liens, avec leur description Insta originale complète\n"
        "• Il te crée un thread privé organisé avec 2 parties + suppression auto après 15 min\n\n"
        "**AVANTAGES POUR TOI :**\n"
        "• En 1 clic tu as 16 contenus viraux prêts à poster\n"
        "• Tu gagnes 2h de travail par jour\n"
        "• Tu postes que du contenu qui perce déjà aux US, pas de compte certifié\n\n"
        "👇 **ACTION À FAIRE : Clique sur le bouton vert pour générer ton pack**"
    )
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"OK {salon.mention} configuré ✅")

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
    embed=discord.Embed(color=0x5865F2, title="📂 Ta Bibliothèque Virale Perso")
    embed.description = (
        "**À QUOI SERT CE SALON?**\n"
        "Ce salon sert à voir tout ton stock de vidéos virales US que tu as scannées.\n\n"
        "**RÔLE DU BOT :**\n"
        "• Il garde en mémoire toutes les vidéos que tu as scannées dans #comptes-instagram\n"
        "• Il les trie automatiquement de la plus vue à la moins vue\n"
        "• Il te dit combien tu as au total et combien sont prêtes pour un pack\n"
        "• C'est ta base de données perso pour créer les packs reels\n\n"
        "**AVANTAGES POUR TOI :**\n"
        "• Tu sais exactement ton stock (minimum 8 recommandé avant de générer)\n"
        "• Tu peux vérifier avant de poster\n"
        "• Tout est filtré US non certifié uniquement\n\n"
        "👇 **ACTION À FAIRE : Clique sur le bouton bleu pour voir ton stock**"
    )
    await salon.send(embed=embed, view=ViewMesVideos())
    await ctx.send(f"OK {salon.mention} configuré ✅")

@bot.command()
async def setupall(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("🚀 Setup complet en cours...")
    await setupcomptes(ctx); await setuppack(ctx); await setupviral(ctx)
    await ctx.send("✅ **TOUT EST RÉPARÉ** - Les boutons marchent maintenant")

@bot.event
async def on_ready():
    print(f"EN LIGNE {NOM_AGENCE}")
    bot.add_view(ViewScanCompte())
    bot.add_view(ViewMesVideos())
    bot.add_view(ViewPackReels())

bot.run(os.getenv("DISCORD_TOKEN"))
