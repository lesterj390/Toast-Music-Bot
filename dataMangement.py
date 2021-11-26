import os
import pickle

from githubManagement import *


def SaveServerInfo(serverData):
    """
    This function saves the servers info on which chat is prefixless to a file.

    :param serverData:
    :return:
    """
    with open(os.path.join(PATH, "serverData.dat"), "wb") as file:
        pickle.dump(serverData, file)

    UploadServerData()




def GetServerInfo():
    """
    This function opens the servers info of prefixless chats and returns it.

    :return serverData:
    """

    if DownloadServerData() is False:
        return False

    if not os.path.isfile(os.path.join(PATH, "serverData.dat")):
        file = open(os.path.join(PATH, "serverData.dat"), "x")
        file.close()
    else:
        file = open(os.path.join(PATH, "serverData.dat"), "rb")

    try:
        serverData = pickle.load(file)
        file.close()
    except:
        return False

    return serverData


def GetChatID(serverData: list, targetGuildID):
    """
    This function uses the serverData array and targetGuildID (server id)
    number to get the id of the prefixless channel.

    :param serverData:
    :param targetGuildID:
    :return:
    """

    if serverData is not False:
        for x in serverData:
            if (x['guildID'] == f'{targetGuildID}'):
                return int(x['chatID'])

    return False


def UpdateChatID(serverData: list, targetGuildID, newChatID):
    """
    This function uses the serverData array, the targetGuildID (server id) and the
    newChatID to update the prefixless channel id in the event it gets remade.

    :param serverData:
    :param targetGuildID:
    :param newChatID:
    :return:
    """
    for x in serverData:
        if (x['guildID'] == f'{targetGuildID}'):
            x['chatID'] = f'{newChatID}'
