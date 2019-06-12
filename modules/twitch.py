import discord
from discord.ext import commands

from main import Bot


class Twitch(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        role = discord.utils.get(before.guild.roles, name='Live 🔴')   # Invisible Emote

        if not role:
            return

        if any(isinstance(activity, discord.Streaming) for activity in after.activities) and not\
                any(isinstance(activity, discord.Streaming) for activity in before.activities):

            await after.add_roles(role, reason='Live Streamer Update')

        elif not any(isinstance(activity, discord.Streaming) for activity in after.activities) and\
                any(isinstance(activity, discord.Streaming) for activity in before.activities):

            await after.remove_roles(role, reason='Live Streamer Update')

    @commands.group(aliases=['stream'])
    async def streams(self, ctx: commands.Context):
        pass

    @streams.command()
    async def setup(self, ctx: commands.Context):
        await ctx.trigger_typing()
        role: discord.Role = discord.utils.get(ctx.guild.roles, name='Live 🔴')  # Invisible Emote

        if role:
            return await ctx.send('Your guild already has a Live streamer role.')

        try:
            await ctx.guild.create_role(name='Live 🔴', hoist=True, reason='Twitch Live Role')
        except discord.HTTPException as e:
            return await ctx.send(f'An error occurred while creating the Streamer Role.\n\n{e}')

        await ctx.send('Live streamer role was successfully created. You may now move it to your preferred position.')

    @streams.command(aliases=['delete', 'del'])
    async def remove(self, ctx: commands.Context):
        await ctx.trigger_typing()
        role: discord.Role = discord.utils.get(ctx.guild.roles, name='Live 🔴')  # Invisible Emote

        if not role:
            return await ctx.send('Your guild does not have a Live streamer role setup.')

        try:
            await role.delete()
        except discord.HTTPException as e:
            return await ctx.send(f'An error occurred while deleting the Streamer Role.\n\n{e}')

        await ctx.send('Live streamer role was successfully removed.')


def setup(bot):
    bot.add_cog(Twitch(bot))
