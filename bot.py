from flask import Flask
import threading
import os, discord, requests, random, re, io, time, yt_dlp, tempfile
from discord.ext import commands

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
NOMS_FILLES = ["Sophie","Mia","Emma","Lina","Chloe","Luna","Ava","Sofia","Lily","Nina","Eva","Ruby","Bella","Zoe","Maya","Lea","Jade","Mila","Sara","Elisa","Noa","Lola","Ines","Camille","Julie"]
SUFFIXES = ["rose","dream","love","sweet","babe","doll","angel","honey","bliss","vibe","bloom","glow","petal","charm"]

async def get_bios_from_salon(guild):
    for ch in guild.text_channels:
        if "bio" in ch.name.lower():
            bios=[m.content async for m in ch.history(limit=200) if m.content and len(m.content)>10]
            if bios: return bios
    return ["19 🎀 sweet girl | DM me"]

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
    p=random.choice(NOMS_FILLES).lower(); s=random.choice(SUFFIXES); l=''.join(random.choices("abcdefghijkmnopqrstuvwxyz", k=2))
    return f"{p}{s}{l}", f"{p}.{s}{l}", f"{p}{s}{random.randint(10,99)}{l}"

# --- V3 - ENVOI VIDÉO DIRECTE SANS LIEN ---
def extract_folder_id(url):
    m = re.search(r'/folders/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    return m.group(1) if m else None

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    return extract_folder_id(url)

async def get_drive_reels(guild, limit=1000):
    reels=[]
    for ch in guild.text_channels:
        if "drive" in ch.name.lower():
            async for m in ch.history(limit=limit):
                for att in m.attachments:
                    if att.content_type and "video" in att.content_type:
                        reels.append({'type': 'discord', 'message': m, 'url': att.url, 'name': att.filename})
                if "drive.google.com" in m.content:
                    # on récupère tous les liens drive dans le message
                    urls = re.findall(r'https?://drive\.google\.com/\S+', m.content)
                    for url in urls:
                        fid = extract_file_id(url)
                        if not fid: continue
                        if "/folders/" in url or "folders" in url:
                            # si dossier, on le marque, on ira lister dedans avec l'API si clé dispo
                            reels.append({'type': 'folder', 'id': fid, 'url': url})
                        else:
                            reels.append({'type': 'drive_file', 'id': fid, 'url': url})
    # Si on a des dossiers et une clé API, on liste les vraies vidéos dedans
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from googleapiclient.discovery import build
            service = build('drive', 'v3', developerKey=api_key)
            expanded = []
            for r in reels:
                if r['type'] == 'folder':
                    try:
                        res = service.files().list(q=f"'{r['id']}' in parents and trashed=false", fields="files(id,name,mimeType)", pageSize=100).execute()
                        for f in res.get('files', []):
                            if 'video' in f.get('mimeType','') or f['name'].lower().endswith(('.mp4','.mov','.mkv')):
                                expanded.append({'type': 'drive_file', 'id': f['id'], 'name': f['name']})
                    except: pass
                else:
                    expanded.append(r)
            return expanded
        except: pass
    # Si pas de clé API, on multiplie les dossiers x20 pour débloquer comme avant
    final=[]
    for r in reels:
        if r['type'] == 'folder':
            for _ in range(20): final.append(r)
        else: final.append(r)
    return final

async def get_descriptions(guild, limit=1000):
    descs=[]
    for ch in guild.text_channels:
        if "description" in ch.name.lower():
            async for m in ch.history(limit=limit):
                if m.content and len(m.content.strip())>5 and not m.content.startswith("!"):
                    descs.append(m)
    return descs

def download_gdrive_file(file_id):
    # Téléchargement direct sans lien public
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        for chunk in r.iter_content(1024*1024):
            if chunk: tmp.write(chunk)
    tmp.close()
    return tmp.name
# --- FIN V3 ---

class ViewPseudosFilles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎀 Pseudo", style=discord.ButtonStyle.primary, custom_id="btn_pseudo_fille_final")
    async def pseudo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        ps1,ps2,ps3=generer_pseudo_inutilise()
        bios=await get_bios_from_salon(interaction.guild); photos=await get_photos_from_salon(interaction.guild)
        embed=discord.Embed(color=0xFF69B4, title="🎀 Identité générée")
        embed.add_field(name="👤 RECOMMANDÉ", value=f"`{ps1}`", inline=False)
        embed.add_field(name="📝 Bio", value=f"```{random.choice(bios)[:900]}```", inline=False)
        if photos: embed.set_image(url=random.choice(photos))
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎯 Générer 8 Packs", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final_v3", emoji="🎬")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        reels=await get_drive_reels(interaction.guild)
        descs=await get_descriptions(interaction.guild)
        if len(reels)<8:
            await interaction.followup.send(f"❌ J'ai trouvé {len(reels)} vidéos. Il en faut 8. Mets des fichiers vidéos ou ajoute GOOGLE_API_KEY sur Render.", ephemeral=True)
            return
        if len(descs)<8:
            await interaction.followup.send(f"❌ {len(descs)}/8 descriptions", ephemeral=True)
            return
        random.shuffle(reels); random.shuffle(descs)
        salon_out=discord.utils.get(interaction.guild.text_channels, name="🎯┃packs-reels")
        await interaction.followup.send(f"✅ J'envoie 8 VIDÉOS DIRECTES dans {salon_out.mention} (sans lien) - ça prend 30s", ephemeral=True)
        for i in range(8):
            r=reels[i]; d=descs[i]
            try:
                if r['type'] == 'discord':
                    # Vidéo déjà dans Discord -> on la re-télécharge et re-envoie sans lien
                    data = requests.get(r['url']).content
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tmp.write(data); tmp.close()
                    file_to_send = discord.File(tmp.name, filename=r['name'])
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8")
                    embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    await salon_out.send(embed=embed, file=file_to_send)
                    os.unlink(tmp.name)
                else:
                    # Drive file
                    path = download_gdrive_file(r['id'])
                    name = r.get('name', f"reel_{i+1}.mp4")
                    file_to_send = discord.File(path, filename=name)
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8 - VIDÉO DIRECTE")
                    embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    embed.set_footer(text=f"Pour {interaction.user.name} | Sans lien")
                    await salon_out.send(embed=embed, file=file_to_send)
                    os.unlink(path)
            except Exception as e:
                await salon_out.send(f"❌ Erreur pack {i+1}: {e}")
                print(e)

