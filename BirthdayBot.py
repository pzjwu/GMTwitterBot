import tweepy
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re
from secret import consumer_key, consumer_secret, access_secret, access_token, handle

def twitter_api():
    twitter_api_key = consumer_key
    twitter_api_key_secret = consumer_secret
    twitter_access_token = access_token
    twitter_access_token_secret = access_secret
    auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_key_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    twitter_api = tweepy.API(auth)
    return twitter_api

# log into the API
api = tweepy.API(twitter_api().auth)
print('[{}] Logged into Twitter API as @{}\n-----------'.format(
    datetime.now().strftime("%H:%M:%S %Y-%m-%d"),
    handle
))

# string array of words that will trigger the on_status function
trigger_words = [
    '@' + handle # respond to @mentions
]


def get_celeb(url):
    # get name
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    celeb_data = {}

    celebrity_element = soup.find("a", "face face person-item")
    celebrity_name_and_age = celebrity_element.find("div", "name").text
    comma_position = celebrity_name_and_age.find(",")
    lengthCeleb = len(celebrity_name_and_age)
    celebrity_age = celebrity_name_and_age[comma_position + 2: lengthCeleb - 1]
    check_age = int(celebrity_age) % 10
    if(check_age == 0 or check_age == 4 or check_age == 5 or check_age == 6 or check_age == 7 or check_age == 8 or check_age == 9):
        celebrity_age = str(celebrity_age + 'th')
    elif(check_age == 1):
        celebrity_age = str(celebrity_age + 'st')
    elif(check_age == 2):
        celebrity_age = str(celebrity_age + 'nd')
    elif(check_age == 3):
        celebrity_age = str(celebrity_age + 'rd')
    celebrity_broken = celebrity_name_and_age[:comma_position]
    celebrity_name = celebrity_broken.replace("\n", "")
    celeb_data["NAME"] = celebrity_name
    celeb_data["AGE"] =celebrity_age

    # get image url
    celebrity_image_url_unshortened = celebrity_element.attrs["style"]
    celebrity_image_url_wp = re.findall(r"(?P<url>https?://[^\s]+)", celebrity_image_url_unshortened)
    celebrity_image_url = celebrity_image_url_wp[0].replace(')', '')
    celeb_data["URL"] = celebrity_image_url

    return celeb_data


def prepare_media_for_upload(celeb_image_url):
    # download image of celeb (from URL)
    response = requests.get(celeb_image_url, stream=True)
    with open("images/celeb.jpg", "wb") as celeb_img:
        celeb_img.write(response.content)

    # create media ids
    filename = "images/celeb.jpg"
    media_id = []
    res = twitter_api().media_upload(filename)
    media_id.append(res.media_id)

    return media_id


def format_for_tweet(celeb_name, celeb_age):
    tweet_str = f"Happy Birthday {celeb_name}! GM wishes you a great {celeb_age} birthday!"
    return tweet_str

# override the default listener to add code to on_status
class MyStreamListener(tweepy.StreamListener):

    # listener for tweets
    # -------------------
    # this function will be called any time a tweet comes in
    # that contains words from the array created above
    def on_status(self, status):

        # log the incoming tweet
        print('[{}] Received: "{}" from @{}'.format(
            datetime.now().strftime("%H:%M:%S %Y-%m-%d"),
            status.text,
            status.author.screen_name
        ))

        # get the text from the tweet mentioning the bot.
        # for this bot, we won't need this since it doesn't process the tweet.
        # but if your bot does, then you'll want to use this
        message = status.text

        celeb_data_today = get_celeb("https://www.famousbirthdays.com/")
        final_tweet = format_for_tweet(celeb_data_today["NAME"],celeb_data_today["AGE"])
        print(final_tweet)
        twitter_api().update_status(status=final_tweet, media_ids=prepare_media_for_upload(celeb_data_today['URL']))

        print('[{}] Responded to @{}'.format(
            datetime.now().strftime("%H:%M:%S %Y-%m-%d"),
            status.author.screen_name
        ))

# create a stream to receive tweets
try:
    streamListener = MyStreamListener()
    stream = tweepy.Stream(auth = api.auth, listener=streamListener)
    stream.filter(track=trigger_words)
except KeyboardInterrupt:
    print('\nGoodbye')