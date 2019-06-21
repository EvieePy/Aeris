import discord
from discord.ext import commands

from main import Bot


ADMIN = 490952483238313995
MODERATOR = 578255729295884308
KNOWLEDGEABLE = 490994825315745795
TWITCHIO = 539436435556794369
BASE = 'https://api.github.com/'


class Pythonista(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.has_role(TWITCHIO)
    @commands.group(aliases=['twitchio'])
    async def git(self, ctx):
        pass

    @git.command()
    async def issue(self, ctx):
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'token {self.bot.config.get("TOKENS", "git")}',
                   'User-Agent': 'Aeris Discord Bot(TwitchIO Manager)'}

        data = {}

        msg = await ctx.send(content='Ok you want to make an issue, what should the title be? (Type quit at anytime to stop).')
        resp = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=None)

        if resp.content.lower() == 'quit':
            return await msg.edit('Ok, goodbye!')

        data['title'] = resp.content
        await resp.delete()

        await msg.edit(content='Ok, and what should the body of the issue say?')
        resp = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=None)

        if resp.content.lower() == 'quit':
            return await msg.edit('Ok, goodbye!')

        data['body'] = resp.content
        await resp.delete()

        await msg.edit(content='Ok and what labels would you like to assign? Options:\n'
                       'None\n'
                       'IRC\n'
                       'HTTP\n'
                       'bug\n'
                       'enhancement\n'
                       'new feature\n'
                       'help wanted\n\n'
                       'Separate labels with a comma')
        resp = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=None)

        if resp.content.lower() == 'quit':
            return await msg.edit('Ok, goodbye!')

        if resp.content.lower() == 'none':
            pass
        else:
            labels = resp.content.split(',')
            data['labels'] = labels

        await resp.delete()

        async with self.bot.session.post(BASE + 'repos/TwitchIO/TwitchIO/issues', json=data, headers=headers) as resp:
            if resp.status != 201:
                return await msg.edit(content='Something went wrong while creating this issue pleases try again!')

            resp = await resp.json()
            await msg.edit(content=f'Ok I have created this issue for you!\n<{resp["html_url"]}>')


def setup(bot):
    bot.add_cog(Pythonista(bot))
