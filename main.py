import asyncio

from googleapiclient.discovery import build
from urllib.parse import parse_qs, urlparse
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import youtube_dl
import random

from dataMangement import *

import os

try:
    from apikeys import *
except:
    pass

try:
    from boto.s3.connection import S3Connection
    s3 = S3Connection(os.environ['YTDEVKEY'], os.environ['BOTTOKEN'])

    YTDEVKEY = os.environ['YTDEVKEY']
    BOTTOKEN = os.environ['BOTTOKEN']
except:
    pass

def GetPlaylistUrls(url: str):
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]
    youtube = build("youtube", "v3", developerKey=YTDEVKEY)

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


def GetYTVidTitle(url: str):
    youtube = build("youtube", "v3", developerKey=YTDEVKEY)

    myID = url.replace("https://www.youtube.com/watch?v=", "")

    request = youtube.videos().list(
        part='snippet',
        id=myID
    )

    response = request.execute()

    return response['items'][0]['snippet']['title']


def GetYTVidUrl(search: str):
    youtube = build("youtube", "v3", developerKey=YTDEVKEY)

    request = youtube.search().list(
        part='snippet',
        type='video',
        q=search,
        maxResults=1
    )

    response = request.execute()

    return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"


client = commands.Bot(command_prefix='t')

queue = []

serverData = GetServerInfo()

currentGuildID = 0

updateTPlayer = False

commandList = ["hello", "next", "play", "pause", "resume", "clear", "leave", "shuffle", "remove", "t"]

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

TOASTBOTID = 906763140748959774


@client.event
async def on_ready():
    print("The bot is now ready for use")
    print("----------------------------")


@client.event
async def on_message(message):
    global serverData
    global currentGuildID
    global commandList

    global queue

    currentGuildID = message.channel.guild.id
    messageChatID = message.channel.id
    toastChatID = int(GetChatID(serverData, currentGuildID))

    # Testing for commands in custom channel
    if messageChatID == toastChatID and message.author.id != TOASTBOTID:
        # Adding prefix to message
        if not message.content.startswith(tuple(commandList)):
            message.content = f"tplay {message.content}"
        # Removing message
        await message.channel.purge(limit=1)

    await client.process_commands(message)


@client.command()
async def hello(ctx):
    """
    Says hello.

    :param ctx:
    :return:
    """

    await ctx.send("hello, I am toast bot")


def GetUrl(song: str):
    """
    Returns info including the url of a given song title / link.

    :param song:
    :return:
    """
    info = ""

    with youtube_dl.YoutubeDL(ydl_param) as ydl:
        try:
            info = ydl.extract_info(song, download=False)
        except:
            pass

    if info != "":
        return {
            'link': info['formats'][0]['url'],
            'title': info['title']
        }
        # return info['formats'][0]['url']

    else:
        return False


def GetQueue():
    global queue

    queueString = "Queue:\n"

    if len(range(1, len(queue))) >= 10:
        for x in range(1, 11):
            queueString += f"{x}. {GetYTVidTitle(queue[x])}\n"

    else:
        for x in range(1, len(queue)):
            queueString += f"{x}. {GetYTVidTitle(queue[x])}\n"

    if len(range(1, len(queue))) > 10:
        queueString += f"...\n"

    return (queueString)


async def UpdateToastPlayer(titlestr, queuestr, chatID):
    titlestr = f"Playing - {titlestr}"

    mbed = discord.Embed(
        title=titlestr,
        description=queuestr
    )

    channel = client.get_channel(chatID)

    await channel.purge(limit=1)

    await channel.send(embed=mbed)


async def toastPlayerCheck():
    global queue
    global serverData
    global currentGuildID
    global updateTPlayer

    await client.wait_until_ready()

    while True:
        if updateTPlayer:
            chatID = GetChatID(serverData, currentGuildID)
            if len(queue) > 0:
                title = GetYTVidTitle(queue[0])
                qtitles = GetQueue()
                await UpdateToastPlayer(title, qtitles, chatID)
            else:
                channel = client.get_channel(chatID)
                await channel.purge(limit=1)

            updateTPlayer = False

        await asyncio.sleep(1)


@client.command(pass_context=True)
async def next(ctx):
    global voice

    voice.stop()


