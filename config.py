from os import environ 

class Config:
    API_ID = int(environ.get("API_ID", ""))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "tjbot") 
    DATABASE_URI = environ.get("DATABASE_URI", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "forward-bot")
    BOT_OWNER = int(environ.get("BOT_OWNER", ""))



class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []

