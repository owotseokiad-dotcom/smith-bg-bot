from flask import Flask
import threading, os, discord, requests, random, re, tempfile, asyncio
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE OFM EN LIGNE"
def run_web(): app.run(host='0.0.0.0', port=10000)
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
                if fid:
                    if "/folders/" in url: reels.append({'type': 'folder', 'id': fid})
                    else: reels.append({'type': 'drive_file', 'id': fid, 'name': f"{fid}.mp4"})
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
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
        except: pass
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
    for k,v in r.cookies.items():
        if k.startswith('download_warning'):
            url = f"https://drive.google.com/uc?export=download&confirm={v}&id={file_id}"
            r = session.get(url, stream=True)
            break
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
    @discord.ui.button(label="🎀 Générer une Identité", style=discord.ButtonStyle.primary, custom_id="btn_pseudo_fille_final")
    async def pseudo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        ps=generer_pseudo_inutilise()
        bios=await get_bios_from_salon(interaction.guild); photos=await get_photos_from_salon(interaction.guild)
        salon_pack = discord.utils.get(interaction.guild.text_channels, name="🎯┃packs-reels")
        embed=discord.Embed(color=0xFF69B4, title="🎀 Identité Générée - Étape 1/2")
        embed.add_field(name="👤 Pseudo Insta", value=f"`{ps}`", inline=False)
        embed.add_field(name="📝 Bio", value=f"```{random.choice(bios)[:900]}```", inline=False)
        if salon_pack:
            embed.add_field(name="➡️ Étape Suivante", value=f"Identité prête! Va maintenant dans {salon_pack.mention} pour prendre tes 8 Reels.", inline=False)
        if photos: embed.set_image(url=random.choice(photos))
        embed.set_footer(text="Ramane | OFM - Agence Pro")
        view_link = discord.ui.View()
        if salon_pack:
            view_link.add_item(discord.ui.Button(label="🎯 Aller dans Packs Reels", style=discord.ButtonStyle.link, url=salon_pack.jump_url, emoji="🎬"))
        await interaction.followup.send(embed=embed, view=view_link, ephemeral=True)

class ViewPackReels(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎯 Générer 8 Packs Reels", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final_v3", emoji="🎬")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Génération en cours... Je sélectionne 8 vidéos du MÊME modèle...", ephemeral=True)
        reels=await get_drive_reels_grouped(interaction.guild); descs=await get_descriptions(interaction.guild)
        if len(reels)<8 or len(descs)<8:
            await interaction.followup.send(f"❌ Stock insuffisant: {len(reels)}/8 vidéos, {len(descs)}/8 descriptions.", ephemeral=True); return
        random.shuffle(reels); random.shuffle(descs); reels = reels[:8]
        salon_out=discord.utils.get(interaction.guild.text_channels, name="🎯┃packs-reels") or interaction.channel
        try: thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", type=discord.ChannelType.private_thread, auto_archive_duration=60)
        except: thread = await salon_out.create_thread(name=f"pack-{interaction.user.name}-{random.randint(100,999)}", auto_archive_duration=60)
        try: await thread.add_user(interaction.user)
        except: pass
        for member in interaction.guild.members:
            if any(r.name.lower() in ["boss","createur","créateur","owner","manager","team leader","team-leader","admin"] for r in member.roles):
                try: await thread.add_user(member)
                except: pass
        await interaction.followup.send(f"✅ Pack privé créé {thread.mention} - Suppression auto 15 min", ephemeral=True)
        sent=[]; welcome=await thread.send(f"{interaction.user.mention} 🎬 **PACK 8 REELS - MÊME MODÈLE** - ⚠️ Suppression 15 min"); sent.append(welcome)
        for i in range(8):
            r=reels[i]; d=descs[i]
            try:
                if r['type'] == 'discord':
                    data = await bot.loop.run_in_executor(None, lambda: requests.get(r['url']).content)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.write(data); tmp.close()
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8"); embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(tmp.name, filename=r['name'])); sent.append(msg); os.unlink(tmp.name)
                else:
                    path = await bot.loop.run_in_executor(None, lambda: download_gdrive_file_sync(r['id']))
                    embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8"); embed.add_field(name="📝 DESCRIPTION", value=d.content[:1024], inline=False)
                    msg=await thread.send(embed=embed, file=discord.File(path, filename=r.get('name', f"reel_{i+1}.mp4"))); sent.append(msg); os.unlink(path)
            except Exception as e: print(e)
        if sent:
            bot.loop.create_task(delete_after(sent, 15))
            async def delete_thread_after():
                await asyncio.sleep(15*60)
                try: await thread.delete()
                except: pass
            bot.loop.create_task(delete_thread_after())

@bot.event
async def on_ready():
    print(f"✅ {NOM_AGENCE} EN LIGNE")
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
    embed = discord.Embed(
        color=0x00FF88,
        title="🎯 Ramane | OFM - Générateur de Packs Reels",
        description=(
            "**🤖 C'est quoi ce bot?**\n"
            "Génère automatiquement **8 Packs Reels + Descriptions** prêts à poster.\n\n"
            "**⚙️ Comment ça marche?**\n"
            "1️⃣ Clique sur le bouton vert ci-dessous\n"
            "2️⃣ Le bot choisit 1 modèle (1 salon Drive = 1 modèle)\n"
            "3️⃣ Il te sort 8 vidéos DU MÊME MODÈLE + 8 descriptions\n"
            "4️⃣ Thread privé pour toi + Staff uniquement\n\n"
            "**🔒 Confidentialité :** Suppression auto 15 min\n\n"
            "👇 **Clique ci-dessous**"
        )
    )
    embed.set_footer(text="Ramane | OFM Agency - Système Pro")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"✅ {salon.mention}")

