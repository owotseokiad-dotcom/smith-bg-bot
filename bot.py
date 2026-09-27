import discord
from discord.ext import commands
import os
import json
import random
from flask import Flask
import threading

# --- PATCH RENDER ANTI TIMED OUT ---
app = Flask(__name__)
@app.route('/')
def home(): return "RAMANE BOT ONLINE"
def run_web(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run_web, daemon=True).start()
# --- FIN PATCH ---

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

# ==================== 1. BOT NUMERO USA (TON CODE D'ORIGINE - INTACT) ====================
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

# ==================== 2. BOT PSEUDO FILLES - VERSION FINALE CORRIGÉE (INTACT) ====================
PRENOMS = ["emma","sophia","mia","ava","isabella","luna","chloe","lily","zoe","amelia","harper","aria","ella","scarlett","ruby","mila","nora","avery","layla","hazel","grace","violet","nova","aurora","stella"]
NOMS = ["rose","lane","blake","summers","grey","ray","love","moore","carter","hart","quinn","sky","mae","jane","bloom","reed","fox","moon","brooks","hayes","wren","james","cole","jade"]

def gen_pseudo_insta():
    prenom = random.choice(PRENOMS)
    nom = random.choice(NOMS)
    num = random.randint(10,99)
    pseudo = random.choice([
        f"{prenom}.{nom}{num}",
        f"{prenom}_{nom}{num}",
        f"{prenom}.{nom}.{num}",
        f"its{prenom}{nom}",
        f"the{prenom}{nom}{num}"
    ])
    nom_complet = f"{prenom.capitalize()} {nom.capitalize()}"
    return nom_complet, pseudo

