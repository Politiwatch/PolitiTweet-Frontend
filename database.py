from time import gmtime, strftime
import json
import os
from database import *

config_location = "configs/database.config.json"
config = json.load(open(config_location, "r"))

database_location = config["databaseLocation"]


def time():
    return strftime("%Y-%m-%d--%H-%M-%S", gmtime())


def getLatestTweets():
    latest = []
    if os.path.exists(database_location + "latest.json"):
        with open(database_location + "latest.json", "r") as datafile:
            latest = json.load(datafile)
    return latest

def writeLatestTweet(diction):
    latest = [diction]
    latest.extend(getLatestTweets())
    latest = sorted(latest, key=lambda k: k["id"], reverse=True)
    with open(database_location + "latest.json", "w") as datafile:
        json.dump(latest[:50], datafile)


def initializeAccountData(id):
    if not os.path.exists(database_location +
                          "accounts/" + str(id)):
        os.mkdir(database_location + "accounts/" + str(id))
    if not os.path.exists(database_location +
                          "accounts/" + str(id) + "/archive/"):
        os.mkdir(database_location + "accounts/" + str(id) + "/archive/")


def hasTweetArchive(id):
    return os.path.exists(database_location +
                          "accounts/" + str(id) + "/tweets/")

def markTweetAsDeleted(userid, tweetid):
    data = []
    with open(database_location + "accounts/" + str(userid) + "/tweets/" + str(tweetid) + ".json", "r") as tweetfile:
        data = json.load(tweetfile)
    data["deleted"] = True
    with open(database_location + "accounts/" + str(userid) + "/tweets/" + str(tweetid) + ".json", "w") as tweetfile:
        json.dump(data, tweetfile)
    deleted = {}
    userid = str(userid)
    tweetid = int(tweetid)
    if os.path.exists(database_location + "deleted.json"):
        with open(database_location + "deleted.json", "r") as deleted_file:
            deleted = json.load(deleted_file)
    if userid in deleted.keys():
        if tweetid not in deleted[userid]:
            deleted[userid].append(tweetid)
    else:
        deleted[userid] = [tweetid]
    with open(database_location + "deleted.json", "w") as deleted_file:
        json.dump(deleted, deleted_file)


def getTweet(userid, tweetid):
    with open(database_location + "accounts/" + str(userid) + "/tweets/" + str(tweetid) + ".json", "r") as tweetfile:
        data = json.load(tweetfile)
        if "deleted" not in data:
            data["deleted"] = False  # edge cases
        if "retrieved" not in data and "retreived" not in data:
            data["retrieved"] = "n/a"
        return data


def initializeTweetArchive(id):
    if not os.path.exists(database_location +
                          "accounts/" + str(id) + "/tweets/"):
        os.mkdir(database_location + "accounts/" + str(id) + "/tweets/")


def getAccountFromDatabase(id):
    if os.path.exists(database_location +
                          "accounts/" + str(id) + "/account.json"):
        with open(database_location + "accounts/" + str(id) +
                  "/account.json", "r") as account_file:
            data = json.load(account_file)
            metadata = getAccountMetadata(id)
            for key in metadata.keys():
                data[key] = metadata[key]
            if "deleted" not in data:
                data["deleted"] = False # edge cases
            if "url" not in data:
                data["url"] = "https://twitter.com/" + data["screen_name"] # edge cases
            return data


def hasAccountData(id):
    return os.path.exists(database_location + "accounts/" +
                          str(id) + "/account.json")

deleted_tweet_data = {}

