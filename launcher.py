import asyncio
from main import Bot


loop = asyncio.get_event_loop()


bot = Bot()
loop.run_until_complete(bot.prepare())
bot.run(bot.config.get('TOKENS', 'bot'))
