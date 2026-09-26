@bot.command()
async def cleanbot(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    await ctx.send("🧹 Je vide tout ce que j'ai mis dans les salons de bot... Je touche pas aux salons privés.")
    
    # Salons où le bot doit nettoyer son contenu
    cibles = ["pseudo", "numero", "pack", "comptes-instagram", "mes-videos", "drive", "description", "bio", "pdp", "photo", "viral"]
    nettoyes = 0
    
    for ch in ctx.guild.text_channels:
        # On saute les salons privés
        if "privé" in ch.name.lower() or "prive" in ch.name.lower() or "private" in ch.name.lower():
            continue
        
        for mot in cibles:
            if mot in ch.name.lower():
                try:
                    # Supprime 100 derniers messages du bot
                    async for m in ch.history(limit=100):
                        if m.author == bot.user:
                            try:
                                await m.delete()
                                nettoyes += 1
                                await asyncio.sleep(0.3)
                            except: pass
                except: pass
                break
    
    await ctx.send(f"✅ CLEAN FINI. J'ai supprimé {nettoyes} messages que j'avais mis. Les salons privés sont restés intacts. Maintenant je ne remettrai plus rien si tu ne tapes pas !setup")

@bot.command()
async def setupall(ctx):
