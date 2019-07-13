#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser, logging, pickle, os.path, json
import random, re, requests, telepot, time, tweepy
from apscheduler.scheduler import Scheduler
from bs4 import *
from emoji import emojize

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

    msg = '*PREVISÃO DO TEMPO EM GOIÂNIA*\n\n'.decode('utf-8')
    for i in range(3):
        msg += '*' + re.sub('\s+', ' ', title[i].text) + ':*\n'
        msg += '_Mínima: _'.decode('utf-8') + minW[i].text + '\n'
        msg += '_Máxima: _'.decode('utf-8') + maxW[i].text + '\n'
        msg += ' - ' + descriptions[i].text.strip() + '\n\n'

    bot.sendMessage(chat, msg + tail, parse_mode='Markdown')

def checkQuotation():
    '''
    Check last dolar quotation and BTC to Real BR from economia.awesomeapi.com.br
    '''
    global databaseFile
    tail = '\n#awesomeapi'
    url = 'https://economia.awesomeapi.com.br/all'
    ua = random.choice(loadUA())
    req = requests.get(url , headers={'User-Agent': ua})
    reqj = req.json()

    msg = ':money-mouth_face: *COTAÇÃO DE MOEDAS* :money-mouth_face:\n\n'.decode('utf-8')
    for i in ['USD','USDT','BTC']:
        if i == 'BTC':
            msg += '*' + reqj[i]['name'] + ':* :moneybag:\n'
            msg += '_Compra:_ R$ '.decode('utf-8') + reqj[i]['bid'] + '\n'
            msg += '_Venda:_ R$ '.decode('utf-8') + reqj[i]['ask'] + '\n'
            msg += '_Variação:_ R$ '.decode('utf-8') + reqj[i]['varBid'] + '\n\n'
        else:
            msg += '*' + reqj[i]['name'] + ':* :dollar:\n'
            msg += '_Compra:_ R$ '.decode('utf-8') + reqj[i]['bid'].replace('.',',') + '\n'
            msg += '_Venda:_ R$ '.decode('utf-8') + reqj[i]['ask'].replace('.',',') + '\n'
            msg += '_Variação:_ R$ '.decode('utf-8') + reqj[i]['varBid'].replace('.',',') + '\n\n'

    Message = bot.sendMessage(chat, emojize(msg, use_aliases=True) + tail, parse_mode='Markdown')
    bot.pinChatMessage(chat, Message['message_id'], disable_notification=True)

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

    # Scheduler for any different task
    schd = Scheduler()
    '''
    Using a scheduler to check every 5 minutes for new tweets. If you want to add more twitter's profile, just follow example below:

    schd.add_interval_job(checkTwitter, minutes = MIN,  args = ['profile'])
    '''
    schd.add_interval_job(checkTwitter, minutes = 5,  args = ['rmtcgoiania'])
    schd.add_interval_job(checkTwitter, minutes = 5,  args = ['jornalopcao'])
    ## Using a scheduler to get every 6 hours and 16 hours informations about weather
    schd.add_cron_job(checkWeather, hour='6,16', minute=00)
    ## Using a scheduler to get every 6 hours and 16 hours informations about quotation
    schd.add_cron_job(checkQuotation, hour='8,14', minute='00')
    schd.start()

    # Keeping the main thread alive
    while True:
        time.sleep(300)

if __name__ == '__main__':
    main()
