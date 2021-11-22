import os
import pickle


def SaveServerInfo(serverData):
    """
    This function saves the servers info on which chat is prefixless to a file.

    :param serverData:
    :return:
    """
    with open("ServerData.dat", "wb") as file:
        pickle.dump(serverData, file)


def GetServerInfo():
    """
    This function opens the servers info of prefixless chats and returns it.

    :return serverData:
    """

    if not os.path.isfile("ServerData.dat"):
        file = open("ServerData.dat", "x")
        file.close()
    else:
        file = open("ServerData.dat", "rb")

    try:
        serverData = pickle.load(file)
    except:
        file.close()
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
