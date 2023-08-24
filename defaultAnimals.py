from webexteamssdk import WebexTeamsAPI, ApiError
import json
import time
from pymongo import MongoClient


# Load config from the provided path
with open('/opt/gbb/config.json') as f:
    config = json.load(f)

# Map variables from the loaded config
dbusername = config['db_username']
dbpassword = config['db_password']
BOT_TOKEN = config['webex_bot_access_token']

# Set up the Webex Teams API client
api = WebexTeamsAPI(access_token=BOT_TOKEN)

# Get the bot's details using the token
bot_details = api.people.me()
BOT_ID = bot_details.id

client = MongoClient(f"mongodb://{dbusername}:{dbpassword}@localhost:27017/")
db = client['goodboy']
subscribers_collection = db['subscribers']

# Set default animal settings for existing subscribers
def set_default_animals():
    default_animals = {"dog": True, "cat": False, "capy": False}
    all_subscribers = subscribers_collection.find({})
    
    for subscriber in all_subscribers:
        roomId = subscriber.get('roomId')
        if roomId:  # just to be safe
            subscribers_collection.update_one(
                {"roomId": roomId},
                {"$set": {"animals": default_animals}},
                upsert=True  # This will insert if the record doesn't exist
            )

# Run this function once to update existing records
set_default_animals()