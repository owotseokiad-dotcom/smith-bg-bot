class ViewNumero(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(
        placeholder="🌍 Choisis ton pays (USA / Ukraine / UK / Canada)...",
        custom_id="ramane_numero_v4_final",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="USA - Numéro US", emoji="🇺🇸", value="usa", description="Numéro USA pour vérif TikTok/Insta"),
            discord.SelectOption(label="UK - Angleterre", emoji="🇬🇧", value="uk", description="Numéro Angleterre"),
            discord.SelectOption(label="Ukraine", emoji="🇺🇦", value="ukraine", description="Numéro Ukraine pas cher"),
            discord.SelectOption(label="Canada", emoji="🇨🇦", value="canada", description="Numéro Canada"),
        ]
    )
    async def select_pays(self, interaction: discord.Interaction, select: discord.ui.Select):
        pays = select.values[0]
        embed = discord.Embed(color=0x5865F2, title=f"Numéro {pays.upper()} - Instructions")
        embed.description = f"Tu as choisi **{pays.upper()}**\n\n**A QUOI SERT CE BOT?**\nCe bot te donne des numéros virtuels pour créer tes comptes.\n\n**ROLE:**\n1. Choisis un pays ci-dessus\n2. Le bot va te générer un numéro + site (5sim / SMS-Activate)\n3. Utilise le numéro pour vérifier ton compte\n\n**CONSEIL:** Prends toujours USA ou UK pour OFM, ça passe mieux."
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def setupnumero(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.send("Je place les bots numéro dans tes 3 salons...")
    cibles = 0
    for ch in ctx.guild.text_channels:
        name = ch.name.lower()
        if "numero" in name or "numéro" in name or "gmail" in name or "mail" in name:
            embed=discord.Embed(
                color=0x5865F2,
                title="📱 Générateur de Numéros & Gmail - Ramane OFM",
                description=(
                    "**A QUOI SERT CE BOT?**\n"
                    "Ce salon te permet de générer des numéros virtuels pour vérifier tes comptes modèles (Insta, TikTok, OnlyFans).\n\n"
                    "**ROLE DU BOT:**\n"
                    "• Te fournir un numéro jetable selon le pays que tu choisis\n"
                    "• Te donner le site pour acheter (5sim, SMS-Activate, etc)\n"
                    "• Te guider pour la vérification\n\n"
                    "**👇 COMMENT FAIRE?**\n"
                    "**Clique sur le menu ci-dessous et choisis 1 pays parmi les 4:**\n"
                    "🇺🇸 USA / 🇬🇧 Angleterre / 🇺🇦 Ukraine / 🇨🇦 Canada\n\n"
                    "Le bot t'enverra ensuite les instructions en privé."
                )
            )
            try:
                await ch.send(embed=embed, view=ViewNumero())
                cibles += 1
            except: pass

    await ctx.send(f"✅ Fait. Bot numéro placé dans {cibles} salons (tes 2 numéros + Gmail).")

@bot.event
async def on_ready():
    print(f"EN LIGNE {NOM_AGENCE}")
    bot.add_view(ViewScanCompte())
    bot.add_view(ViewMesVideos())
    bot.add_view(ViewPackReels())
    bot.add_view(ViewPseudosFilles())
    bot.add_view(ViewNumero()) # IMPORTANT pour que le menu reste après reboot
