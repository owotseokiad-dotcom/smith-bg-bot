import discord
from discord.ext import commands
import os
import json
import random
import asyncio

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

# ==================== 1. BOT NUMERO USA (comme ta photo) ====================

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
    embed.add_field(name="📱 Service Instagram USA", value="Bienvenue! Pour obtenir un numéro Instagram :\n\n**1** Cliquez sur 'Prendre un numéro'\n**2** Entrez le numéro sur Instagram et validez.\n**3** Attendez 30 à 60 secondes le SMS.\n**4** Cliquez sur le bouton de vérification.\n\n*Si pas de code, prenez un autre.*", inline=False)
    await ctx.channel.send(embed=embed, view=ViewNumeroUSA())
    await ctx.send(f"✅ Bot USA placé dans {ctx.channel.mention}")

# ==================== 2. BOT PSEUDO FILLES (catégorie Modèle) ====================

NOMS_FILLE_OFM = ["Emma Rose","Sophia Lane","Mia Blake","Ava Summers","Isabella Grey","Luna Ray","Chloe Love","Lily Moore","Zoe Carter","Amelia Hart","Harper Quinn","Aria Sky","Ella Mae","Scarlett Rose","Ruby Jane"]

class ViewPseudoFille(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="✨ Générer un profil complet", style=discord.ButtonStyle.success, custom_id="gen_pseudo_fille_final_v5")
    async def generer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        bio_channel = discord.utils.find(lambda c: "bio" in c.name.lower(), guild.text_channels)
        photo_channel = discord.utils.find(lambda c: ("photo" in c.name.lower() or "pdp" in c.name.lower() or "profil" in c.name.lower()) and "bio" not in c.name.lower() and "numero" not in c.name.lower(), guild.text_channels)

        nom = random.choice(NOMS_FILLE_OFM)
        bio_text = "Ajoute des bios dans ton salon bio"
        if bio_channel:
            try:
                msgs = [m async for m in bio_channel.history(limit=300) if m.content and len(m.content) > 15]
                if msgs: bio_text = random.choice(msgs).content
            except: pass
        photo_url = None
        if photo_channel:
            try:
                msgs = [m async for m in photo_channel.history(limit=300) if m.attachments]
                if msgs: photo_url = random.choice(msgs).attachments[0].url
            except: pass

        embed = discord.Embed(color=0xFF69B4, title=f"🎀 Pack Profil - {nom}")
        embed.add_field(name="👩 Nom complet OFM (sans chiffres)", value=f"`{nom}`", inline=False)
        embed.add_field(name=f"📝 Bio prise dans {bio_channel.mention if bio_channel else '#bio'}", value=bio_text[:1000], inline=False)
        embed.add_field(name=f"🖼️ Photo prise dans {photo_channel.mention if photo_channel else '#photo-de-profil'}", value="Image ci-dessous", inline=False)
        embed.set_footer(text="Message visible que par toi + Boss/Manager/Team Leader - S'efface dans 5 min")
        if photo_url: embed.set_image(url=photo_url)

        await interaction.followup.send(embed=embed, ephemeral=True)

        # Envoi aux boss/manager
        for member in guild.members:
            if any(r.name.lower() in ["boss","manager","team leader","admin"] for r in member.roles) or member.guild_permissions.administrator:
                if member.id!= interaction.user.id:
                    try: await member.send(f"📦 Pack généré par {interaction.user.name} dans #pseudo-filles :", embed=embed)
                    except: pass
        try:
            msg = await interaction.channel.send(f"✅ {interaction.user.mention} a généré un pack - Visible par toi + Boss/Manager/Team Leader. Effacement 5 min.", embed=embed)
            await asyncio.sleep(300)
            await msg.delete()
        except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def setuppseudo(ctx):
    try: await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    except: pass
    embed = discord.Embed(color=0xFF69B4, title="🎀 GÉNÉRATEUR DE PROFILS OFM - RAMANE AGENCY")
    embed.description = "**BIENVENUE DANS LE SALON PSEUDO DE FILLES**\n\nCe bot donne automatiquement:\n**1️⃣ Nom de fille OFM** sans chiffres\n**2️⃣ Bio** prise dans ton salon bio\n**3️⃣ Photo** prise dans ton salon photo de profil\n\n🔒 Résultat visible seulement par toi + Boss + Manager + Team Leader\n🚫 Personne ne peut écrire ici sauf le bot\n👇 **CLIQUE SUR LE BOUTON VERT**"
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
    await ctx.send(f"✅ Numéro {numero} ajouté dans {pays}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setcode(ctx, numero, code):
    db = load_num()
    for pays in db:
        for n in db[pays]:
            if n["number"] == numero:
                n["sms_code"] = code
                save_num(db)
                await ctx.send(f"✅ Code {code} mis pour {numero}")
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
        msg += f"{pays.upper()}: {dispo}/{total} dispo\n"
    await ctx.send(f"📦 STOCK:\n{msg}")

@bot.event
async def on_ready():
    bot.add_view(ViewNumeroUSA())
    bot.add_view(ViewPseudoFille())
    print(f"EN LIGNE RAMANE - {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
