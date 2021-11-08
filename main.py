import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import youtube_dl
import asyncio

# example playlist = 'https://www.youtube.com/playlist?list=PLSXSvMgBtiIMZxCPYc7ahT9omTyFnGXL3'

def GetPlaylistUrls(url: str):
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]
    #
    # print(f'get all playlist items links from {playlist_id}')
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey="AIzaSyAXw2am0_BDG2v85kkjpKKDI2HfK6YhSJM")

    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    playlist_items = []
    while request is not None:
        response = request.execute()
        playlist_items += response["items"]
        request = youtube.playlistItems().list_next(request, response)

    # print(f"total: {len(playlist_items)}")

    for t in range(0, len(playlist_items)):
        playlist_items[t] = "https://www.youtube.com/watch?v=" + playlist_items[t]["snippet"]["resourceId"]["videoId"]

    return playlist_items


client = commands.Bot(command_prefix = 't')

queue = []

queueIndex = 0

voice = ""

ydl_param = {
            'format': 'bestaudio',
            'noplaylist':'True',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredquality': '192'
            }]
        }

ffmpeg_param = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@client.event
async def on_ready():
    print("The bot is now ready for use")
    print("----------------------------")

@client.command()
async def hello(ctx):
    await ctx.send("hello, I am toast bot")

def GetUrl(song : str):
    info = ""

    if "watch?v" in song:
        with youtube_dl.YoutubeDL(ydl_param) as ydl:
            try:
                info = ydl.extract_info(song, download=False)
            except:
                pass
    else:
        with youtube_dl.YoutubeDL(ydl_param) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % song, download=False)['entries'][0]
            except:
                pass

    if info != "":
        return {
            'link': info['formats'][0]['url'],
            'title': info['title']
        }

    else:
        return False

@client.command(pass_context = True)
async def next(ctx = ""):
    global queue
    global voice

    if len(queue) > 1:
        if ctx != "":
            voice.stop()
        else:
            queue.pop(0)
            await StartSong(queue[0])

    elif len(queue) == 1:
        voice.stop()
        queue.pop(0)



async def StartSong(currentSong):
    global voice

    songLink = currentSong['link']
    songTitle = currentSong['title']
    source = FFmpegPCMAudio(songLink, **ffmpeg_param)

    print(f"playing {songTitle}")
    print(songLink)

    player = voice.play(source, after=lambda e: asyncio.run(next()))

@client.command(pass_context = True)
async def play(ctx, *args : str):
    global voice
    global queue

    songParam = ""

    for x in args:
        songParam += (f"{x} ")

    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            voice = await channel.connect()

        currentSong = GetUrl(songParam)

        queue.append(currentSong)

        if len(queue) == 1:
            await StartSong(currentSong)

    else:
        await ctx.send("You're not in a voice channel ya goof")

@client.command(pass_context = True)
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        queue = []
    else:
        await ctx.send("I'm not in a voice channel ya goof")


client.run("OTA2NzYzMTQwNzQ4OTU5Nzc0.YYdW-w.V32tYXU-OuAdKSeFWpaBAuxw6NQ")
