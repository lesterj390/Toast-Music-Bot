from googleapiclient.discovery import build
from urllib.parse import parse_qs, urlparse
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import FFmpegPCMAudio
from pytube import YouTube
from pytube.exceptions import *
import random
import io

from dataMangement import *

import os

try:
    YTDEVKEY = os.getenv('YTDEVKEY')
    BOTTOKEN = os.getenv('BOTTOKEN')
except:
    pass

try:
    from apikeys import *
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

    try:
        return response['items'][0]['snippet']['title']
    except:
        return "Title Error"


def GetYTVidUrl(search: str):
    youtube = build("youtube", "v3", developerKey=YTDEVKEY)

    request = youtube.search().list(
        part='snippet',
        type='video',
        q=search,
        maxResults=1
    )

    try:
        response = request.execute()

        return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    except Exception as E:
        print("Could not find url.")
        return None


help_header = commands.DefaultHelpCommand(
    no_category='Commands'
)

intent = discord.Intents.default()
intent.message_content = True
client = commands.Bot(command_prefix='t', help_command=help_header, intents=intent)

queues = {}

startupDB = Database()
startupDB.CreateTables()
startupDB.conn.close()

currentGuildID = 0

commandList = ["next", "play", "pause", "resume", "clear", "leave", "shuffle", "remove", "swap"]

voice = ""

voices = {}

ffmpeg_param = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 4000'
}

TOASTBOTID = 906763140748959774


@client.event
async def on_ready():
    print("The bot is now ready for use")
    print("----------------------------")
    # toastPlayerCheck.start()
    # client.loop.create_task(toastPlayerCheck())
    # toastPlayerCheck.start()


@client.event
async def on_message(message):
    global currentGuildID
    global commandList
    global queues

    serverDB = Database()

    currentGuildID = message.channel.guild.id
    messageChatID = message.channel.id
    toastChatID = int(serverDB.GetChatID(currentGuildID))
    serverDB.conn.close()

    if currentGuildID not in queues:
        queues[currentGuildID] = []

    # Testing for commands in custom channel
    if messageChatID == toastChatID and message.author.id != TOASTBOTID:
        # Adding prefix to message
        if not message.content.startswith(tuple(commandList)):
            message.content = f"tplay {message.content}"
        elif not message.content.startswith("t"):
            message.content = f"t{message.content}"
        await message.channel.purge(limit=1)

    await client.process_commands(message)


@client.command()
async def hello(ctx):
    """
    Says hello.

    :param ctx:
    :return:
    """

    await ctx.send("Hello, I am Toast Bot")


def GetYouTubeLink(song: str):
    """
    Returns the YouTube URL of a given song (this can be a YouTube link input or search query)

    :param song:
    :return:
    """
    info = ""

    if song is None:
        return None

    videoID = song.split("?")
    # song is already a YouTube URL
    if len(videoID) > 1:
        videoID = parse_qs(videoID[1])
        if "v" in videoID.keys():
            videoID = videoID["v"][0]
            return f"https://www.youtube.com/watch?v={videoID}"
    # song is the title of a video
    else:
        return GetYTVidUrl(song)


def GetQueueString(guildID):
    global queues

    queueString = ""

    if len(queues[guildID]) > 1:
        queueString += "Queue\n"

        for x in range(1, min(11, len(queues[guildID]))):
            queueString += f"{x}. {GetYTVidTitle(queues[guildID][x])}\n"

    if (len(queues[guildID]) - 1) > 10:
        queueString += f"...\n"

    return queueString


async def UpdateToastPlayer(guildID):
    serverDB = Database()
    chatID = int(serverDB.GetChatID(guildID))
    channel = client.get_channel(chatID)

    if len(queues[guildID]) == 0:
        await channel.purge(limit=1)
        return

    titlestr = GetYTVidTitle(queues[guildID][0])
    queuestr = GetQueueString(guildID)

    serverDB.conn.close()

    titlestr = f"Playing - {titlestr}"

    mbed = discord.Embed(
        title=titlestr,
        description=queuestr
    )

    channel = client.get_channel(chatID)

    await channel.purge(limit=1)

    await channel.send(embed=mbed)


@client.command(pass_context=True)
async def next(ctx=""):
    """
    Plays the next song in the queue by stopping the current song.

    :param ctx:
    :return:
    """
    global voices
    global currentGuildID

    voices[currentGuildID].stop()


def dequeue(guildID):
    """
    Removes a song from the queue and plays it.

    :param guildID:
    :return:
    """

    global currentGuildID

    global voices
    global queues

    if len(queues[guildID]) >= 1:
        songFinishLambda = lambda e: (queues[guildID].pop(0),
                                      dequeue(guildID))
        try:
            nextSong = queues[guildID][0]

            if nextSong is None:
                raise VideoUnavailable("This video's link could not be found.")

            nextYouTubeLink = GetYouTubeLink(nextSong)

            client.loop.create_task(UpdateToastPlayer(guildID))

            playableLink = YouTube(nextYouTubeLink, use_oauth=False)
            playableLink = playableLink.streams.get_audio_only().url
            print(playableLink)

            source = FFmpegPCMAudio(playableLink, **ffmpeg_param)

            voices[guildID].play(source, after=songFinishLambda)
        except AgeRestrictedError:
            print("Age restricted video could not be played and was removed.")
            songFinishLambda(None)
        except VideoUnavailable:
            print("This video could not be played and was removed.")
            songFinishLambda(None)
        except Exception as E:
            print(f"I have no clue why this didn't work but here: {E}")
            songFinishLambda(None)
    else:
        client.loop.create_task(UpdateToastPlayer(guildID))


