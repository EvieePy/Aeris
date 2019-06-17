import datetime
import discord
from discord.ext import buttons, commands

from main import Bot


class Todo(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.group()
    async def todo(self, ctx):
        pass

    @todo.command(aliases=['make', 'add', 'create'])
    async def todo_create(self, ctx, *, entry: str):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if len(entry) > 120:
            return await ctx.send('Your TODO entry must be 120 characters or shorter.', delete_after=15)

        async with self.bot.todo_cache.acquire() as conn:
            resp = await conn.zadd(ctx.author.id, datetime.datetime.utcnow().toordinal(), entry)

        if isinstance(resp, int):
            return await ctx.send('Ok. I have added this to your todos.', delete_after=15)

        await ctx.send('There was an error processing your entry, try again!', delete_after=15)

    @todo.command(aliases=['delete', 'del', 'complete', 'remove'])
    async def todo_remove(self, ctx, index: int):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        async with self.bot.todo_cache.acquire() as conn:
            entries = await conn.zrange(ctx.author.id, 0, -1)

            if not entries:
                return await ctx.send('You do not currently have any TODOs.', delete_after=15)

            try:
                entry = entries[index - 1]
            except IndexError:
                return await ctx.send('That TODO ID does not exist.', delete_after=15)

            await conn.zrem(ctx.author.id, entry)

        await ctx.send('Successfully removed your TODO entry.', delete_after=15)

    @todo.command(aliases=['list', 'ls'])
    async def todo_list(self, ctx, *, member: discord.Member=None):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if member is None:
            member = ctx.author

        async with self.bot.todo_cache.acquire() as conn:
            entries = await conn.zrange(member.id, 0, -1)

        if not entries:
            return await ctx.send(f'{member.name} has no TODOs.', delete_after=15)

        entries = [f'**{index}:** {entry.decode()}' for index, entry in enumerate(entries, 1)]
        pagey = buttons.Paginator(timeout=300, entries=entries, embed=True, title=f'{member.name} - TODOs',
                                  thumbnail=member.avatar_url, colour=0xbcf379)

        await pagey.start(ctx)

    @todo.command(aliases=['clear', 'clr'])
    async def todo_clear(self, ctx):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        async with self.bot.todo_cache.acquire() as conn:
            await conn.delete(ctx.author.id)

        await ctx.send('Successfully cleared your TODO list.', delete_after=15)

    @commands.command()
    async def todos(self, ctx, *, member: discord.Member=None):
        await ctx.invoke(self.todo_list, member=member)


def setup(bot):
    bot.add_cog(Todo(bot))
