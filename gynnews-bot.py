#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser, logging, pickle, os.path
import random, requests, telepot, time, tweepy
from apscheduler.scheduler import Scheduler
from TOKEN import *
from bs4 import *

# Initializing logs for apschedule
logging.basicConfig()

parserConfig = configparser.ConfigParser()
parserConfig.read('bot.conf')

# TELEGRAM TOKENS
TELEGRAMKEY = str(parserConfig.get('TELEGRAM', 'KEY'))
TELEGRAMID = str(parserConfig.get('TELEGRAM', 'ID'))

# TWITTER TOKENS
TWITTERCONSUMERKEY = str(parserConfig.get('TWITTER', 'CONSUMERKEY'))
TWITTERCONSUMERSECRET = str(parserConfig.get('TWITTER', 'CONSUMERSECRET'))
TWITTERACCESSTOKEN = str(parserConfig.get('TWITTER', 'ACCESSTOKEN'))
TWITTERACCESSSECRET = str(parserConfig.get('TWITTER', 'ACCESSSECRET'))

config = {"botKey": KEY, "idChat": ID}
bot = telepot.Bot(config['botKey'])
chat = config['idChat']

def loadDatabase():
    global database
    global databaseFile
    try:
        with open(databaseFile) as f:
            database = pickle.load(f)
    except:
        database = []

def saveDatabase():
    global databaseFile
    global database
    with open(databaseFile, 'wb') as f:
        pickle.dump(database, f)

def checkTwitter(twitterUser):
    '''
    Check twitter accounts for the last 20 tweets
    - Arg1: twitter account
    '''
    global api
    # Recover last 20 tweets (default) without retweets
    tweets = api.user_timeline(screen_name = twitterUser,        
                            tweet_mode='extended',
                            include_rts = False)

    # Transverse tweets in reverse order
    for t in reversed(tweets):
        text = t.full_text
        # Check if the content is in the database
        if not text[:50] in database:
            # Check if there are images or videos
            if t.entities.has_key('media'):
                if t.entities['media'][0].has_key('media_url'):
                    img = t.entities['media'][0]['media_url']
                    bot.sendPhoto(chat, img, caption = text)
                else:
                    bot.sendMessage(chat, text)
            else:
                bot.sendMessage(chat, text)
            database.append(text[:50])
            saveDatabase()

def twitterAuth():
    '''
    Autenticate twitter account using bot.conf
    '''
    global api
    auth = tweepy.OAuthHandler(TWITTERCONSUMERKEY, TWITTERCONSUMERSECRET) 
    auth.set_access_token(TWITTERACCESSTOKEN, TWITTERACCESSSECRET)
    api = tweepy.API(auth)

def main():
    global databaseFile
    databaseFile = '.database'
    loadDatabase()
    twitterAuth()

    # Using a scheduler to check every 5 minutes for new tweets
    schd = Scheduler()
    schd.add_interval_job(checkTwitter, minutes = 2,  args = ['rmtcgoiania'])
    schd.start()

    # Keeping the main thread alive
    while True:
        time.sleep(100)

if __name__ == '__main__':
    main()
