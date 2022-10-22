from click import command
import discord
from discord.ext import commands
import asyncio

ayudaMusica = """
                            🎸Musica🎧
########################################################################
#!play   - Reproduce un URL o la primera cancion que encuentre en YT   #
#!pause  - Pausa la cancion actual                                     #
#!resume - Vuelve a reproducir la cancion pausada                      #
#!stop   - Detiene la reproduccion                                     #
########################################################################
"""



async def help(msg):
    if msg.content.startswith('!help musica'):
        await msg.channel.send(ayudaMusica)