def getAllDeletedTweets():
    deleted = getDeletedTweetsMap()
    tweet_data = []
    for user in deleted.keys():
        for tweet in deleted[user]:
            if str(user) not in deleted_tweet_data:
                deleted_tweet_data[str(user)] = {str(tweet): getTweet(user, tweet)}
            if str(user) in deleted_tweet_data and str(tweet) not in deleted_tweet_data[str(user)]:
                deleted_tweet_data[str(user)][str(tweet)] = getTweet(user, tweet)
            data = deleted_tweet_data[str(user)][str(tweet)]
            if "user" not in data or "profile_image_url" not in data["user"]:
                data["user"] = getAccountFromDatabase(user)
                print(data["user"])
                deleted_tweet_data[str(user)][str(tweet)] = data
            tweet_data.append(deleted_tweet_data[str(user)][str(tweet)])
    tweets = sorted(tweet_data, key=lambda k: int(k["id"]), reverse=True)
    return tweets

def getDeletedTweets(id):
    deleted = getDeletedTweetsMap()
    if str(id) in deleted:
        return deleted[str(id)]
    return []

def getDeletedTweetsData(id):
    ids = getDeletedTweets(id)
    data = [getTweet(id, tweet) for tweet in ids]  # I think i'm starting to get the hang of this
    return data

def getDeletedTweetsMap():
    deleted = {}
    if os.path.exists(database_location + "deleted.json"):
        with open(database_location + "deleted.json", "r") as deleted_file:
            deleted = json.load(deleted_file)
    return deleted


def getAllAccountsInDatabase():
    accounts = []
    for directory in os.listdir(database_location + "accounts/"):
        if directory.startswith("."):
            continue
        accounts.append(int(directory))
    return accounts


def writeAccountToDatabase(account):
    with open(database_location + "accounts/" + str(account.id) +
              "/account.json", "w") as account_file:
        account_file.write(account.AsJsonString())


def writeAccountMetadata(id, metadata):
    with open(database_location + "accounts/" + str(id) +
              "/metadata.json", "w") as meta_file:
        json.dump(metadata, meta_file)


def hasAccountMetadata(id):
    return os.path.exists(database_location + "accounts/" + str(id) +
                          "/metadata.json")

def writeTweet(account, tweet_id, jsondata):
    initializeTweetArchive(account)
    with open(database_location + "accounts/" + str(account) + "/tweets/" + str(tweet_id) + ".json", "w") as tweet_archive:
        data = json.loads(jsondata)
        data["retrieved"] = time()
        json.dump(data, tweet_archive)


def getHighestLowestArchivedStatus(id):
    lowest_archived_status = -1  # for the max_id parameter for subsequent searches
    highest_archived_status = -1
    for dirname, dirnames, filenames in os.walk(database_location + "accounts/" + str(id) + "/tweets/"):
        for filename in filenames:
            try:
                status = int(filename.replace(".json", ""))  # could be cleaner but it'll do
                if status < lowest_archived_status or lowest_archived_status == -1:
                    lowest_archived_status = status
                if status > highest_archived_status or highest_archived_status == -1:
                    highest_archived_status = status
            except Exception:
                pass
                # is a .file
    return [highest_archived_status, lowest_archived_status]


def getAllTweetsInDatabase(id):
    tweets = []
    for dirname, dirnames, filenames in os.walk(database_location + "accounts/" + str(id) + "/tweets/"):
        for filename in filenames:
            try:
                tweets.append(getTweet(id, int(filename.replace(".json", ""))))
            except Exception:
                pass
                # is a .file
    return tweets


def getAccountMetadata(id):
    if not hasAccountMetadata(id):
        return {}
    with open(database_location + "accounts/" + str(id) +
              "/metadata.json", "r") as meta_file:
        return json.load(meta_file)


def archiveAccountData(account):
    if not os.path.exists(database_location + "accounts/" + str(account.id) + "/archive/"):
        os.mkdir(database_location + "accounts/" + str(account.id) + "/archive/")
    with open(database_location + "accounts/" + str(account.id) + "/archive/" + time() + ".json", "w") as archive_file:
        archive_file.write(account.AsJsonString())


def getFollowing():
    return json.load(open(database_location + "following.json", "r"))

def hasFollowingData():
    return os.path.exists(database_location + "following.json")

def writeFollowingData(following):
    with open(database_location + "following.json", "w") as f:
        json.dump(following, f)