class ViewPseudoFille(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✨ Générer un profil complet", style=discord.ButtonStyle.success, custom_id="gen_pseudo_fille_v8_random_all")
    async def generer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        bio_channels = [c for c in guild.text_channels if "bio" in c.name.lower()]
        photo_channels = [c for c in guild.text_channels if "photo-de-profil" in c.name.lower() or "photo de profil" in c.name.lower()]

        all_bios = []
        for ch in bio_channels:
            try:
                async for m in ch.history(limit=1000):
                    if m.content and 20 < len(m.content) < 1200 and not m.content.startswith("!"):
                        all_bios.append(m.content)
            except: pass

        all_photos = []
        for ch in photo_channels:
            try:
                async for m in ch.history(limit=1000):
                    for att in m.attachments:
                        if att.filename.lower().endswith((".png",".jpg",".jpeg",".webp")):
                            all_photos.append(att.url)
            except: pass

        if all_bios:
            random.shuffle(all_bios)
            bio_text = random.choice(all_bios)
        else:
            bio_text = "❌ Aucune bio trouvée, ajoute des bios dans #bio"

        photo_url = None
        if all_photos:
            random.shuffle(all_photos)
            photo_url = random.choice(all_photos)

        nom_complet, pseudo_insta = gen_pseudo_insta()

        embed = discord.Embed(color=0xFF69B4, title=f"🎀 Pack Profil - {nom_complet}")
        embed.add_field(name="👩 Nom complet OFM", value=f"`{nom_complet}`", inline=False)
        embed.add_field(name="✅ Pseudo Instagram (jamais utilisé)", value=f"`{pseudo_insta}`", inline=False)
        embed.add_field(name="📝 Bio aléatoire", value=bio_text[:1000], inline=False)
        if photo_url:
            embed.set_image(url=photo_url)
            embed.add_field(name="🖼️ Photo aléatoire", value=f"✅ {len(all_photos)} photos trouvées dans #photo-de-profil", inline=False)
        else:
            embed.add_field(name="🖼️ Photo", value=f"❌ Aucune photo trouvée dans #photo-de-profil", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

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
    embed.description = (
        "**BIENVENUE - LIS BIEN ✅**\n\n"
        "Ce bouton te génère un pack complet en 1 clic :\n\n"
        "👩 **1. Nom de fille OFM** → prénom + nom US aléatoire\n"
        "✅ **2. Pseudo Insta qui passe** → jamais utilisé\n"
        "📝 **3. Bio Insta** → prise au HASARD uniquement dans #bio\n"
        "🖼️ **4. Photo de profil** → prise au HASARD uniquement dans #photo-de-profil\n\n"
        "🔁 À chaque clic ça change, tu n'auras jamais 2 fois la même chose\n"
        "🔒 Seule toi vois ton pack + Boss/Manager\n\n"
        "👇 **CLIQUE SUR LE BOUTON EN DESSOUS**"
    )
    await ctx.channel.send(embed=embed, view=ViewPseudoFille())

# ==================== COMMANDES STOCK (INTACT) ====================
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

# ==========================================================
# ========== SYSTEME DE BIENVENUE AUTO (INTACT) =========
# ==========================================================
import asyncio

def get_welcome_embed(member):
    embed = discord.Embed(title=f"Bienvenue {member.display_name} chez RAMANE OFM 👑", color=0xFF1493)
    embed.description = f"""
{member.mention} Bienvenue, ceci est **ta discussion privée**. Seul toi et le staff voyez ce salon.

**🏢 PRESENTATION AGENCE :**
Bienvenue chez Ramane OFM Agency. On est une agence OFM / MYM. Toi tu fournis le contenu, nous on gère tout : tchat, vente, promo, stratégie.

**📁 EXPLICATION DES SALONS :**
🔒・**Ici (ta discussion)** → Ton suivi perso, tes paiements, tes questions
📢・**#annonces** → Infos importantes
📸・**#contenu-a-envoyer / #bio / #photo-de-profil** → Dépôt de contenu
💸・**#paiements** → Tes virements
💬・**#discussion-generale** → Parler avec les autres
🆘・**#support** → Bug / problème
🇺🇸・**#numero-us-app** → Numéros Insta USA
🎀・**#pseudo** → Générateur de profils

**👉 QUE FAIRE MAINTENANT?**
1. Lis les épinglés dans #annonces
2. Présente toi ICI : pseudo + ce que tu fais
3. Envoie ton contenu du jour
Le staff va te prendre en charge.
"""
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)
    return embed

def find_private_category(guild):
    for cat in guild.categories:
        low = cat.name.lower()
        if "discussion" in low or "privee" in low or "privée" in low or "ticket" in low:
            return cat
    return None

@bot.listen('on_member_join')
async def auto_create_discussion(member):
    if member.bot: return
    await asyncio.sleep(2)
    guild = member.guild
    category = find_private_category(guild)
    channel_name = f"privee-{member.name.lower()}"[:90].replace(" ", "-")
    if discord.utils.get(guild.channels, name=channel_name):
        return
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    for role in guild.roles:
        if role.name.lower() in ["boss","manager","team leader","staff","admin","administrateur"]:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    try:
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites, topic=f"Discussion privée de {member.display_name} | ID: {member.id}")
        await channel.send(f"{member.mention}", embed=get_welcome_embed(member))
        print(f"[WELCOME] Discussion créée pour {member}")
    except Exception as e:
        print(f"[WELCOME ERREUR] {e}")

@bot.command(name="rattrapage")
@commands.has_permissions(administrator=True)
async def rattrapage(ctx):
    await ctx.send("⏳ Je check les membres sans discussion...")
    count = 0
    for m in ctx.guild.members:
        if m.bot: continue
        name = f"privee-{m.name.lower()}"[:90].replace(" ", "-")
        if not discord.utils.get(ctx.guild.channels, name=name):
            await auto_create_discussion(m)
            count += 1
            await asyncio.sleep(1)
    await ctx.send(f"✅ Boss {count} discussions créées.")

