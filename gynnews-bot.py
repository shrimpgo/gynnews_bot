#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser, logging, pickle, os.path
import random, re, requests, telepot, time, tweepy
from apscheduler.scheduler import Scheduler
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

bot = telepot.Bot(TELEGRAMKEY)
chat = TELEGRAMID

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

def loadUA():
    uas = []
    with open("user-agents.txt", 'rb') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[0:-1-0])
    random.shuffle(uas)
    return uas

def checkWeather():
    '''
    Check weather in Goiania from www.climatempo.com.br
    '''
    global databaseFile
    tail = '\n#climatempo'
    url = 'https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/88/goiania-go'
    ua = random.choice(loadUA())
    req = requests.get(url , headers={'User-Agent': ua})
    soup = BeautifulSoup(req.content, 'html.parser')
    title = soup.findAll('p', {'class':'left top10 bold font12 txt-darkgray medium-8'})
    descriptions = soup.findAll('div', {'class':'columns small-12 medium-12 description-block'})
    maxW = soup.findAll('p', {'arial-label':'temperatura máxima'})
    minW = soup.findAll('p', {'arial-label':'temperatura mínima'})

    msg = 'PREVISÃO DO TEMPO EM GOIÂNIA\n\n'.decode('utf-8')
    for i in range(3):
        msg += re.sub('\s+', ' ', title[i].text) + ':\n'
        msg += ' - Mínima: '.decode('utf-8') + minW[i].text + '\n'
        msg += ' - Máxima: '.decode('utf-8') + maxW[i].text + '\n'
        msg += ' - ' + descriptions[i].text.strip() + '\n\n'

    bot.sendMessage(chat, msg + tail)

def checkTwitter(twitterUser):
    '''
    Check twitter accounts for the last 20 tweets
    - Arg1: twitter account
    '''
    global api
    tail = '\n#' + twitterUser
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
                    bot.sendPhoto(chat, img, caption = text + tail)
                else:
                    bot.sendMessage(chat, text + tail)
            else:
                bot.sendMessage(chat, text + tail)
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

    # # Using a scheduler to check every 5 minutes for new tweets
    schd = Scheduler()
    schd.add_interval_job(checkTwitter, minutes = 5,  args = ['rmtcgoiania'])
    schd.add_interval_job(checkWeather, hours = 6)
    schd.start()

    # Keeping the main thread alive
    while True:
        time.sleep(300)

if __name__ == '__main__':
    main()
