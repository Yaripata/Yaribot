import discord
import asyncio
import youtube_dl
from discord.ext import commands
#import logging
import sys


# root = logging.getLogger("discord.ext.commands.bot")

# #root = logging.getLogger()
# root.setLevel(logging.DEBUG)

# #handler = logging.StreamHandler(sys.stdout)
# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# root.addHandler(handler)


            
class music_cog(commands.Cog):
    
    def __init__(self,bot):
        self.bot = bot
        self.vc = None
        
        self.is_playing = False
        self.is_paused = False
        
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
    
    
        
    def play_next(self,voice_client):
        if len(self.music_queue[voice_client.guild.id]) > 0:
            self.is_playing = True

            m_url, nombre, _ = self.music_queue[voice_client.guild.id][0]
            
            self.music_queue[voice_client.guild.id].pop(0)

            self.voice_clients[voice_client.guild.id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(voice_client))
        else:
            self.is_playing = False
    
    
    async def play_music(self, ctx,Guildid):
        if len(self.music_queue[Guildid]) > 0:
            self.is_playing = True
            
            m_url, nombre, voice = self.music_queue[Guildid][0]
            
            if self.voice_clients[voice.guild.id] == None or not self.voice_clients[voice.guild.id].is_connected():
                self.voice_clients[voice.guild.id] = await voice.connect()
                if self.voice_clients[voice.guild.id] == None:
                    await ctx.send("No pude conectarme al voice wn")
                    return
            else:
                await self.voice_clients[voice.guild.id].move_to(voice)
        
            self.music_queue[Guildid].pop(0)
            
            await ctx.send("Reproduciendo "+ nombre +" 🎧")
            
            player = discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options)
            self.voice_clients[voice.guild.id].play(player,after=lambda e: self.play_next(voice_client))
        else:
            self.is_playing = False
    
    
    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_client = ctx.author.voice.channel
        
        if voice_client is None:
            await ctx.send('Metete a un chat de voz pto')
        else:

            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))

                song = data['url']
                titulo = data['title']
                
                await ctx.send("Cancion ql añadida a la cola")
                
                try:
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                except:
                    self.music_queue[voice_client.guild.id] = []
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                    self.voice_clients[voice_client.guild.id] = None

                if self.is_playing == False:
                    await self.play_music(ctx,voice_client.guild.id)
                    

            except Exception as err:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info("ytsearch:%s" % query, download=False)['entries'][0])

                song = data['formats'][0]['url']
                titulo = data['title']
                
                await ctx.send("Cancion ql añadida a la cola")
                try:
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                except:
                    self.music_queue[voice_client.guild.id] = []
                    self.music_queue[voice_client.guild.id].append([song,titulo,voice_client])
                    self.voice_clients[voice_client.guild.id] = None
                
                
                if self.is_playing == False:
                    await self.play_music(ctx,voice_client.guild.id)
            
    
    @commands.command(name="pause", aliases=["pa"], help="Pausa la cancion actual")
    async def pause(self, ctx):
        try:
            client = ctx.author.voice.channel.guild.id
            await ctx.send("Pausada la cancion ql")
            self.voice_clients[client].pause()
        except Exception as err:
            print(err)
    
    
    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        client = ctx.author.voice.channel
        if self.voice_clients[client.guild.id] != None and self.voice_clients[client.guild.id]:
            self.voice_clients[client.guild.id].stop()
            #try to play next in the queue if it exists
            self.play_next(client)
            await ctx.send("Saltada la cancion ql")
            
            
    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx):
        client = ctx.author.voice.channel.guild.id
        retval = ""
        for i in range(0, len(self.music_queue[client])):
            # display a max of 5 songs in the current queue
            if (i > 4): break
            retval += self.music_queue[client][i][1] + "\n"

        if retval != "":
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
