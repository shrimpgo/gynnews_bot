# gynnews_bot
News from Goiania city - Brazil on Telegram Bot

## Dependencies

- The program was made in python 3.5, and all dependencies can be installed
  using `pip3` with the following command: 

`pip3 install -r requirements.txt`

### List of dependencies:

- APScheduler
- Tweepy
- Requests
- Telepot
- Beautifulsoup4
- Emoji

## Configuration file

- It is necessary to create a file called `bot.conf` with the following content: 

```
[TWITTER]
CONSUMERKEY = <consumer key>
CONSUMERSECRET = <consumer secret> 
ACCESSTOKEN = <twitter token>
ACCESSSECRET = <twitter secret>

[TELEGRAM]
KEY = <telegram token provided by botfather>
ID = <telegram channel id>
```
