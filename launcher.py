import asyncio
from main import Bot

loop = asyncio.get_event_loop()

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


bot = Bot()
loop.run_until_complete(bot.prepare())
bot.run(bot.config.get('TOKENS', 'bot'))
