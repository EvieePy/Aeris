import aiohttp
import asyncio
import configparser
import pathlib
from discord.ext import commands


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=['::'])

        self.config = configparser.RawConfigParser()
        self.config.read('config.ini')

        self.session = None

    async def on_ready(self):
        print(f'Logged in: {self.user.name} | {self.user.id}')

    async def prepare(self):
        resolver = aiohttp.AsyncResolver(nameservers=['1.1.1.1', '1.0.0.1'])
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, resolver=resolver))

        modules = [f'{p.parent}.{p.stem}' for p in pathlib.Path('modules').glob('*.py')]
        for module in modules:
            self.load_extension(module)
