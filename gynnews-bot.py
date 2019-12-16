#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser, logging, pickle, os.path, json
import random, re, requests, telepot, time, tweepy
from apscheduler.schedulers.background import BlockingScheduler
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

# CLIMATEMPO TOKEN
CTKEY = str(parserConfig.get('CLIMATEMPO', 'TOKEN'))

bot = telepot.Bot(TELEGRAMKEY)
chat = TELEGRAMID

def loadDatabase():
    global database
    global databaseFile
    try:
        f = open(databaseFile, encoding='8859').read()
        database = pickle.loads(bytes(f, encoding='8859'))
    except:
        database = []

def saveDatabase():
    global databaseFile
    global database
    f = open(databaseFile, 'wb')
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
    Check weather in Goiania from apiadvisor.climatempo.com.br

    Create your token: https://advisor.climatempo.com.br
    Documentation: http://apiadvisor.climatempo.com.br/doc/index.html#api-Forecast-Forecast15DaysByCity
    '''
    ico = {'1':':sunny:',
            '2':':white_sun_with_small_cloud:',
            '2r':':white_sun_behind_cloud:',
            '3':':cloud_with_rain:', 
            '3tm':':cloud:',
            '4':':white_sun_behind_cloud_with_rain:',
            '4r':':white_sun_behind_cloud_with_rain:',
            '4t':':white_sun_behind_cloud_with_rain: :cloud_with_lightning:',
            '5':':cloud_with_rain:',
            '6':':thunder_cloud_and_rain:',
            '9':':white_sun_with_small_cloud:' }
    global databaseFile
    tail = '\n#climatempo'
    url = 'http://apiadvisor.climatempo.com.br/api/v1/forecast/locale/6861/days/15?token=' + CTKEY
    ua = random.choice(loadUA())
    req = requests.get(url , headers={'User-Agent': ua})
    data = json.loads(req.text)

    msg = ':sunny: *PREVISÃO DO TEMPO EM GOIÂNIA* :umbrella_with_rain_drops:\n\n'
    for i in range(3):
        msg += '*' +  'Dia ' + data['data'][i]['date_br'] + ':*\n'
        msg += '*Temperatura:* :thermometer:\n'
        msg += '· ' + '_Mín: _' + str(data['data'][i]['temperature']['min']) + '° C' + '\n'
        msg += '· ' + '_Máx: _' + str(data['data'][i]['temperature']['max']) + '° C' + '\n'
        msg += '*Umidade do Ar:* :droplet:\n'
        msg += '· ' + '_Mín: _' + str(data['data'][i]['humidity']['min']) + '%' + '\n'
        msg += '· ' + '_Máx: _' + str(data['data'][i]['humidity']['max']) + '%' + '\n'
        msg += ' - ' + data['data'][i]['text_icon']['text']['phrase']['reduced'] + ' ' + ico[data['data'][i]['text_icon']['icon']['day']] + '\n\n'

    bot.sendMessage(chat, emojize(msg, use_aliases=True) + tail, parse_mode='Markdown')

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

    msg = ':money-mouth_face: *COTAÇÃO DE MOEDAS* :money-mouth_face:\n\n'
    for i in ['USD','USDT','BTC']:
        if i == 'BTC':
            msg += '*' + reqj[i]['name'] + ':* :moneybag:\n'
            msg += '_Compra:_ R$ ' + reqj[i]['bid'] + '\n'
            msg += '_Venda:_ R$ ' + reqj[i]['ask'] + '\n'
            msg += '_Variação:_ R$ ' + reqj[i]['varBid'] + '\n\n'
        else:
            msg += '*' + reqj[i]['name'] + ':* :dollar:\n'
            msg += '_Compra:_ R$ ' + reqj[i]['bid'].replace('.',',') + '\n'
            msg += '_Venda:_ R$ ' + reqj[i]['ask'].replace('.',',') + '\n'
            msg += '_Variação:_ R$ ' + reqj[i]['varBid'].replace('.',',') + '\n\n'

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
            if 'media' in t.entities:
                if 'media_url' in t.entities['media'][0]:
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
    schd = BlockingScheduler()
    '''
    Using a scheduler to check every 5 minutes for new tweets. If you want to add more twitter's profile, just follow example below:

    schd.add_interval_job(checkTwitter, minutes = MIN,  args = ['profile'])
    '''
    schd.add_job(checkTwitter, 'interval', minutes = 5,  args = ['rmtcgoiania'])
    schd.add_job(checkTwitter, 'interval', minutes = 5,  args = ['jornalopcao'])
    ## Using a scheduler to get every 6 hours and 16 hours informations about weather
    schd.add_job(checkWeather, 'cron', hour='6,16', minute=00)
    ## Using a scheduler to get every 6 hours and 16 hours informations about quotation
    schd.add_job(checkQuotation, 'cron', hour='8,14', minute=00)
    schd.start()

    # Keeping the main thread alive
    while True:
        time.sleep(300)

if __name__ == '__main__':
    main()