@client.command(pass_context=True)
async def play(ctx, *args: str):
    """
    Plays a song based on song arguments (link, title, playlist link).

    :param ctx:
    :param args:
    :return:
    """

    global voices

    global queues
    global currentGuildID

    # Play has to tag an *args variable to capture sentences since it delimits by space
    # This code turns the space delimited arguments into a single string
    songParam = ""
    for x in args:
        songParam += (f"{x} ")
    songParam = list(songParam)
    songParam[-1] = ""
    songParam = "".join(songParam)

    if not ctx.author.voice:
        await ctx.send("You're not in a voice channel ya goof")
        return

    channel = ctx.message.author.voice.channel
    if not ctx.voice_client:
        voices[currentGuildID] = await channel.connect()

    if "?list" in songParam:  # If playlist
        playlist = GetPlaylistUrls(songParam)
        for x in playlist:
            queues[currentGuildID].append(x)

        if len(playlist) == len(queues[currentGuildID]):
            dequeue(currentGuildID)
        else:
            await UpdateToastPlayer(currentGuildID)

    elif "?watch" in songParam:
        queues[currentGuildID].append(songParam)
        if len(queues[currentGuildID]) == 1:
            dequeue(currentGuildID)
        else:
            await UpdateToastPlayer(currentGuildID)

    else:
        myUrl = GetYouTubeLink(songParam)
        queues[currentGuildID].append(myUrl)
        if len(queues[currentGuildID]) == 1:
            dequeue(currentGuildID)
        else:
            await UpdateToastPlayer(currentGuildID)


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
async def clear(ctx=""):
    """
    Clears the queue.

    :param ctx:
    :return:
    """
    global currentGuildID

    queues[currentGuildID] = queues[currentGuildID][:1]
    await UpdateToastPlayer(currentGuildID)


@client.command(pass_context=True)
async def leave(ctx):
    """
    Removes the bot from the server.

    :param ctx:
    :return:
    """

    global queues
    global currentGuildID

    if ctx.voice_client:
        queues[currentGuildID] = queues[currentGuildID][:1]
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel ya goof")


@client.command(pass_context=True)
async def setup(ctx):
    """
    Sets up the toast prefixless text channel.

    :param ctx:
    :return:
    """

    serverDB = Database()
    guildID = str(ctx.message.guild.id)

    if serverDB[guildID]:
        savedChatID = serverDB.GetChatID(guildID)
        tempChannel = client.get_channel(int(savedChatID))
        if tempChannel == None:  # the saved chat id no longer exists
            channel = await ctx.guild.create_text_channel(name='🍞')
            serverDB.UpdateChatID(guildID, channel.id)
            await ctx.send("The 🍞 chat has been setup!")
        else:
            await ctx.send("The chat is already setup ya goof!")

    else:
        channel = await ctx.guild.create_text_channel(name='🍞')
        serverDB[guildID] = str(channel.id)

        await ctx.send("The 🍞 chat has been setup!")

    serverDB.conn.close()


@client.command(pass_context=True)
async def shuffle(ctx, playlistLink=""):
    """
    Shuffles the queue or shuffle a given playlist and adds it to queue.

    :param ctx:
    :param playlistLink:
    :return:
    """

    global voices

    global queues
    global currentGuildID

    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            voices[currentGuildID] = await channel.connect()

    if playlistLink != "":
        playlist = GetPlaylistUrls(playlistLink)
        random.shuffle(playlist)

        for x in playlist:
            queues[currentGuildID].append(x)

        if len(playlist) == len(queues[currentGuildID]):
            dequeue(currentGuildID)
        else:
            await UpdateToastPlayer(currentGuildID)

    else:
        tempQueue = queues[currentGuildID][1:]
        random.shuffle(tempQueue)
        queues[currentGuildID] = [queues[currentGuildID][0]] + tempQueue

        await UpdateToastPlayer(currentGuildID)


@client.command(pass_context=True)
async def remove(ctx, index):
    """
    Removes a specified song from the queue via queue number

    :param ctx:
    :param index:
    :return:
    """

    global queues
    global currentGuildID

    try:
        queues[currentGuildID].pop(int(index))
        await UpdateToastPlayer(currentGuildID)
    except:
        ctx.send("That number is not in the queue ya goof!")


@client.command(pass_context=True)
async def swap(ctx, index1, index2):
    """
    Swaps two indexes of the queue

    :param ctx:
    :param index1:
    :param index2:
    :return:
    """

    global queues
    global currentGuildID

    try:
        index1 = int(index1)
        index2 = int(index2)
        queues[currentGuildID][index1], queues[currentGuildID][index2] = queues[currentGuildID][index2], \
            queues[currentGuildID][index1]
        await UpdateToastPlayer(currentGuildID)
    except Exception as E:
        print(E)


@client.command(pass_context=True)
async def burger(ctx):
    """
    Burger, nough' said

    :param ctx:
    :return:
    """
    await ctx.send("🍞")
    await ctx.send("🍅")
    await ctx.send("🥬")
    await ctx.send("🥩")
    await ctx.send("🍞")


@client.command(pass_context=True)
async def join(ctx):
    global currentGuildID
    global voices

    """
    dwbi

    :param ctx:
    :return:
    """

    URL1 = "https://www.youtube.com/watch?v=jz40salowcc"

    URL2 = "https://www.youtube.com/watch?v=2Gu7j5ZgZw4"

    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            tempVoice = await channel.connect()

            playableLink = YouTube(URL1).streams.get_audio_only().url

            source = FFmpegPCMAudio(playableLink, **ffmpeg_param)
            tempVoice.play(source)


client.run(BOTTOKEN)
