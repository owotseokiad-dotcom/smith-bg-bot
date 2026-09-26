@bot.command()
async def wipeall(ctx):
    if not ctx.author.guild_permissions.administrator: 
        return
    await ctx.send("💣 NETTOYAGE DE L'AGENCE EN COURS... Ca va tout supprimer.")

    # Liste des mots clés à effacer
    mots_a_supprimer = [
        "comptes-instagram", "packs-reels", "mes-videos-virales",
        "pseudo", "numero", "drive", "description", "bio", "pdp", 
        "photo", "pack", "viral", "comptes"
    ]

    supprimes = 0
    for ch in list(ctx.guild.text_channels):
        for mot in mots_a_supprimer:
            if mot in ch.name.lower():
                try:
                    await ch.delete(reason=f"Wipe demandé par {ctx.author}")
                    supprimes += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
                break
    
    # Supprime aussi les threads dans les salons restants
    for ch in ctx.guild.text_channels:
        if ch.threads:
            for thread in list(ch.threads):
                try:
                    await thread.delete()
                except:
                    pass

    await ctx.send(f"✅ TERMINÉ. {supprimes} salons supprimés. L'agence est clean. Plus de boutons.")
