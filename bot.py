from flask import Flask
import threading
import os, discord, requests, random, re, time, tempfile
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE OFM EN LIGNE - OK"
def run_web(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_web, daemon=True).start()

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
    return f"{p}{s}{l}"

def extract_file_id(url):
    m = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'/folders/([a-zA-Z0-9-_]+)', url)
    if m: return m.group(1)
    m = re.search(r'id=([a-zA-Z0-9-_]+)', url)
    return m.group(1) if m else None

async def get_drive_reels(guild):
    reels=[]
    for ch in guild.text_channels:
        if "drive" in ch.name.lower():
            async for m in ch.history(limit=500):
                for att in m.attachments:
                    if att.content_type and "video" in att.content_type:
                        reels.append({'type': 'discord', 'url': att.url, 'name': att.filename})
                if "drive.google.com" in m.content:
                    urls = re.findall(r'https?://drive\.google\.com/\S+', m.content)
                    for url in urls:
                        fid = extract_file_id(url)
                        if fid:
                            if "/folders/" in url: reels.append({'type': 'folder', 'id': fid})
                            else: reels.append({'type': 'drive_file', 'id': fid, 'name': f"{fid}.mp4"})

    # Expand folders avec API KEY
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and any(r['type']=='folder' for r in reels):
        try:
            from googleapiclient.discovery import build
            service = build('drive', 'v3', developerKey=api_key)
            expanded=[]
            for r in reels:
                if r['type'] == 'folder':
                    res = service.files().list(q=f"'{r['id']}' in parents and trashed=false", fields="files(id,name,mimeType)", pageSize=100).execute()
                    for f in res.get('files', []):
                        if 'video' in f.get('mimeType','') or f['name'].lower().endswith(('.mp4','.mov','.m4v')):
                            expanded.append({'type': 'drive_file', 'id': f['id'], 'name': f['name']})
                else: expanded.append(r)
            return expanded
        except Exception as e:
            print(f"Erreur Drive API: {e}")
            return [r for r in reels if r['type']!='folder']
    return reels

async def get_descriptions(guild):
    descs=[]
    for ch in guild.text_channels:
        if "description" in ch.name.lower():
            async for m in ch.history(limit=1000):
                if m.content and len(m.content.strip())>5 and not m.content.startswith("!"): descs.append(m)
    return descs

def download_gdrive_file_sync(file_id):
    # version non-bloquante pour Render
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    session = requests.Session()
    r = session.get(url, stream=True)
    # gestion gros fichier avec token
    for k,v in r.cookies.items():
        if k.startswith('download_warning'):
            url = f"https://drive.google.com/uc?export=download&confirm={v}&id={file_id}"
            r = session.get(url, stream=True)
            break
    for chunk in r.iter_content(1024*1024):
        if chunk: tmp.write(chunk)
    tmp.close()
    return tmp.name

class ViewPseudosFilles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎀 Pseudo", style=discord.ButtonStyle.primary, custom_id="btn_pseudo_fille_final")
    async def pseudo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        ps=generer_pseudo_inutilise()
        bios=await get_bios_from_salon(interaction.guild); photos=await get_photos_from_salon(interaction.guild)
        embed=discord.Embed(color=0xFF69B4, title="🎀 Identité générée")
        embed.add_field(name="👤 Pseudo", value=f"`{ps}`", inline=False)
        embed.add_field(name="📝 Bio", value=f"```{random.choice(bios)[:900]}```", inline=False)
        if photos: embed.set_image(url=random.choice(photos))
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎯 Générer 8 Packs", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final_v3", emoji="🎬")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Je cherche 8 vidéos + 8 descriptions... (10-20s)", ephemeral=True)

        reels=await get_drive_reels(interaction.guild); descs=await get_descriptions(interaction.guild)

        if len(reels)<8 or len(descs)<8:
            await interaction.followup.send(f"❌ Pas assez: {len(reels)}/8 vidéos, {len(descs)}/8 descriptions. Ajoute dans salons #drive et #description", ephemeral=True)
            return

        random.shuffle(reels); random.shuffle(descs)
        salon_out=discord.utils.get(interaction.guild.text_channels, name="🎯┃packs-reels")
        if not salon_out:
            salon_out = interaction.channel

        for i in range(8):
            r=reels[i]; d=descs[i]
            try:
                if r['type'] == 'discord':
                    data = await bot.loop.run_in_executor(None, lambda: requests.get(r['url']).content)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.write(data); tmp.close()
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8")
                    embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    await salon_out.send(embed=embed, file=discord.File(tmp.name, filename=r['name']))
                    os.unlink(tmp.name)
                else:
                    path = await bot.loop.run_in_executor(None, lambda: download_gdrive_file_sync(r['id']))
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8 - VIDÉO DIRECTE")
                    embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    await salon_out.send(embed=embed, file=discord.File(path, filename=r.get('name', f"reel_{i+1}.mp4")))
                    os.unlink(path)
            except Exception as e:
                print(f"Erreur pack {i+1}: {e}")
                await salon_out.send(f"❌ Erreur vidéo {i+1}: {e}\nDesc: {d.content[:500]}")

@bot.event
async def on_ready():
    print(f"✅ {NOM_AGENCE} EN LIGNE - {bot.user}")
    bot.add_view(ViewPseudosFilles()); bot.add_view(ViewPackReels())

@bot.command()
async def setuppack(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    for ch in list(ctx.guild.text_channels):
        if "packs-reels" in ch.name.lower():
            try: await ch.delete()
            except: pass
    salon=await ctx.guild.create_text_channel(name="🎯┃packs-reels", category=cat)
    await salon.send(embed=discord.Embed(color=0x00FF88, title="🎯 PACKS REELS - VIDÉO DIRECTE", description="Clique = 8 vidéos sans lien + 8 desc"), view=ViewPackReels())
    await ctx.send(f"✅ {salon.mention}")

@bot.command()
async def setupfilles(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    salon=discord.utils.get(ctx.guild.text_channels, name="🎀┃pseudos-filles") or await ctx.guild.create_text_channel(name="🎀┃pseudos-filles", category=cat)
    await salon.send(embed=discord.Embed(color=0xFF69B4, title="🎀 Générateur d'identités"), view=ViewPseudosFilles())
    await ctx.send(f"✅ {salon.mention}")

bot.run(os.getenv("DISCORD_TOKEN"))