"""
Clean all tweets in database.
"""
def cleanAllTweets():
    total = len(os.listdir(database_location + "accounts/"))
    ind = 0.0
    affected = 0
    for dirname in os.listdir(database_location + "accounts/"):
        if dirname.startswith("."):
            continue
        ind += 1.0
        print(str(ind/total*100) + "%: " + dirname)
        try:
            for filename in os.listdir(database_location + "accounts/" + dirname+"/tweets/"):
                try:
                    if filename.startswith("."):
                        continue
                    with open(database_location + "accounts/" + dirname+"/tweets/" + filename, "r") as tweet:
                        #print("Scanning " + database_location + "accounts/" + dirname+"/tweets/" + filename)
                        twdata = json.load(tweet)
                        if "deleted" not in twdata.keys() or "retrieved" not in twdata.keys():
                            if "deleted" not in twdata.keys():
                                twdata["deleted"] = False
                            if "retrieved" not in twdata.keys():
                                twdata["retrieved"] = time()
                            if "retreived" in twdata.keys():
                                del twdata["retreived"]
                            with open(database_location + "accounts/" + dirname+"/tweets/" + filename, "w") as tweet_write:
                                json.dump(twdata, tweet_write)
                            affected += 1
                            print("Cleaned tweet " + twdata["id_str"])
                except Exception as e:
                    print(e)
                    continue
        except Exception as e:
            print(e)
            continue
        #except Exception as exception:
        #    print("Error: " + str(exception))
    print("Cleaned " + str(affected) + " tweets.")

"""
Collect all media!
"""
def findAllMediaInDatabase(debug=True):
    media = []
    total = len(os.listdir(database_location + "accounts/"))
    ind = 0.0
    for dirname in os.listdir(database_location + "accounts/"):
        if dirname.startswith("."):
            continue
        ind += 1.0
        print(str(ind/total*100) + "%: " + dirname)
        try:
            for filename in os.listdir(database_location + "accounts/" + dirname+"/tweets/"):
                try:
                    if filename.startswith("."):
                        continue
                    with open(database_location + "accounts/" + dirname+"/tweets/" + filename, "r") as tweet:
                        #print("Scanning " + database_location + "accounts/" + dirname+"/tweets/" + filename)
                        twdata = json.load(tweet)
                        if "media" in twdata.keys():
                            i = 0
                            for item in twdata["media"]:
                                media.append(twdata["media"][i]["media_url_https"])
                                if debug:
                                    print(str(ind/total*100) + "%:   ...found media: " + twdata["media"][i]["media_url_https"])
                                i += 1
                except Exception as e:
                    print(e)
                    continue
        except Exception as e:
            print(e)
            continue
        #except Exception as exception:
        #    print("Error: " + str(exception))
    print("Found " + str(len(media)) + " pieces of media.")
    if os.path.exists(database_location + "media.json"):
        with open(database_location + "media.json", "r") as media_file:
            media_old = json.load(media_file)
            for item in media_file:
                if item not in media:
                    media.append(item)
    with open(database_location + "media.json", "w") as media_file:
        json.dump(media, media_file)
    return media

def markAsHasDeletedTweet(id):
    metadata = getAccountMetadata(id)
    metadata["has_deleted_tweet"] = True
    writeAccountMetadata(id, metadata)

def retreiveAllStatusesFromDatabase(id):
    statuses = []
    if os.path.exists(database_location + "accounts/" + str(id) + "/tweets/"):
        for dirname, dirnames, filenames in os.walk(database_location + "accounts/" + str(id) + "/tweets/"):
            for filename in filenames:
                if filename.startswith("."):
                    continue
                try:
                    fp = database_location + "accounts/" + str(id) + "/tweets/" + filename
                    with open(fp, "r") as tweetfile:
                        statuses.append(json.load(tweetfile))
                except Exception:
                    print("Error: " + str(exception))
    return statuses
