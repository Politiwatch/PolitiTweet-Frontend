import tornado.ioloop
import tornado.web
import json
import database
import cache
from operator import itemgetter
import httplib
import html.parser

def unescape(text):
    return html.parser.HTMLParser().unescape(text)

def render(tweets):
    rendered = []
    for tweet in tweets:
        tweet["text"] = unescape(tweet["text"])
        rendered.append(tweet)
    return rendered

def httpsify(link):
    link.replace("http://", "https://", 1)

def injectHeaders(handler):
    if database.database_location.startswith("/home/"):  #linux
        handler.set_header("Content-Security-Policy", "upgrade-insecure-requests")


brand = "PolitiTweet"


class IndexHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", message=httplib.responses[status_code], error=status_code, brand=brand)
    def get(self):
        injectHeaders(self)
        deleted_tweets = database.getAllDeletedTweets()
        for tweet in deleted_tweets[:10]:
            tweet["user"] = database.getAccountFromDatabase(tweet["user"]["id"])
        self.render("pages/index.html", count=len(cache.accounts), brand=brand, latest=render(database.getLatestTweets()), deleted=render(deleted_tweets[:10]))
class DeletedHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", message=httplib.responses[status_code], brand=brand, error=status_code)
    def get(self):
        injectHeaders(self)
        deleted_tweets = database.getAllDeletedTweets()
        for tweet in deleted_tweets:
            tweet["user"] = database.getAccountFromDatabase(tweet["user"]["id"])
        self.render("pages/deleted.html", count=len(deleted_tweets), brand=brand, deleted=render(deleted_tweets))
class AboutHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", message=httplib.responses[status_code], brand=brand, error=status_code)
    def get(self):
        injectHeaders(self)
        self.render("pages/about.html", count=len(cache.accounts), brand=brand)
class FiguresHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", message=httplib.responses[status_code], brand=brand, error=status_code)
    def get(self):
        injectHeaders(self)
        figures = []
        for account in cache.accounts:
            if account is None:
                continue
            try:
                account["archive_url"] = "figure?account=" + str(account["id"])
                figures.append(account)
            except Exception as e:
                print(account)
                print(e)
                continue
        figures_sorted = sorted(figures, key=itemgetter('name'))
        deleted_tweets = database.getDeletedTweetsMap()
        for figure in figures_sorted:
            try:
                figure["deleted_tweets_length"] = len(deleted_tweets[str(figure["id"])])
            except KeyError:
                figure["deleted_tweets_length"] = 0
        self.render("pages/figures.html", figures=figures_sorted, brand=brand)
class FigureHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", message=httplib.responses[status_code], brand=brand, error=status_code)
    def get(self):
        injectHeaders(self)
        user = self.get_argument("account")
        account = cache.get_account(user)
        account["json"] = json.dumps(account)
        account["description"] = unescape(account["description"])
        account["deleted_tweets"] = database.getDeletedTweetsData(int(user))
        account["deleted_tweets_length"] = len(account["deleted_tweets"])
        if "retreived" in account:
            account["retrieved"] = account["retreived"] # to correct for a simple spelling error that is prevalent in database...
        self.render("pages/figure.html", brand=brand, figure=account)
class TweetsHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", brand=brand, message=httplib.responses[status_code], error=status_code)
    def get(self):
        injectHeaders(self)
        user = self.get_argument("account")
        deleted = bool(self.get_argument("deleted", default=False))
        tweets = []
        title = "Tweets of @"
        if deleted:
            title = "Deleted " + title
            tweets = database.getDeletedTweetsData(int(user))
        else:
            tweets = database.getAllTweetsInDatabase(int(user))
        last = int(self.get_argument("last", default=len(tweets)))
        account = cache.get_account(user)
        title = title + account["screen_name"]
        account["json"] = json.dumps(account)
        tweets_sorted = sorted(tweets, key=lambda tweet: int(tweet["id"]), reverse=True)
        self.render("pages/tweets.html", figure=account, brand=brand, title=title, statuses=render(tweets_sorted[:last]))
class TweetHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", brand=brand, message=httplib.responses[status_code], error=status_code)
    def get(self):
        injectHeaders(self)
        user = self.get_argument("account")
        tweet = self.get_argument("tweet")
        tweet_data = database.getTweet(user, tweet)
        account = cache.get_account(user)
        account["json"] = json.dumps(account)
        account["description"] = unescape(account["description"])
        account["deleted_tweets"] = database.getDeletedTweetsData(int(user))
        account["deleted_tweets_length"] = len(account["deleted_tweets"])
        tweet_data["json"] = json.dumps(tweet_data)
        tweet_data["text"] = unescape(tweet_data["text"])
        if "favorite_count" not in tweet_data:  # for some reason if =0 twitter omits favorite count
            tweet_data["favorite_count"] = 0
        if "retweet_count" not in tweet_data:  # for some reason if =0 twitter omits retweet count
            tweet_data["retweet_count"] = 0
        if "retreived" in tweet_data:
            tweet_data["retrieved"] = tweet_data["retreived"] # to fix a little typo that is prevalent in the database...
        self.render("pages/tweet.html", brand=brand, figure=account, tweet=tweet_data)
class ErrorHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        injectHeaders(self)
        self.render("pages/error.html", brand=brand, message=httplib.responses[status_code], error=status_code)
    def get(self):
        injectHeaders(self)
        self.render("pages/error.html", brand=brand, message="Page not found", error="404")
application = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/figures", FiguresHandler),
    (r"/about", AboutHandler),
    (r"/figure", FigureHandler),
    (r"/tweets", TweetsHandler),
    (r"/deleted", DeletedHandler),
    (r"/tweet", TweetHandler),
    (r'/static/(.*)$', tornado.web.StaticFileHandler, {'path': "pages/static"})
    ], default_handler_class=ErrorHandler)
if __name__ == "__main__":
    print "Loading tweets..."
    database.getAllDeletedTweets()
    print "Ready!"
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