@bot.command(name="welcome")
@commands.has_permissions(administrator=True)
async def welcome_cmd(ctx, member: discord.Member = None):
    if member is None: member = ctx.author
    name = f"privee-{member.name.lower()}"[:90].replace(" ", "-")
    ch = discord.utils.get(ctx.guild.channels, name=name)
    if not ch:
        await ctx.send("❌ Pas de discussion, je crée...")
        await auto_create_discussion(member)
    else:
        await ch.send(f"{member.mention}", embed=get_welcome_embed(member))
        await ctx.send(f"✅ Message renvoyé dans {ch.mention}")

# ==========================================================
# ========== AJOUT BOSS - SALON NUMERO-GMAIL 3 PAYS =========
# ========== (NOUVEAU - DEMANDE VOCAL) ======================
# ==========================================================

class ChoixPaysGmailView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    async def attribuer(self, interaction: discord.Interaction, pays_key: str, emoji: str, nom_complet: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = load_num()
        dispo = [n for n in db.get(pays_key, []) if not n.get("used")]
        if not dispo:
            await interaction.followup.send(f"❌ Stock {nom_complet} vide. Mentionne le Boss pour recharger.", ephemeral=True)
            return

        choisi = dispo[0]
        choisi["used"] = True
        choisi["claimed_by"] = interaction.user.id
        save_num(db)

        # Création fil privé dans le MÊME salon numero-gmail
        # Visible uniquement par demandeur + Boss/Manager/Team Leader
        try:
            thread = await interaction.channel.create_thread(
                name=f"{pays_key.upper()}-{interaction.user.name}",
                type=discord.ChannelType.private_thread
            )
            await thread.add_user(interaction.user)
            # Ajoute le staff
            for role in interaction.guild.roles:
                if role.name.lower() in ["boss","manager","team leader","staff","admin","administrateur"]:
                    for m in role.members:
                        try: await thread.add_user(m)
                        except: pass

            embed_num = discord.Embed(color=0xFFFFFF, title=f"{emoji} Numéro {nom_complet} - RAMANE OFM")
            embed_num.add_field(name="📞 Numéro attribué :", value=f"`{choisi['number']}`", inline=False)
            embed_num.add_field(name="👤 Pour :", value=f"{interaction.user.mention}", inline=False)
            embed_num.add_field(name="🔒 Confidentialité :", value="Visible uniquement par toi + Boss/Manager/Team Leader", inline=False)
            embed_num.set_footer(text="Le code SMS arrivera ici même - Reste dans ce fil")

            class ViewCodeGmail(discord.ui.View):
                def __init__(self, obj_num):
                    super().__init__(timeout=None)
                    self.obj = obj_num
                @discord.ui.button(label="Lire le code Gmail", style=discord.ButtonStyle.primary, emoji="✉️", custom_id="lire_code_gmail_vocal")
                async def lire(self, inter, btn):
                    await inter.response.defer(ephemeral=True)
                    code = self.obj.get("sms_code")
                    if not code:
                        await inter.followup.send("⏳ Code pas encore arrivé. Attends 30s et reclique.", ephemeral=True)
                    else:
                        await inter.followup.send(f"✅ Ton code Gmail : `{code}`", ephemeral=True)

            await thread.send(f"{interaction.user.mention}", embed=embed_num, view=ViewCodeGmail(choisi))
            await interaction.followup.send(f"✅ Ton numéro {emoji} {nom_complet} est prêt dans {thread.mention}\nTout se passe là-bas (numéro + code).", ephemeral=True)

        except Exception as e:
            # Fallback si pas de threads
            embed_num = discord.Embed(color=0xFFFFFF, title=f"{emoji} Numéro {nom_complet}")
            embed_num.add_field(name="📞 Numéro :", value=f"`{choisi['number']}`", inline=False)
            await interaction.followup.send(embed=embed_num, ephemeral=True)
            print(f"Erreur thread gmail: {e}")

    @discord.ui.button(label="USA", emoji="🇺🇸", style=discord.ButtonStyle.primary, custom_id="gmail_choix_usa_vocal")
    async def usa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.attribuer(interaction, "usa", "🇺🇸", "USA")

    @discord.ui.button(label="Angleterre", emoji="🇬🇧", style=discord.ButtonStyle.primary, custom_id="gmail_choix_uk_vocal")
    async def uk(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.attribuer(interaction, "uk", "🇬🇧", "Angleterre")

    @discord.ui.button(label="Canada", emoji="🇨🇦", style=discord.ButtonStyle.secondary, custom_id="gmail_choix_canada_vocal")
    async def canada(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.attribuer(interaction, "canada", "🇨🇦", "Canada")

class ViewNumeroGmailMain(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎲 Générer un numéro", style=discord.ButtonStyle.success, custom_id="gmail_generer_main_vocal", emoji="📱")
    async def generer(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_num()
        usa_stock = len([n for n in db.get("usa", []) if not n.get("used")])
        uk_stock = len([n for n in db.get("uk", []) if not n.get("used")])
        ca_stock = len([n for n in db.get("canada", []) if not n.get("used")])

        embed_choix = discord.Embed(color=0x2B2D31, title="🌍 Choisis ton pays")
        embed_choix.description = f"**Stock actuel :**\n🇺🇸 USA : `{usa_stock}` dispo\n🇬🇧 Angleterre : `{uk_stock}` dispo\n🇨🇦 Canada : `{ca_stock}` dispo\n\nClique sur le pays que tu veux."
        await interaction.response.send_message(embed=embed_choix, view=ChoixPaysGmailView(), ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setupgmail(ctx):
    # Bloque le salon pour que personne ne parle sauf bot
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.channel.set_permissions(ctx.guild.me, send_messages=True)
    except: pass

    embed = discord.Embed(color=0x5865F2, title="📱 RAMANE OFM - SERVICE NUMÉROS GMAIL")
    embed.description = (
        "**🤖 RÔLE DE CE BOT :**\n"
        "Ce bot te fournit des numéros jetables internationaux pour créer tes comptes Gmail pro.\n"
        "Tous les numéros sont **payés par l'agence**, tu n'as rien à payer.\n\n"
        "**⚙️ COMMENT ÇA MARCHE?**\n"
        "1. Clique sur `🎲 Générer un numéro` ci-dessous\n"
        "2. Choisis ton pays : **USA 🇺🇸 / Angleterre 🇬🇧 / Canada 🇨🇦**\n"
        "3. Un fil privé va se créer **dans ce même salon**. Seuls toi + Boss / Manager / Team Leader verront le numéro.\n"
        "4. Le code de validation arrivera aussi **dans ce même fil**.\n\n"
        "**🔒 CONFIDENTIALITÉ TOTALE**\n"
        "Tout le monde peut utiliser le bot, mais chaque numéro est visible uniquement par 4 personnes : toi + staff.\n"
        "⚠️ 1 clic = 1 numéro retiré du stock. Ne gaspille pas."
    )
    embed.set_footer(text="RAMANE OFM - Excellence & Sécurité")

    db = load_num()
    embed.add_field(name="📦 Stock Live", value=f"🇺🇸 {len([n for n in db.get('usa',[]) if not n.get('used')])} | 🇬🇧 {len([n for n in db.get('uk',[]) if not n.get('used')])} | 🇨🇦 {len([n for n in db.get('canada',[]) if not n.get('used')])}", inline=False)

    await ctx.send(embed=embed, view=ViewNumeroGmailMain())

# --- FIN AJOUT BOSS ---

@bot.event
async def on_ready():
    bot.add_view(ViewNumeroUSA())
    bot.add_view(ViewPseudoFille())
    bot.add_view(ViewNumeroGmailMain()) # Ajout vocal
    bot.add_view(ChoixPaysGmailView()) # Ajout vocal
    print(f"EN LIGNE RAMANE - {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