def next_song():
    """
    Plays the next song whether the command is called internally or
    from chat and updates the queue accordingly.

    :param ctx:
    :return:
    """

    global queue
    global voice

    global serverData
    global currentGuildID
    global updateTPlayer

    if len(queue) > 1:
        queue.pop(0)

        playableLink = GetUrl(queue[0])['link']

        source = FFmpegPCMAudio(playableLink, **ffmpeg_param)
        voice.play(source, after=lambda e: next_song())
        updateTPlayer = True

    elif len(queue) == 1:
        voice.stop()
        queue.pop(0)
        updateTPlayer = True


async def StartSong(ytlink):
    """
    Starts a song based on the currentSong parameter. If the given song is a playlist link,
    It calls "StartPlaylistSong".

    :param currentSong:
    :return:
    """

    global voice
    global updateTPlayer

    playableLink = GetUrl(ytlink)['link']

    source = FFmpegPCMAudio(playableLink, **ffmpeg_param)
    voice.play(source, after=lambda e: next_song())
    updateTPlayer = True

@client.command(pass_context=True)
async def play(ctx, *args: str):
    """
    Plays a song based on song arguments (link, title, playlist link).

    :param ctx:
    :param args:
    :return:
    """

    global voice
    global queue
    global updateTPlayer

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
                updateTPlayer = True


        elif "?watch" in songParam:
            queue.append(songParam)

        else:
            myUrl = GetYTVidUrl(songParam)
            print(f"url: {myUrl}")
            queue.append(myUrl)

        if len(queue) == 1:
            await StartSong(queue[0])

        else:
            updateTPlayer = True

    else:
        await ctx.send("You're not in a voice channel ya goof")


@client.command(pass_context=True)
async def pause(ctx):
    """
    Pauses currently playing song.

    :param ctx:
    :return:
    """

    tempPlayer = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if tempPlayer.is_playing():
        tempPlayer.pause()
    else:
        await ctx.send("There's nothing playing rn ya goof!")


@client.command(pass_context=True)
async def resume(ctx):
    """
    Resumes a currently playing song.

    :param ctx:
    :return:
    """

    tempPlayer = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if tempPlayer.is_paused():
        tempPlayer.resume()
    else:
        await ctx.send("I'm already playing ya goof!")


@client.command(pass_context=True)
async def clear(ctx):
    global updateTPlayer

    """
    Clears the queue.

    :param ctx:
    :return:
    """

    global queue
    for x in range(1, len(queue)):
        queue.pop(1)

    updateTPlayer = True


@client.command(pass_context=True)
async def leave(ctx):
    """
    Removes the bot from the server.

    :param ctx:
    :return:
    """

    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        queue = []
    else:
        await ctx.send("I'm not in a voice channel ya goof")


def IsSetup(guildID):
    """
    Checks if a given server has used the "setup" command.

    :param guildID:
    :return:
    """

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
    """
    Sets up the toast prefixless text channel.

    :param ctx:
    :return:
    """

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

            await ctx.send("The 🍞 chat has been setup!")
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

        await ctx.send("The 🍞 chat has been setup!")


@client.command(pass_context=True)
async def shuffle(ctx, playlistLink=""):
    """
    Shuffles the queue or plays shuffles a given playlist and adds it to queue.

    :param ctx:
    :param playlistLink:
    :return:
    """

    global queue
    global voice
    global updateTPlayer

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
            updateTPlayer = True


    else:
        tempqueue = queue[1:]
        random.shuffle(tempqueue)

        for x in range(0, len(tempqueue)):
            queue.pop(1)
            queue.insert(1, tempqueue[x])

        updateTPlayer = True

@client.command(pass_context=True)
async def remove(ctx, index):
    global queue
    global updateTPlayer

    try:
        queue.pop(int(index))
        updateTPlayer = True
    except:
        ctx.send("That number is not in the queue ya goof!")


@client.command(pass_context=True)
async def burger(ctx):
    await ctx.send("🍞")
    await ctx.send("🍅")
    await ctx.send("🥬")
    await ctx.send("🥩")
    await ctx.send("🍞")


client.loop.create_task(toastPlayerCheck())
client.run(BOTTOKEN)
