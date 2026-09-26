import discord
from discord.ext import commands
import os
import json
import random

# --- CONFIG ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "numeros.json"

def load_num():
    if not os.path.exists(DB_FILE):
        return {"usa": [], "uk": [], "canada": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"usa": [], "uk": [], "canada": []}

def save_num(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==================== 1. BOT NUMERO USA ====================
class ViewNumeroUSA(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Prendre un numéro", style=discord.ButtonStyle.success, emoji="🇺🇸", custom_id="numero_usa_prendre_final")
    async def prendre(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = load_num()
        dispo = [n for n in db.get("usa", []) if not n.get("used")]
        if not dispo:
            await interaction.followup.send("❌ Plus de numéro USA dispo. Tag le boss pour recharger.", ephemeral=True)
            return
        choisi = dispo[0]
        choisi["used"] = True
        choisi["claimed_by"] = interaction.user.name
        save_num(db)
        embed = discord.Embed(color=0xFFFFFF, title="✅ Numéro trouvé!")
        embed.add_field(name="📞 Numéro :", value=f"`{choisi['number']}`", inline=False)
        embed.add_field(name="Instructions :", value="1. Copie sur Instagram\n2. Attends 30-60s\n3. Clique sur Lire le code", inline=False)
        class ViewCode(discord.ui.View):
            def __init__(self, obj):
                super().__init__(timeout=None)
                self.obj = obj
            @discord.ui.button(label="Lire le code Instagram", style=discord.ButtonStyle.primary, emoji="✉️", custom_id="lire_code_final")
            async def lire(self, inter, btn):
                await inter.response.defer(ephemeral=True)
                code = self.obj.get("sms_code")
                if not code:
                    await inter.followup.send("⏳ SMS pas encore arrivé. Attends 30s et reclique.", ephemeral=True)
                else:
                    await inter.followup.send(f"✅ Ton code: `{code}`", ephemeral=True)
        await interaction.followup.send(embed=embed, view=ViewCode(choisi), ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setupusa(ctx):
    embed = discord.Embed(color=0x5865F2)
    embed.set_author(name="NUMERO US APP", icon_url="https://flagcdn.com/w40/us.png")
    embed.add_field(name="📱 Service Instagram USA", value="Bienvenue! Pour obtenir un numéro Instagram :\n\n**1** Cliquez sur 'Prendre un numéro'\n**2** Entrez le numéro sur Instagram et validez.\n**3** Attendez 30 à 60 secondes le SMS.\n**4** Cliquez sur le bouton de vérification.", inline=False)
    await ctx.channel.send(embed=embed, view=ViewNumeroUSA())

# ==================== 2. BOT PSEUDO FILLES - VARIE VRAIMENT ====================
NOMS_FILLE_OFM = ["Emma Rose","Sophia Lane","Mia Blake","Ava Summers","Isabella Grey","Luna Ray","Chloe Love","Lily Moore","Zoe Carter","Amelia Hart","Harper Quinn","Aria Sky","Ella Mae","Scarlett Rose","Ruby Jane","Mila Grace","Nora Bloom","Avery Reed","Layla Fox","Hazel Moon"]

class ViewPseudoFille(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✨ Générer un profil complet", style=discord.ButtonStyle.success, custom_id="gen_pseudo_fille_v8_random_all")
    async def generer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        # Trouve TOUS les salons bio et photo
        bio_channels = [c for c in guild.text_channels if "bio" in c.name.lower()]
        photo_channels = [c for c in guild.text_channels if ("photo" in c.name.lower() or "pdp" in c.name.lower() or "profil" in c.name.lower()) and "bio" not in c.name.lower() and "numero" not in c.name.lower()]

        # Récupère toutes les bios
        all_bios = []
        for ch in bio_channels:
            try:
                async for m in ch.history(limit=1000):
                    if m.content and 20 < len(m.content) < 1200 and not m.content.startswith("!"):
                        all_bios.append(m.content)
            except: pass

        # Récupère toutes les photos
        all_photos = []
        for ch in photo_channels:
            try:
                async for m in ch.history(limit=1000):
                    for att in m.attachments:
                        if att.filename.lower().endswith((".png",".jpg",".jpeg",".webp")):
                            all_photos.append(att.url)
            except: pass

        # VARIATION - Mélange à chaque fois
        if all_bios:
            random.shuffle(all_bios)
            bio_text = random.choice(all_bios)
        else:
            bio_text = "❌ Aucune bio trouvée, ajoute des bios dans tes salons bio"

        photo_url = random.choice(all_photos) if all_photos else None
        if all_photos:
            random.shuffle(all_photos)
            photo_url = random.choice(all_photos)

        nom = random.choice(NOMS_FILLE_OFM)

        embed = discord.Embed(color=0xFF69B4, title=f"🎀 Pack Profil - {nom}")
        embed.add_field(name="👩 Nom complet OFM", value=f"`{nom}`", inline=False)
        embed.add_field(name="📝 Bio aléatoire", value=bio_text[:1000], inline=False)
        if photo_url:
            embed.set_image(url=photo_url)
            embed.add_field(name="🖼️ Photo aléatoire", value=f"{len(all_photos)} photos trouvées - choix aléatoire", inline=False)
        else:
            embed.add_field(name="🖼️ Photo", value=f"❌ Aucune photo trouvée ({len(photo_channels)} salons scannés)", inline=False)

        # Envoi - RESTE POUR TOUJOURS, PAS DE SUPPRESSION
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Envoi au boss/manager
        for member in guild.members:
            if any(r.name.lower() in ["boss","manager","team leader"] for r in member.roles) or member.guild_permissions.administrator:
                if member.id!= interaction.user.id:
                    try:
                        await member.send(f"📦 Pack généré par {interaction.user.name}:", embed=embed)
                    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def setuppseudo(ctx):
    try: await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    except: pass
    embed = discord.Embed(color=0xFF69B4, title="🎀 GÉNÉRATEUR DE PROFILS OFM - RAMANE AGENCY")
    embed.description = "**BIENVENUE**\n\nCe bot donne:\n**1️⃣ Nom de fille OFM**\n**2️⃣ Bio** prise au HASARD dans tous tes salons bio\n**3️⃣ Photo** prise au HASARD dans tous tes salons photo\n\n🔒 Visible seulement par toi + Boss/Manager\n👇 **CLIQUE**"
    await ctx.channel.send(embed=embed, view=ViewPseudoFille())

# ==================== COMMANDES STOCK ====================
@bot.command()
@commands.has_permissions(administrator=True)
async def addnumero(ctx, pays, numero):
    db = load_num()
    pays = pays.lower()
    if pays not in db: db[pays] = []
    db[pays].append({"number": numero, "used": False, "sms_code": None})
    save_num(db)
    await ctx.send(f"✅ {numero} ajouté dans {pays}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setcode(ctx, numero, code):
    db = load_num()
    for pays in db:
        for n in db[pays]:
            if n["number"] == numero:
                n["sms_code"] = code
                save_num(db)
                await ctx.send(f"✅ Code {code} pour {numero}")
                return
    await ctx.send("Numéro non trouvé")

@bot.command()
@commands.has_permissions(administrator=True)
async def stock(ctx):
    db = load_num()
    msg = ""
    for pays in db:
        dispo = len([x for x in db[pays] if not x.get("used")])
        total = len(db[pays])
        msg += f"{pays.upper()}: {dispo}/{total}\n"
    await ctx.send(f"📦 STOCK:\n{msg}")

@bot.event
async def on_ready():
    bot.add_view(ViewNumeroUSA())
    bot.add_view(ViewPseudoFille())
    print(f"EN LIGNE RAMANE - {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
