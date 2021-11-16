import os
import pickle


def SaveServerInfo(serverData):
    with open("ServerData.dat", "wb") as file:
        pickle.dump(serverData, file)

def GetServerInfo():
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

def GetChatID(serverData : list, targetGuildID):
    for x in serverData:
        if (x['guildID'] == f'{targetGuildID}'):
            return x['chatID']

    return False

def UpdateChatID(serverData : list, targetGuildID, newChatID):
    for x in serverData:
        if (x['guildID'] == f'{targetGuildID}'):
            x['chatID'] = f'{newChatID}'


