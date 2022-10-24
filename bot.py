import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class Customhelp(commands.HelpCommand):
    def __init__(self):
        super().__init__()
    
    async def send_bot_help(self, mapping):
        for cog in mapping:
            await self.get_destination().send(f'{cog.qualified_name}: {[command.name for command in mapping[cog]]}')
    
    async def send_cog_help(self, cog):
        await self.get_destination().send(f'{cog.qualified_name}: {[command.name for command in cog.get_commands()]}')
    
    async def send_group_help(self, group):
        await self.get_destination().send(f'{group.name}: {[command.name for index, command in enumerate(group.commands)]}')
        
    async def send_command_help(self, command):
        return await super().send_command_help(command)


# Discord bot Initialization
intents = discord.Intents.all()
client = commands.Bot(command_prefix = '-',intents=intents, help_command=Customhelp(), activity = discord.Activity(type=discord.ActivityType.watching, name="Funcional 👀"))
client.remove_command('help')
key = os.getenv('TOKEN')



# This event happens when the bot gets run
@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")

    
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')


async def main():
    async with client:
        await load_extensions()
        await client.start(key)

asyncio.run(main())
