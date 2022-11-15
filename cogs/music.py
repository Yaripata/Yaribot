from logging import exception
import discord
import asyncio
import youtube_dl
from discord.ext import commands
import logging
import sys
import time
import tabulate

root = logging.getLogger("discord.ext.commands.bot")

# #root = logging.getLogger()
root.setLevel(logging.DEBUG)

# #handler = logging.StreamHandler(sys.stdout)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


            
class music_cog(commands.Cog):
    
    def __init__(self,bot):
        self.bot = bot
        self.vc = None
        
        self.is_playing = {}
        
        self.music_queue = {}
        
        self.voice_clients = {}
        
        self.yt_dl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            }
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': "-vn"
            }
        self.ytdl = youtube_dl.YoutubeDL(self.yt_dl_opts)
    
    
        
    def play_next(self,ctx,voice_client):
        if len(self.music_queue[voice_client]) > 0:
            self.is_playing[voice_client] = True

            m_url, _ , _ = self.music_queue[voice_client][0]
            
            self.music_queue[voice_client].pop(0)

            self.voice_clients[voice_client].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(ctx,voice_client))
        else:
            self.is_playing[voice_client] = False
    
    
    async def play_music(self, ctx,Guildid):
        if len(self.music_queue[Guildid]) > 0:
            self.is_playing[Guildid] = True
            
            m_url, nombre, voice = self.music_queue[Guildid][0]
            
            if self.voice_clients[voice.guild.id] == None:
                self.voice_clients[voice.guild.id] = await voice.connect()
                if self.voice_clients[voice.guild.id] == None:
                    await ctx.send("No pude conectarme al voice wn")
                    return
            else:
                await self.voice_clients[voice.guild.id].move_to(voice)
        
            self.music_queue[Guildid].pop(0)
            
            await ctx.send("Reproduciendo "+ nombre[0] +" 🎧")
            
            player = discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options)
            self.voice_clients[voice.guild.id].play(player,after=lambda e: self.play_next(ctx,Guildid))
        else:
            self.voice_clients[Guildid].stop()
            await self.voice_clients[Guildid].disconnect()
            await ctx.send("No hay mas musica, chao")
            self.is_playing[Guildid] = False


    @commands.command(name="play", aliases=["p","playing"], help="Reproduce un link o una busqueda de Youtube.")
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_client = ctx.author.voice
        
        if voice_client is None:
            await ctx.send('Metete a un chat de voz pto')
        else:
            voice_client = ctx.author.voice.channel

            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))

                song = data['url']
                titulo = [data['title'],time.strftime('%M:%S',time.gmtime(data['duration'])),data['channel']]
                
                await ctx.send("Cancion ql añadida a la cola")
                
                try:
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                except Exception:
                    self.music_queue[voice_client.guild.id] = []
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                    self.voice_clients[voice_client.guild.id] = None
                    self.is_playing[voice_client.guild.id] = False

                if self.is_playing[voice_client.guild.id] == False:
                    await self.play_music(ctx,voice_client.guild.id)
                    

            except Exception:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info("ytsearch:%s" % query, download=False)['entries'][0])

                song = data['formats'][0]['url']
                titulo = [data['title'],time.strftime('%M:%S',time.gmtime(data['duration'])),data['channel']]
                
                await ctx.send("Cancion ql añadida a la cola")
                try:
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                except Exception:
                    self.music_queue[voice_client.guild.id] = []
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                    self.voice_clients[voice_client.guild.id] = None
                    self.is_playing[voice_client.guild.id] = False
                
                
                if self.is_playing[voice_client.guild.id] == False:
                    await self.play_music(ctx,voice_client.guild.id)
            
    
    @commands.command(name="pause", aliases=["pa"], help="Pausa la cancion actual")
    async def pause(self, ctx):
        try:
            client = ctx.author.voice.channel.guild.id
            await ctx.send("Pausada la cancion ql")
            self.voice_clients[client].pause()
        except Exception as err:
            print(err)
    
    
    @commands.command(name="skip", help="Salta la cancion actual.")
    async def skip(self, ctx):
        client = ctx.author.voice.channel
        if self.voice_clients[client.guild.id] != None and self.voice_clients[client.guild.id]:
            self.voice_clients[client.guild.id].stop()
            #try to play next in the queue if it exists
            await self.play_music(ctx,client.guild.id)
            await ctx.send("Saltada la cancion ql")
            
            
    @commands.command(name="queue", aliases=["q"], help="Muestra las canciones que estan en la cola")
    async def queue(self, ctx):
        client = ctx.author.voice.channel.guild.id
        retval = "🎧 Duracion \t Titulo \t Canal 🎧 \n"
        template = "📍  {} \t {} \t {} \n"

        for i in range(0, len(self.music_queue[client])):
            # display a max of 5 songs in the current queue
            if (i > 4): break
            retval += template.format(self.music_queue[client][i][1][1],self.music_queue[client][i][1][0],self.music_queue[client][i][1][2])

        if retval != "🎧 Duracion \t Titulo \t Canal 🎧":
            await ctx.send(retval)
        else:
            await ctx.send("No hay musica en la lista")
            
            
    @commands.command(name="resume", aliases=["r"], help="Vuelve a reproducir la cancion pausada")
    async def resume(self,ctx):
        try:
            client = ctx.author.voice.channel.guild.id
            self.voice_clients[client].resume()
            await ctx.send("Resumia la cancion ql")
        except Exception as err:
            print(err)
    
    @commands.command(name="stop", aliases=["s"], help="Detiene el bot")      
    async def stop(self,ctx):
        try:
            client = ctx.author.voice.channel.guild.id
            self.voice_clients[client].stop()
            await self.voice_clients[client].disconnect()
            await ctx.send("Chao ctm")
        except Exception as err:
            print(err)



async def setup(bot):
    await bot.add_cog(music_cog(bot))
