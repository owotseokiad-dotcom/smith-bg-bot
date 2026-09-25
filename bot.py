import discord, os, re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

def find_chan(guild, mots):
    for c in guild.text_channels:
        name = c.name.lower()
        for m in mots:
            if m in name:
                return c
    return None

def get_mention(guild, mots):
    chan = find_chan(guild, mots)
    return chan.mention if chan else f"#{mots[0]}"

def a_deja_salon(member, cat):
    for chan in cat.text_channels:
        if chan.overwrites_for(member).read_messages and not member.bot:
            return chan
    return None

def message_bienvenue_complet(member, guild):
    # On récupère TOUS les salons importants
    bienvenue = get_mention(guild, ["bienvenue"])
    reglement = get_mention(guild, ["reglement", "regles"])
    annonces = get_mention(guild, ["annonce"])
    drive3 = get_mention(guild, ["drive-3", "drive3"])
    drive = get_mention(guild, ["drive"])
    entraide = get_mention(guild, ["entraide"])
    resultats = get_mention(guild, ["resultat"])
    boost = get_mention(guild, ["boost", "promo"])
    idees = get_mention(guild, ["idee", "contenu"])

    # Liste
