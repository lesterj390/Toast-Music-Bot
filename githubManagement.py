import boto
import os
import git

try:
    from apikeys import *
except:
    pass

try:
    from boto.s3.connection import S3Connection

    s3 = S3Connection(os.environ['GHTOKEN'])

    GHTOKEN = os.environ['GHTOKEN']
except:
    pass

LINK = f"https://lesterj390:{GHTOKEN}@github.com/lesterj390/Toast-Bot.git"

PATH = os.path.join(os.getcwd(), "data")

if not os.path.isdir(PATH):
    repo = git.Repo.clone_from(LINK, 'data')
else:
    repo = git.Repo(PATH)


def UploadServerData():
    repo.git.add(os.path.join(PATH, "serverData.dat"))
    repo.index.commit("herokuServerDataUpdate")
    origin = repo.remote('origin')
    origin.push()


def DownloadServerData():
    try:
        repo.git.checkout('HEAD', '--', 'serverData.dat')
        return True
    except:
        return False