@bot.command()
async def setupfilles(ctx):
    if not ctx.author.guild_permissions.administrator: return
    cat=discord.utils.get(ctx.guild.categories, name="🎀 MODELES") or await ctx.guild.create_category("🎀 MODELES")
    salon=discord.utils.get(ctx.guild.text_channels, name="🎀┃pseudos-filles") or await ctx.guild.create_text_channel(name="🎀┃pseudos-filles", category=cat)
    embed = discord.Embed(
        color=0xFF69B4,
        title="🎀 Ramane | OFM - Générateur d'Identités",
        description=(
            "**🤖 C'est quoi ce bot?**\n"
            "Génère un pseudo Insta pro + bio + photo de profil\n\n"
            "**⚙️ Workflow Agence :**\n"
            "1️⃣ Génère ton identité ici\n"
            "2️⃣ Clique sur le bouton pour aller dans Packs Reels\n"
            "3️⃣ Poste ton compte complet\n\n"
            "👇 **Clique ci-dessous**"
        )
    )
    embed.set_footer(text="Ramane | OFM - Étape 1/2")
    await salon.send(embed=embed, view=ViewPseudosFilles())
    await ctx.send(f"✅ {salon.mention}")

@bot.command()
async def setupexplications(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("⏳ Mise en place pro de l'agence en cours...")
    salon_pseudo = discord.utils.get(ctx.guild.text_channels, name="🎀┃pseudos-filles")
    salon_pack = discord.utils.get(ctx.guild.text_channels, name="🎯┃packs-reels")
    lien_pseudo = f"{salon_pseudo.mention}" if salon_pseudo else "`🎀┃pseudos-filles`"
    lien_pack = f"{salon_pack.mention}" if salon_pack else "`🎯┃packs-reels`"
    for ch in ctx.guild.text_channels:
        name = ch.name.lower()
        if "pseudo" in name or "pack-reels" in name: continue
        if "drive" not in name and "bio" not in name and "pdp" not in name and "photo" not in name and "profil" not in name and "description" not in name: continue
        has_human_explained = False
        async for m in ch.history(limit=20):
            if not m.author.bot and len(m.content.strip()) > 20 and "drive.google.com" not in m.content and "http" not in m.content.lower():
                has_human_explained = True; break
        if has_human_explained: continue
        embed=None
        if "drive" in name:
            embed=discord.Embed(color=0x9B59B6, title=f"📁 {ch.name.upper()} - Stock Modèle", description=(f"**🤖 C'est quoi ce salon?**\nStock vidéos d'**UN SEUL modèle**. Toutes les vidéos = même fille.\n\n**⚙️ Comment l'utiliser?**\nToi tu ne postes rien ici. C'est le staff qui alimente.\n\n**🎯 Pour créer ton compte :**\n1️⃣ {lien_pseudo} -> **Pseudo + Bio + PDP**\n2️⃣ {lien_pack} -> **8 Reels + Descriptions** de ce modèle\n\n**⚠️ Règle d'or : 1 salon = 1 modèle**"))
            embed.set_footer(text="Ramane | OFM - Lecture Seule - Agence Pro")
        elif "bio" in name:
            embed=discord.Embed(color=0x3498DB, title="📝 STOCK BIOS", description=f"**🤖 Stock Bios Instagram.**\nEnvoie 1 bio par message.\nUtilisé auto par {lien_pseudo}")
        elif any(x in name for x in ["photo","pdp","profil"]):
            embed=discord.Embed(color=0xE67E22, title="🖼️ STOCK PHOTOS PROFIL", description=f"**🤖 Stock PDP.**\nEnvoie tes photos ici.\nUtilisé auto par {lien_pseudo}")
        elif "description" in name:
            embed=discord.Embed(color=0x2ECC71, title="✍️ STOCK DESCRIPTIONS", description=f"**🤖 Stock Captions Reels.**\n1 description par message.\nUtilisé auto par {lien_pack}")
        if embed:
            try: await ch.send(embed=embed)
            except: pass
            if "drive" in name:
                try:
                    everyone = ctx.guild.default_role
                    overwrite = ch.overwrites_for(everyone)
                    overwrite.send_messages=False; overwrite.add_reactions=False
                    overwrite.create_private_threads=False; overwrite.create_public_threads=False
                    overwrite.send_messages_in_threads=False
                    await ch.set_permissions(everyone, overwrite=overwrite)
                except: pass
            await asyncio.sleep(0.5)
    await ctx.send(f"✅ Agence configurée pro. Drive en lecture seule + explications ajoutées. Workflow : {lien_pseudo} -> {lien_pack}")

@bot.event
async def on_message(message):
    if message.author.bot: await bot.process_commands(message); return
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
