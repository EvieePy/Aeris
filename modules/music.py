import discord
import math
import plugins
import random
import re
import time
import wavelink
from discord.ext import buttons, commands
from main import Bot


RURL = re.compile(r'https?:\/\/(?:www\.)?.+')


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot
        self.wl = wavelink.Client(self.bot)

        bot.loop.create_task(self.__init_nodes__())

    async def __init_nodes__(self):
        await self.bot.wait_until_ready()

        nodes = {'MAIN': {'host': '0.0.0.0',
                          'port': 2333,
                          'rest_uri': 'http://0.0.0.0:2333',
                          'password': "password",
                          'identifier': 'MAIN',
                          'region': 'us_central'}}

        for n in nodes.values():
            node = await self.wl.initiate_node(**n)
            node.set_hook(self.event_hook)

    async def event_hook(self, event):
        if event.player._current.repeats:
            event.player._current.repeats -= 1
            event.player.index -= 1

        event.player.index += 1
        await event.player._play_next()

    def get_player(self, *, ctx: commands.Context=None, member=None):
        if member:
            player: plugins.Player = self.wl.get_player(member.guild.id, cls=plugins.Player)
            return player

        player: plugins.Player = self.wl.get_player(ctx.guild.id, cls=plugins.Player)
        if not player.dj:
            player.dj = ctx.author

        return player

    def is_privileged(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        return player.dj.id == ctx.author.id or ctx.author.guild_permissions.administrator

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        player = self.get_player(member=member)

        if member.bot:
            return

        if not player or not player.is_connected:
            return

        vc = self.bot.get_channel(int(player.channel_id))

        if after.channel == vc:
            player.last_seen = None

            if player.dj not in vc.members:
                player.dj = member
            return
        elif before.channel != vc:
            return

        if (len(vc.members) - 1) <= 0:
            player.last_seen = time.time()
        elif player.dj not in vc.members:
            for mem in vc.members:
                if mem.bot:
                    continue
                else:
                    player.dj = mem
                    break

    async def cog_before_invoke(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    async def cog_after_invoke(self, ctx):
        player = self.get_player(ctx=ctx)

        if player.updating:
            return

        await player.invoke_session()

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        embed = discord.Embed(title='Music Error', description=f'```\n{error}\n````', colour=0xebb145)
        await ctx.send(embed=embed)

    def required(self, ctx: commands.Context):
        channel = ctx.voice_client.channel
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop':
            if len(channel.members) - 1 == 2:
                required = 2

        return required

    @commands.command(aliases=['np', 'nowplaying', 'current', 'currentsong', 'current_song'])
    async def now_playing(self, ctx):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if player.updating:
            return

    @commands.command(aliases=['join'])
    async def connect(self, ctx, *, channel: discord.VoiceChannel=None):
        player = self.get_player(ctx=ctx)

        if player.is_connected and not self.is_privileged(ctx):
            return

        if channel:
            return await player.connect(channel.id)

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send('Could not connect to a voice channel. Make sure you specify or join a voice channel.')
        else:
            await player.connect(channel.id)

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str):
        await ctx.trigger_typing()

        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            await ctx.invoke(self.connect)

        query = query.strip('<>')

        if not RURL.match(query):
            query = f'ytsearch:{query}'

        tracks = await self.wl.get_tracks(query)
        if not tracks:
            return await ctx.send('No songs were found with that query. Please try again.', delete_after=15)

        if isinstance(tracks, wavelink.TrackPlaylist):
            for t in tracks.tracks:
                player.queue.append(plugins.Track(t.id, t.info, ctx=ctx))

            await ctx.send(f'```ini\nAdded the playlist {tracks.data["playlistInfo"]["name"]}'
                           f' with {len(tracks.tracks)} songs to the queue.\n```', delete_after=15)
        else:
            track = tracks[0]
            await ctx.send(f'```ini\nAdded {track.title} to the Queue\n```', delete_after=15)
            player.queue.append(plugins.Track(track.id, track.info, ctx=ctx))

        if not player.is_playing:
            await player._play_next()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if player.paused:
            return

        if self.is_privileged(ctx):
            await player.set_pause(True)
            player.pause_votes.clear()
            return await ctx.send(f'{ctx.author.mention} has paused the song as Admin or DJ', delete_after=10)

        if ctx.author in player.pause_votes:
            return await ctx.send('You have already voted to pause the song!', delete_after=10)

        player.pause_votes.add(ctx.author)
        if len(player.pause_votes) >= self.required(ctx):
            await ctx.send('Vote to pause the song passed. Now pausing!', delete_after=10)
            player.pause_votes.clear()
            return await player.set_pause(True)

        await ctx.send(f'Your vote to pause has been received. {self.required(ctx) - len(player.pause_votes)} more required', delete_after=10)

    @commands.command()
    async def resume(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.paused:
            return

        if self.is_privileged(ctx):
            await player.set_pause(False)
            player.resume_votes.clear()
            return await ctx.send(f'{ctx.author.mention} has resumed the song as Admin or DJ', delete_after=10)

        if ctx.author in player.resume_votes:
            return await ctx.send(f'{ctx.author.mention} you have already voted to resume the song!', delete_after=10)

        player.resume_votes.add(ctx.author)
        if len(player.resume_votes) >= self.required(ctx):
            await ctx.send('Vote to resume the song passed. Now resuming your song!', delete_after=10)
            player.resume_votes.clear()
            return await player.set_pause(False)

        await ctx.send(f'Your vote to resume has been received. {self.required(ctx) - len(player.resume_votes)} more required', delete_after=10)

    @commands.command()
    async def back(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f'{ctx.author.mention} has rewind the player.', delete_after=10)
            return await self.do_back(ctx)

        player.back_votes.add(ctx.author)
        if len(player.back_votes) >= self.required(ctx):
            await ctx.send('Vote to rewind the song passed. Now rewinding the player!', delete_after=10)
            player.back_votes.clear()

            return await self.do_back(ctx)

        await ctx.send(f'Your vote to rewind has been received. {self.required(ctx) - len(player.back_votes)} more required', delete_after=10)

    async def do_back(self, ctx):
        player = self.get_player(ctx=ctx)

        if int(player.position) / 1000 >= 7.0 and player.is_playing:
            return await player.seek(0)

        player.index -= 2
        if player.index < 0:
            player.index = -1

        return await player.stop()

    @commands.command(aliases=['disconnect'])
    async def stop(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f'{ctx.author.mention} has stopped the player as an Admin or DJ.', delete_after=10)
            return await player.teardown()

        await ctx.send('Only the DJ or Administrators may stop the player!', delete_after=20)

    @commands.command(aliases=['pass', 'next'])
    async def skip(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await player.stop()
            player.skip_votes.clear()
            return await ctx.send(f'{ctx.author.mention} has skipped the song as an Admin or DJ.', delete_after=15)

        if ctx.author in player.skip_votes:
            return await ctx.send(f'{ctx.author.mention} you have already voted to skip the song')

        player.skip_votes.add(ctx.author)
        if len(player.skip_votes) >= self.required(ctx):
            player.skip_votes.clear()
            await ctx.send('Vote to skip the song passed. Skipping your song!', delete_after=10)
            return await player.stop()

        await ctx.send(f'Your vote to skip has been received. {self.required(ctx) - len(player.skip_votes)} more required', delete_after=10)

    @commands.command(aliases=['mix'])
    async def shuffle(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if not len(player.queue) >= 3:
            return await ctx.send('Add more songs to the queue before shuffling.', delete_after=10)

        if self.is_privileged(ctx):
            random.shuffle(player.queue)
            player.shuffle_votes.clear()
            return await ctx.send(f'{ctx.author.mention} has shuffled the playlist as an Admin or DJ.', delete_after=10)

        if ctx.author in player.shuffle_votes:
            return await ctx.send(f'{ctx.author.mention} you have already voted to shuffle.', delete_after=10)

        player.shuffle_votes.add(ctx.author)
        if len(player.shuffle_votes) >= self.required(ctx):
            await ctx.send('Vote to shuffle the playlist passed. Now shuffling the playlist.', delete_after=10)
            player.shuffle_votes.clear()
            return random.shuffle(player.queue)

        await ctx.send(f'Your vote to shuffle was received. {self.required(ctx) - len(player.skip_votes)} more required', delete_after=10)

    @commands.command()
    async def repeat(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        if not player.queue and not player.current:
            return

        if self.is_privileged(ctx):
            await ctx.send(f'{ctx.author.mention} has repeated the song as an Admin or DJ.', delete_after=10)
            player.current.repeats += 1
            return

        if ctx.author in player.repeat_votes:
            return await ctx.send(f'{ctx.author.mention} you have already voted to repeat the song.', delete_after=10)

        player.repeat_votes.add(ctx.author)
        if len(player.repeat_votes) >= self.required(ctx):
            await ctx.send('Vote to repeat the song passed. Now repeating the song.', delete_after=10)
            player.current.repeats += 1
            return

        await ctx.send(f'{ctx.author.mention} Your vote to repeat the song was received.')

    @commands.command(aliases=['vol'])
    async def volume(self, ctx: commands.Context, *, vol: int):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return await ctx.send('I am not currently connected to voice.', delete_after=15)

        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.')

        await player.set_volume(vol)
        await ctx.send(f'Set the volume to **{vol}**%', delete_after=7)

    @commands.command(hidden=True)
    async def vol_up(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 100:
            vol = 100
            await ctx.send('Maximum volume reached', delete_after=7)

        await player.set_volume(vol)

    @commands.command(hidden=True)
    async def vol_down(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.send('Player is currently muted', delete_after=10)

        await player.set_volume(vol)

    @commands.command(aliases=['q', 'que'])
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx=ctx)

        if not player.queue:
            return await ctx.send('No more songs are queued.')

        entries = []
        if player._current.repeats:
            entries.append(f'**({player._current.repeats}x)** `{player._current.title}`')

        for song in player.queue[player.index + 1:]:
            entry = f'`{song.title}`'

            entries.append(entry)

        pagey = buttons.Paginator(timeout=180, colour=0xebb145, length=10,
                                  title=f'Player Queue | Upcoming ({len(player.queue)}) songs.',
                                  entries=entries, use_defaults=True)

        await pagey.start(ctx)

    @commands.command(name='debug')
    async def debug(self, ctx):
        """View debug information for the player."""
        player = self.get_player(ctx=ctx)
        node = player.node

        fmt = f'**Discord.py:** {discord.__version__} | **Wavelink:** {wavelink.__version__} | **Buttons:** 0.1.7\n\n' \
            f'**Connected Nodes:**  `{len(self.wl.nodes)}`\n' \
            f'**Best Avail Node:**     `{self.wl.get_best_node().__repr__()}`\n' \
            f'**WS Latency:**             `{self.bot.latency * 1000}`ms\n\n' \
            f'```\n' \
            f'Frames Sent:    {node.stats.frames_sent}\n' \
            f'Frames Null:    {node.stats.frames_nulled}\n' \
            f'Frames Deficit: {node.stats.frames_deficit}\n' \
            f'Frame Penalty:  {node.stats.penalty.total}\n\n' \
            f'CPU Load (LL):  {node.stats.lavalink_load}\n' \
            f'CPU Load (Sys): {node.stats.system_load}\n' \
            f'```'

        await ctx.send(fmt)


def setup(bot):
    bot.add_cog(Music(bot))
