# Bark - this is triggered by a cron (or manually if you like)
# and deals with sending batches of messages using the Teams API
# 
# TO DO: Weather delivery from DB if exists
#
import webexteamssdk # Import the whole thing

from pymongo import MongoClient
import os
import json
from concurrent.futures import ThreadPoolExecutor
import time

# Go get secrets from the config
with open('/opt/gbb/config.json') as f:
    config = json.load(f)

# Map some variables from the loaded config
dbusername = config['db_username']
dbpassword = config['db_password']
BOT_TOKEN = config['webex_bot_access_token']
# Set up connection to MongoDB
client = MongoClient(f"mongodb://{dbusername}:{dbpassword}@localhost:27017/")
db = client['goodboy']
subscribers_collection = db['subscribers']


def get_dog_image():
    return "https://goodboy.robot64.com/fetch/dog.jpg"


def get_breed_and_goodness_score():
    with open('/var/www/goodboy.robot64.com/fetch/breed.txt', 'r') as file:
        breed = file.readline().strip()
        goodness_score = file.readline().strip()
    return breed, goodness_score

# An attempt at threading - this has a try except which handles a 429 backoff from the API
# This is a single 'thread' of 15 which is fired off from another daily good boy function below
def send_message(subscriber):
    room_id = subscriber['roomId']
    image_url = get_dog_image() 
    breed, goodness_score = get_breed_and_goodness_score()
    card_content = {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🦴🗞️ Good Boy Delivery!",
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "Image",
                    "url": "https://goodboy.robot64.com/fetch/dog.jpg"
                },
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": f"Breed: {breed}",
                                    "wrap": True,
                                    "size": "Small",
                                    "weight": "Bolder",
                                    "color": "Good"
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": f"GoodBoy Rating©: {goodness_score}/10",
                                    "wrap": True,
                                    "size": "Small",
                                    "weight": "Bolder",
                                    "color": "Good",
                                    "isSubtle": False,
                                    "horizontalAlignment": "Right"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "More commands: Help, Unsubscribe, Bark, Woof",
                    "wrap": True,
                    "separator": True,
                    "weight": "Default",
                    "color": "Accent",
                    "isSubtle": True,
                    "size": "Small",
                    "fontType": "Monospace",
                    "spacing": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": "Image credit: Dog CEO's Dog API",
                    "wrap": True,
                    "size": "Small",
                    "spacing": "Small",
                    "weight": "Lighter",
                    "color": "Default",
                    "isSubtle": True,
                    "fontType": "Monospace"
                },
                {
                    "type": "TextBlock",
                    "text": "Feedback: Ping Matt",
                    "wrap": True,
                    "spacing": "Small",
                    "fontType": "Monospace",
                    "size": "Small",
                    "weight": "Lighter",
                    "color": "Warning",
                    "isSubtle": True
                }
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
        }

    try:
        api.messages.create(
            roomId=room_id,
            markdown=f"Bark! Bark!",
            attachments=[
                {"contentType": "application/vnd.microsoft.card.adaptive", "content": card_content}
            ]
        )
    except webexteamssdk.exceptions.ApiError as e:
        if e.response_code == 429:
            retry_after = int(e.response_headers['Retry-After'])
            print(f"Rate limited, retrying after {retry_after} seconds")
            time.sleep(retry_after)
            return send_message(subscriber)  # Recursively retry the same subscriber
        else:
            print(f"Error sending message: {e}")
            return None

    return subscriber




# This sets up 15 workers which individually start a thread of sendMessage defined above
def send_daily_good_boy():
    subscribers = subscribers_collection.find()
    image_url = get_dog_image()
    breed, goodness_score = get_breed_and_goodness_score()

    # Define the number of workers for the ThreadPoolExecutor
    workers = 15

    # Use a ThreadPoolExecutor to send messages in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(send_message, subscribers))


api = webexteamssdk.WebexTeamsAPI(access_token=BOT_TOKEN)
send_daily_good_boy()
