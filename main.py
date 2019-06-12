import aiohttp
import configparser
import pathlib
import redio
from discord.ext import commands


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('::'))

        self.config = configparser.RawConfigParser()
        self.config.read('config.ini')

        self.session = None

        self.room_cache = redio.ConnectionPool('127.0.0.1', 6379, database=15)

    async def on_ready(self):
        print(f'Logged in: {self.user.name} | {self.user.id}')

        if not hasattr(self, 'appinfo'):
            self.appinfo = await self.application_info()

    async def prepare(self):
        resolver = aiohttp.AsyncResolver(nameservers=['1.1.1.1', '1.0.0.1'])
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, resolver=resolver))

        modules = [f'{p.parent}.{p.stem}' for p in pathlib.Path('modules').glob('*.py')]
        for module in modules:
            self.load_extension(module)

        await self.room_cache.open()
