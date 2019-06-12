import discord
from discord.ext import commands

from main import Bot


class Meta(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.command()
    async def about(self, ctx):
        embed = discord.Embed(title='Aeris | About', colour=0xb1f432)
        embed.set_author(name='Eviee#0666', url='https://github.com/EvieePy',
                         icon_url=self.bot.appinfo.owner.avatar_url)
        embed.description = 'Aeris is an easy to use general purpose bot, with a unique and dynamic music player.'
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        embed.add_field(name='\u200b', value='[Support Server](https://discord.gg/JhW28zp)')
        embed.add_field(name='\u200b', value='[Source](https://github.com/EvieePy/Aeris)')

        embed.add_field(name='Guilds', value=str(len(self.bot.guilds)))
        embed.add_field(name='Users', value=str(len(set(self.bot.get_all_members()))))

        embed.set_footer(text='Made in Python with Discord.py, Wavelink and Buttons.')

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Meta(bot))
