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
NOMS_FILLES = ["Sophie","Mia","Emma","Lina","Chloe","Luna","Ava","Sofia","Lily","Nina","Eva","Ruby","Bella","Zoe","Maya","Lea","Jade","Mila","Sara","Elisa","Noa","Lola","Ines","Camille","Julie"]
SUFFIXES = ["rose","dream","love","sweet","babe","doll","angel","honey","bliss","vibe","bloom","glow","petal","charm"]

async def get_bios_from_salon(guild):
    for ch in guild.text_channels:
        if "bio" in ch.name.lower():
            bios=[m.content async for m in ch.history(limit=200) if m.content and len(m.content)>10]
            if bios: return bios
    return ["19 sweet girl | DM me"]

async def get_photos_from_salon(guild):
    for ch in guild.text_channels:
        n=ch.name.lower()
        if ("photo" in n or "pdp" in n or "profil" in n) and "pseudo" not in n:
            photos=[]
            async for m in ch.history(limit=200):
                for att in m.attachments:
                    if att.content_type and "image" in att.content_type: photos.append(att.url)
            if photos: return photos
    return []

def generer_pseudo_inutilise():
    p=random.choice(NOMS_FILLES).lower()
    s=random.choice(SUFFIXES)
    l=''.join(random.choices("abcdefghijkmnopqrstuvwxyz", k=2))
    return f"{p}{s}{l}"

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
            urls = re.findall(r'https?://drive.google.com/\S+', m.content)
            for url in urls:
                fid = extract_file_id(url)
                if fid:
                    if "/folders/" in url: reels.append({'type': 'folder', 'id': fid})
                    else: reels.append({'type': 'drive_file', 'id': fid, 'name': f"{fid}.mp4"})
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

class ViewPseudosFilles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Generer une Identite", style=discord.ButtonStyle.primary, custom_id="btn_pseudo_fille_final")
    async def pseudo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        ps=generer_pseudo_inutilise()
        bios=await get_bios_from_salon(interaction.guild)
        photos=await get_photos_from_salon(interaction.guild)
        embed=discord.Embed(color=0xFF69B4, title="Identite Fille Generee")
        embed.add_field(name="Pseudo Insta", value=f"`{ps}`", inline=False)
        embed.add_field(name="Bio", value=f"{random.choice(bios)[:900]}", inline=False)
        if photos: embed.set_image(url=random.choice(photos))
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Generer 8 Packs Reels", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final_v3")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Recherche en cours...", ephemeral=True)
        reels=await get_drive_reels_grouped(interaction.guild)
        descs=await get_descriptions(interaction.guild)
        if len(reels)<8 or len(descs)<8:
            await interaction.followup.send(f"Stock insuffisant: {len(reels)}/8 videos, {len(descs)}/8 descriptions.", ephemeral=True); return
        random.shuffle(reels); random.shuffle(descs)
        reels = reels[:8]
        salon_out=None
        for ch in interaction.guild.text_channels:
            if "packs-reels" in ch.name.lower(): salon_out=ch; break
        if not salon_out: salon_out=interaction.channel
        thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", auto_archive_duration=60)
        try: await thread.add_user(interaction.user)
        except: pass
        await interaction.followup.send(f"Pack prive cree {thread.mention}", ephemeral=True)
        sent=[]
        w=await thread.send(f"{interaction.user.mention} PACK 8 REELS"); sent.append(w)
        for i in range(8):
            r=reels[i]; d=descs[i]
            try:
                if r['type'] == 'discord':
                    data = await bot.loop.run_in_executor(None, lambda: requests.get(r['url']).content)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.write(data); tmp.close()
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8")
                    embed.add_field(name="DESCRIPTION", value=d.content[:1024], inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(tmp.name, filename=r['name'])); sent.append(msg); os.unlink(tmp.name)
                else:
                    path = await bot.loop.run_in_executor(None, lambda: download_gdrive_file_sync(r['id']))
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8")
                    embed.add_field(name="DESCRIPTION", value=d.content[:1024], inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(path, filename=r.get('name', f"reel_{i+1}.mp4"))); sent.append(msg); os.unlink(path)
            except Exception as e: print(e)
        if sent:
            bot.loop.create_task(delete_after(sent, 15))

@bot.command()
async def setuppack(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="MODELES") or await ctx.guild.create_category("MODELES")
    for ch in list(ctx.guild.text_channels):
        if "packs-reels" in ch.name.lower():
            try: await ch.delete()
            except: pass
    salon=await ctx.guild.create_text_channel(name="packs-reels", category=cat)
    embed = discord.Embed(color=0x00FF88, title="Ramane | OFM - Generateur de Packs Reels", description="Clique ci-dessous pour generer 8 packs")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"OK {salon.mention}")

