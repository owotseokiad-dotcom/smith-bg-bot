from flask import Flask
import threading
import os, discord, requests, random, re, io, time, yt_dlp
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

async def get_drive_reels(guild, limit=400):
    reels=[]
    for ch in guild.text_channels:
        if "drive" in ch.name.lower():
            async for m in ch.history(limit=limit):
                if m.attachments or "drive.google.com" in m.content or "https://" in m.content:
                    if len(m.content)>5 or m.attachments: reels.append(m)
    return reels

async def get_descriptions(guild, limit=400):
    descs=[]
    for ch in guild.text_channels:
        if "description" in ch.name.lower():
            async for m in ch.history(limit=limit):
                if m.content and len(m.content)>15 and not m.content.startswith("!"): descs.append(m)
    return descs

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
    @discord.ui.button(label="🎯 Générer 8 Packs", style=discord.ButtonStyle.success, custom_id="btn_pack_reels_final", emoji="🎬")
    async def pack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        reels=await get_drive_reels(interaction.guild)
        descs=await get_descriptions(interaction.guild)
        if len(reels)<8:
            await interaction.followup.send(f"❌ Il me faut 8 REELS minimum dans tes salons `drive`. J'en ai trouvé {len(reels)}. Ajoute des liens drive.", ephemeral=True)
            return
        if len(descs)<8:
            await interaction.followup.send(f"❌ Il me faut 8 DESCRIPTIONS minimum dans tes salons `description`. J'en ai trouvé {len(descs)}.", ephemeral=True)
            return
        random.shuffle(reels); random.shuffle(descs)
        salon_out=discord.utils.get(interaction.guild.text_channels, name="🎯┃packs-reels")
        await interaction.followup.send(f"✅ Je génère 8 packs... Regarde dans {salon_out.mention}", ephemeral=True)
        for i in range(8):
            r=reels[i]; d=descs[i]
            reel_txt=r.content
            if r.attachments: reel_txt = r.attachments[0].url + "\n" + reel_txt
            embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8 - REEL + DESC MATCH", description=f"Pour {interaction.user.mention}")
            embed.add_field(name="🎬 REEL (pris dans Drive)", value=reel_txt[:1024] or "Lien drive", inline=False)
            embed.add_field(name="📝 DESCRIPTION QUI VA AVEC", value=d.content[:1024], inline=False)
            embed.set_footer(text=f"Reel: #{r.channel.name} | Desc: #{d.channel.name} | Cliqué par {interaction.user.name}")
            await salon_out.send(embed=embed)

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
    embed=discord.Embed(color=0x00FF88, title="🎯 Générateur de PACKS REELS", description="**Le bot va piocher AUTOMATIQUEMENT :**\n\n🎬 **REELS** -> dans tous les salons qui contiennent `drive`\n📝 **DESCRIPTIONS** -> dans tous les salons qui contiennent `description`\n\n**Clique sur le bouton en bas** et tu reçois instantanément :\n✅ 8 REELS + 8 DESCRIPTIONS qui matchent")
    embed.set_footer(text=f"{NOM_AGENCE} | Pack Reel System")
    await salon.send(embed=embed, view=ViewPackReels())
    await ctx.send(f"✅ Salon configuré: {salon.mention} avec bouton. Clique dessus!")

@bot.command()
async def pack(ctx):
    reels=await get_drive_reels(ctx.guild); descs=await get_descriptions(ctx.guild)
    if len(reels)<8 or len(descs)<8:
        await ctx.send(f"❌ Pas assez de données. Reels: {len(reels)}/8 | Desc: {len(descs)}/8")
        return
    random.shuffle(reels); random.shuffle(descs)
    out=discord.utils.get(ctx.guild.text_channels, name="🎯┃packs-reels")
    for i in range(8):
        r=reels[i]; d=descs[i]
        reel_txt=r.content + (f"\n{r.attachments[0].url}" if r.attachments else "")
        embed=discord.Embed(color=0x00FF88, title=f"PACK {i+1}/8")
        embed.add_field(name="🎬 REEL", value=reel_txt[:1000], inline=False)
        embed.add_field(name="📝 DESCRIPTION", value=d.content[:1000], inline=False)
        await out.send(embed=embed)
    await ctx.send(f"✅ 8 packs envoyés dans {out.mention}")

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
