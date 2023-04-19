import discord
import asyncio
import youtube_dl
from discord.ext import commands
from discord.utils import get
from fivem import FiveM as Fivem

server_maintenance = False
IP = "93.186.69.100"
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)
server = Fivem(ip=IP, port=PORT)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


async def embed_generator(title, desc, color, footer, field_number, names, texts, inlines, thumbnail):
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_author(name="Toulon Rp", icon_url="https://media.discordapp.net/attachments/1063947835613130802"
                                                "/1079825445274533969/logo.png?width=676&height=676")
    if thumbnail:
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1063947835613130802"
                                "/1079825445274533969/logo.png?width=676&height=676")
    for i in 0, field_number-1:
        embed.add_field(name=names[i], value=texts[i], inline=inlines[i])
    embed.set_footer(text=footer)
    return embed


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.current_player = None
        self.queue = asyncio.Queue()
        self.loop = False

    async def connect(self, ctx):
        await ctx.author.voice.channel.connect()
        self.voice_client = get(bot.voice_clients, guild=ctx.guild)

        print('Bot connected to voice channel.')

    async def disconnect(self):
        if self.voice_client is not None and self.voice_client.is_connected():
            await self.voice_client.disconnect()

    async def play(self, url, ctx):
        await self.queue.put(url)
        if not self.voice_client.is_playing():
            await self.play_next()

    async def play_next(self):
        if self.queue.empty():
            self.current_player = None
            return
        url = await self.queue.get()
        with youtube_dl.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False, )
            audio_url = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            print(audio_url)
        self.current_player = self.voice_client.play(audio_url, after=lambda _: bot.loop.create_task(self.play_next()))

    def skip(self):
        if self.voice_client.is_playing():
            self.voice_client.stop()

    def toggle_loop(self):
        self.loop = not self.loop


@bot.command()
async def join(ctx):
    player = bot.get_cog('MusicPlayer')
    if player.voice_client is None or not player.voice_client.is_connected():
        await player.connect(ctx)


@bot.command()
async def leave(ctx):
    player = bot.get_cog('MusicPlayer')
    if player.voice_client is not None and player.voice_client.is_connected():
        await player.disconnect()


@bot.command()
async def play(ctx, url):
    player = bot.get_cog('MusicPlayer')
    print(url)
    if player.voice_client is None:
        await player.connect(ctx)
    await player.play(url, ctx)


@bot.command()
async def skip(ctx):
    player = bot.get_cog('MusicPlayer')
    player.skip()


@bot.command()
async def loop(ctx):
    player = bot.get_cog('MusicPlayer')
    player.toggle_loop()


@bot.command()
async def send(ctx):
    await ctx.send('ok')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.add_cog(MusicPlayer(bot))



@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found.')
    else:
        print(error)


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return
    if before.channel is not None and after.channel is None:
        player = bot.get_cog('MusicPlayer')
        if player.voice_client is not None and player.voice_client.channel == before.channel:
            await player.disconnect()


bot.run('MTA3OTgyNDYyMjIxMzY2ODg5NA.Gm5z0D.1n_8KVDJ-q_w5b78ZNUhwZ5Yb3KMEFFSdu-2gY')