@bot.command()
async def setupfilles(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="MODELES") or await ctx.guild.create_category("MODELES")
    salon=None
    for ch in ctx.guild.text_channels:
        if "pseudos-filles" in ch.name.lower(): salon=ch; break
    if not salon:
        salon=await ctx.guild.create_text_channel(name="pseudos-filles", category=cat)
    embed = discord.Embed(color=0xFF69B4, title="Ramane | OFM - Generateur d'Identites")
    await salon.send(embed=embed, view=ViewPseudosFilles())
    await ctx.send(f"OK {salon.mention}")

DB_FILE = "viral_db.json"
def load_db():
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}
def save_db(d):
    with open(DB_FILE, "w") as f: json.dump(d, f)

def get_all_viral_sync(insta_url):
    import yt_dlp
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    posts=[]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(insta_url, download=False)
            for e in (info.get('entries', []) or []):
                views = e.get('view_count',0) or 0
                posts.append({'url': e.get('url') or f"https://www.instagram.com/reel/{e.get('id')}/", 'views': views, 'desc': (e.get('description') or "")[:100]})
        posts = sorted(posts, key=lambda x: x['views'], reverse=True)
        return posts[:30]
    except Exception as e:
        print(e); return []

class ViewMesVideos(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="MES VIDEOS VIRALES", style=discord.ButtonStyle.primary, custom_id="btn_mes_videos")
    async def mes_videos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        db = load_db()
        mine = db.get(str(interaction.user.id), [])
        if not mine:
            await interaction.followup.send("Aucune video encore", ephemeral=True); return
        embed=discord.Embed(color=0xE1306C, title=f"TES VIDEOS VIRALES - {len(mine)}")
        txt=""
        for i, p in enumerate(mine[::-1][:20], 1):
            txt+=f"{i}. {p['views']} vues - {p['url']}\n"
        embed.description=txt[:4000]
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.command()
async def setupcomptes(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="MODELES") or await ctx.guild.create_category("MODELES")
    salon=None
    for ch in ctx.guild.text_channels:
        if "comptes-instagram" in ch.name.lower(): salon=ch; break
    if not salon:
        salon=await ctx.guild.create_text_channel(name="comptes-instagram", category=cat)
    embed=discord.Embed(color=0xE1306C, title="Ramane | OFM - Detecteur de Comptes Viraux", description="Colle un lien Insta ici")
    await salon.send(embed=embed)
    await ctx.send(f"OK {salon.mention}")

@bot.command()
async def setupviral(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="MODELES") or await ctx.guild.create_category("MODELES")
    for ch in list(ctx.guild.text_channels):
        if "mes-videos-virales" in ch.name.lower():
            try: await ch.delete()
            except: pass
    salon=await ctx.guild.create_text_channel(name="mes-videos-virales", category=cat)
    embed=discord.Embed(color=0xE1306C, title="Ton Stock Viral Perso")
    await salon.send(embed=embed, view=ViewMesVideos())
    await ctx.send(f"OK {salon.mention}")

@bot.event
async def on_ready():
    print(f"EN LIGNE {NOM_AGENCE}")
    bot.add_view(ViewPseudosFilles())
    bot.add_view(ViewPackReels())
    bot.add_view(ViewMesVideos())

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    if "comptes-instagram" in message.channel.name.lower() and "instagram.com" in message.content.lower():
        m=re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)', message.content)
        if m:
            username=m.group(1).split('/')[0]
            clean=f"https://www.instagram.com/{username}/reels/"
            await message.channel.send(f"Scan @{username} en cours...")
            viral=await bot.loop.run_in_executor(None, lambda: get_all_viral_sync(clean))
            if not viral:
                await message.channel.send(f"Rien trouve pour @{username}")
            else:
                db=load_db()
                uid=str(message.author.id)
                if uid not in db: db[uid]=[]
                db[uid].extend(viral)
                save_db(db)
                try:
                    thread=await message.channel.create_thread(name=f"viral-{username}-{len(viral)}", auto_archive_duration=60)
                    await thread.add_user(message.author)
                    embed=discord.Embed(color=0xE1306C, title=f"{len(viral)} VIDEOS - @{username}")
                    txt=""
                    for i,p in enumerate(viral,1):
                        txt+=f"{i}. {p['views']} vues - {p['url']}\n"
                    embed.description=txt[:4000]
                    await thread.send(f"{message.author.mention}", embed=embed)
                    await message.channel.send(f"OK @{username} -> {len(viral)} videos -> {thread.mention}")
                except Exception as e:
                    await message.channel.send(f"Erreur {e}")
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
