import asyncio
import discord
from discord.ext import commands

from main import Bot


class Rooms(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot
        self.room_cache = self.bot.room_cache

    async def temps_checker(self, new_id):
        await self.bot.wait_until_ready()

        while True:
            await asyncio.sleep(300)
            new = self.bot.get_channel(new_id)
            if not new:
                return

            if len(new.members) == 0:
                try:
                    return await new.delete()
                except discord.HTTPException:
                    return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not after.channel:
            return

        async with self.room_cache.acquire() as conn:
            id_ = await conn.get(member.guild.id)
            if not id_:
                return

            room = self.bot.get_channel(int(await conn.get(id_)))
            if not room:
                return

            if after.channel.id == room.id:
                old = discord.utils.get(member.guild.voice_channels, name=member.name)

                if old:
                    await member.move_to(old)
                else:
                    new = await member.guild.create_voice_channel(member.name, category=room.category)
                    await member.move_to(new)
                    asyncio.create_task(self.temps_checker(new.id))

    @commands.group(aliases=['auto_room', 'autorooms', 'auto_rooms'])
    async def autoroom(self, ctx):
        pass

    @autoroom.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def setup(self, ctx: commands.Context):
        async with self.room_cache.acquire() as conn:
            room = await conn.get(ctx.guild.id)

            if self.bot.get_channel(room):
                return await ctx.send('You already have an Auto-Room setup.')

            try:
                cat = await ctx.guild.create_category_channel('Temp-Rooms')
                chan = await ctx.guild.create_voice_channel('🎧 Auto Temp 🎧', category=cat)
            except discord.HTTPException as e:
                return await ctx.send(f'Something went wrong while creating your Auto-Room.\n\n{e}')

            await ctx.send('Successfully created your Auto-Room.')
            await conn.set(ctx.guild.id, chan.id)

    @autoroom.command(aliases=['delete', 'del'])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def remove(self, ctx: commands.Context):
        async with self.room_cache.acquire() as conn:
            room = self.bot.get_channel(int(await conn.get(ctx.guild.id)))

            if not room:
                await conn.delete(ctx.guild.id)
                return await ctx.send('You do not currently have an Auto-Room setup.')

            cat = room.category

            try:
                await room.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                return await ctx.send(f'Something went wrong while deleting your Auto-Room.\n\n{e}')

            try:
                await cat.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                return await ctx.send(f'Something went wrong while deleting your Auto-Room.\n\n{e}')

            await conn.delete(ctx.guild.id)
            await ctx.send('Successfully removed your Auto-Room.')


def setup(bot):
    bot.add_cog(Rooms(bot))
