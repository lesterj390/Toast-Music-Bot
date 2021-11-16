import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import youtube_dl
import asyncio
import random

from apikeys import *
from dataMangement import *


def GetPlaylistUrls(url: str):
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YTDEVKEY)

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

    for t in range(0, len(playlist_items)):
        playlist_items[t] = "https://www.youtube.com/watch?v=" + playlist_items[t]["snippet"]["resourceId"]["videoId"]

    return playlist_items


client = commands.Bot(command_prefix='t')

queue = []

serverData = GetServerInfo()

voice = ""

ydl_param = {
    'format': 'bestaudio',
    'noplaylist': 'True',
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


def GetUrl(song: str):
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


@client.command(pass_context=True)
async def next(ctx=""):
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

    if type(currentSong) == type({'a': 'b'}):
        songLink = currentSong['link']
        songTitle = currentSong['title']
        source = FFmpegPCMAudio(songLink, **ffmpeg_param)

        print(f"playing {songTitle}")
        print(songLink)

        player = voice.play(source, after=lambda e: asyncio.run(next()))

    else:
        await StartPlaylistSong(currentSong)

async def StartPlaylistSong(song: str):
    global voice

    currentSong = GetUrl(song)

    songLink = currentSong['link']
    songTitle = currentSong['title']
    source = FFmpegPCMAudio(songLink, **ffmpeg_param)

    print(f"playing {songTitle}")
    print(songLink)

    player = voice.play(source, after=lambda e: asyncio.run(next()))


@client.command(pass_context=True)
async def play(ctx, *args: str):
    global voice
    global queue

    songParam = ""

    for x in args:
        songParam += (f"{x} ")

    songParam = list(songParam)

    songParam[-1] = ""

    songParam = "".join(songParam)

    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            voice = await channel.connect()

        if "?list" in songParam:
            playlist = GetPlaylistUrls(songParam)
            for x in playlist:
                queue.append(x)

            if len(playlist) == len(queue):
                await StartSong(queue[0])

        else:
            currentSong = GetUrl(songParam)
            queue.append(currentSong)

            if len(queue) == 1:
                await StartSong(currentSong)

    else:
        await ctx.send("You're not in a voice channel ya goof")

@client.command(pass_context=True)
async def pause(ctx):
    tempPlayer = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if tempPlayer.is_playing():
        tempPlayer.pause()
    else:
        await ctx.send("There's nothing playing rn ya goof!")

@client.command(pass_context=True)
async def resume(ctx):
    tempPlayer = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if tempPlayer.is_paused():
        tempPlayer.resume()
    else:
        await ctx.send("I'm already playing ya goof!")

@client.command(pass_context=True)
async def clear(ctx):
    global queue
    for x in range(1, len(queue)):
        queue.pop(1)

@client.command(pass_context=True)
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        queue = []
    else:
        await ctx.send("I'm not in a voice channel ya goof")

def IsSetup(guildID):
    global serverData

    if serverData == False:
        print("im not an array")
        return False

    else:
        for x in serverData:
            if x['guildID'] == f'{guildID}':
                return True

        return False

@client.command(pass_context=True)
async def setup(ctx):
    global serverData

    serverData = GetServerInfo()

    server = {}
    guildID = ctx.message.guild.id

    if (IsSetup(guildID)):
        savedChatID = GetChatID(serverData, guildID)
        tempChannel = client.get_channel(int(savedChatID))
        if (tempChannel == None):
            channel = await ctx.guild.create_text_channel(name='🍞')
            UpdateChatID(serverData, guildID, channel.id)
            SaveServerInfo(serverData)
        else:
            await ctx.send("The chat is already setup ya goof!")

    else:
        channel = await ctx.guild.create_text_channel(name='🍞')
        server['guildID'] = f'{guildID}'
        server['chatID'] = f'{channel.id}'

        if (type(serverData) != type([])):
            serverData = []

        serverData.append(server)
        SaveServerInfo(serverData)

@client.command(pass_context=True)
async def shuffle(ctx, playlistLink = ""):
    global queue
    global voice

    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            voice = await channel.connect()

    if playlistLink != "":
        playlist = GetPlaylistUrls(playlistLink)
        random.shuffle(playlist)

        for x in playlist:
            queue.append(x)

        if len(playlist) == len(queue):
            await StartSong(queue[0])

    else:
        tempqueue = queue[1:]
        random.shuffle(tempqueue)

        for x in range(0, len(tempqueue)):
            queue.pop(1)
            queue.insert(1, tempqueue[x])

client.run(BOTTOKEN)