@bot.event
async def on_ready():
    print(f"✅ {NOM_AGENCE} EN LIGNE")
    bot.add_view(ViewPseudosFilles())
    bot.add_view(ViewPackReels())

@bot.command()
async def setupfilles(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    salon=discord.utils.get(ctx.guild.text_channels, name="🎀┃pseudos-filles") or await ctx.guild.create_text_channel(name="🎀┃pseudos-filles", category=cat)
    embed=discord.Embed(color=0xFF69B4, title="🎀 Générateur d'identités", description="Clique sur 🎀 Pseudo")
    await salon.send(embed=embed, view=ViewPseudosFilles())
    await ctx.send(f"✅ {salon.mention}")

@bot.command()
async def setuppack(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    for ch in list(ctx.guild.text_channels):
        if "packs-reels" in ch.name.lower():
            try: await ch.delete()
            except: pass
    salon=await ctx.guild.create_text_channel(name="🎯┃packs-reels", category=cat)
    embed=discord.Embed(color=0x00FF88, title="🎯 Générateur de PACKS REELS - VIDÉO DIRECTE", description="**Clique et tu reçois :**\n\n🎬 8 VIDÉOS directement uploadées (pas de lien)\n📝 8 DESCRIPTIONS (1 message = 1 desc)")
    embed.set_footer(text=f"{NOM_AGENCE} | Pack Reel System V3")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"✅ Salon configuré: {salon.mention}")

@bot.command()
async def pack(ctx):
    reels=await get_drive_reels(ctx.guild); descs=await get_descriptions(ctx.guild)
    if len(reels)<8 or len(descs)<8:
        await ctx.send(f"❌ Pas assez: {len(reels)}/8 reels, {len(descs)}/8 desc")
        return
    random.shuffle(reels); random.shuffle(descs)
    out=discord.utils.get(ctx.guild.text_channels, name="🎯┃packs-reels")
    for i in range(8):
        r=reels[i]; d=descs[i]
        try:
            if r['type'] == 'discord':
                data = requests.get(r['url']).content
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp.write(data); tmp.close()
                await out.send(content=d.content[:1000], file=discord.File(tmp.name, filename=r['name']))
                os.unlink(tmp.name)
            else:
                path = download_gdrive_file(r['id'])
                await out.send(content=d.content[:1000], file=discord.File(path, filename=r.get('name', f"{i}.mp4")))
                os.unlink(path)
        except Exception as e: print(e)
    await ctx.send(f"✅ 8 packs vidéos envoyés")

def scan_insta_viral(url):
    cookie_file="cookies.txt" if os.path.exists("cookies.txt") else None
    ydl_opts={'quiet': True, 'skip_download': True, 'cookiefile': cookie_file, 'sleep_interval': 3, 'max_sleep_interval': 8, 'retries': 5}
    for _ in range(3):
        try:
            time.sleep(random.uniform(2,4))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info=ydl.extract_info(url, download=False)
                vids=[]
                for e in info.get('entries',[info]):
                    if not e: continue
                    vids.append({'url': e.get('webpage_url') or url, 'views': e.get('view_count',0) or 0})
                return sorted(vids, key=lambda x:x['views'], reverse=True)[:8]
        except: time.sleep(5)
    return []

@bot.command()
async def setupauto(ctx):
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    s1=discord.utils.get(ctx.guild.text_channels, name="📥┃comptes-instagram") or await ctx.guild.create_text_channel(name="📥┃comptes-instagram", category=cat)
    s2=discord.utils.get(ctx.guild.text_channels, name="📤┃videos-recues") or await ctx.guild.create_text_channel(name="📤┃videos-recues", category=cat)
    await ctx.send(f"✅ {s1.mention} -> {s2.mention}")

@bot.event
async def on_message(message):
    if message.author.bot: await bot.process_commands(message); return
    if "instagram.com" in message.content and "comptes" in message.channel.name.lower():
        urls=re.findall(r'https?://(?:www\.)?instagram\.com/\S+', message.content)
        if urls:
            await message.channel.send(f"⏳ Scan {urls[0]}...")
            vids=scan_insta_viral(urls[0])
            rec=discord.utils.get(message.guild.text_channels, name="📤┃videos-recues")
            if vids:
                emb=discord.Embed(color=0x00FF88, title="📤 Pack viral")
                for i,v in enumerate(vids,1): emb.add_field(name=f"{i}. {v['views']} vues", value=v['url'], inline=False)
                await rec.send(embed=emb)
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
