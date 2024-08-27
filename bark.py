# Bark - this is triggered by a cron (or manually if you like)
# and deals with sending batches of messages using the Teams API
# 
# Now handles a card as a function, and can do cat or capy as well as dog
#
# TO DO: Weather delivery from DB if exists
#
import webexteamssdk
from pymongo import MongoClient
import os
import json
from concurrent.futures import ThreadPoolExecutor
import time
import os
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

# Go get secrets from the config
with open(config_path) as f:
    config = json.load(f)

# Map some variables from the loaded config
dbusername = config['db_username']
dbpassword = config['db_password']
BOT_TOKEN = config['webex_bot_access_token']

client = MongoClient(f"mongodb://{dbusername}:{dbpassword}@localhost:27017/")
db = client['goodboy']
subscribers_collection = db['subscribers']

def get_image(animal_type):
    return f"https://goodboy.robot64.com/fetch/{animal_type}.jpg"

def get_breed_and_score(animal_type):
    score_type = "GoodBoy" if animal_type == 'dog' else "Cattitude" if animal_type == 'cat' else "Chill"
    credit = "Dog.CEO API" if animal_type == 'dog' else "TheCatAPI.com" if animal_type == 'cat' else "Capy.lol API"
    with open(f'/var/www/goodboy/fetch/{animal_type}.txt', 'r') as file:
        breed = file.readline().strip()
        score = file.readline().strip()
    return breed, score, score_type, credit

def get_dog_image():
    return "https://goodboy.robot64.com/fetch/dog.jpg"

def get_breed_and_goodness_score():
    with open('/var/www/goodboy/fetch/breed.txt', 'r') as file:
        breed = file.readline().strip()
        goodness_score = file.readline().strip()
    return breed, goodness_score

def generate_card(animal_type, breed, goodness_score, score_type, image_url, credit="Unknown"):
    return {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "TextBlock",
                "text": f"🦴🗞️ {animal_type.capitalize()} Delivery!",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "Image",
                "url": image_url
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
                                "text": f"Info: {breed}",
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
                                "text": f"{score_type.capitalize()} Rating©: {goodness_score}/10",
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
                "text": f"Image credit: {credit}",
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

def send_message(subscriber):
    room_id = subscriber['roomId']
    animal_subscriptions = subscriber.get('animals', {})
    print(f"Room ID: {room_id}")
    print(f"Animal Subscriptions: {animal_subscriptions}")

    card_content = None  # Initialize the variable to None
    messages_sent = 0  # Initialize counter for sent messages

    for animal_type, is_subscribed in animal_subscriptions.items():
        if is_subscribed:
            print(f"Sending for {animal_type}")  # Debug print

            image_url = get_image(animal_type)
            breed, score, score_type, credit = get_breed_and_score(animal_type)
            card_content = generate_card(animal_type, breed, score, score_type, image_url, credit)

            try:
                api.messages.create(
                    roomId=room_id,
                    markdown=f"{animal_type.capitalize()} Alert!",
                    attachments=[
                        {"contentType": "application/vnd.microsoft.card.adaptive", "content": card_content}
                    ]
                )
                messages_sent += 1  # Increment the sent messages counter
            except webexteamssdk.exceptions.ApiError as e:
                if e.response_code == 429:
                    retry_after = int(e.response_headers['Retry-After'])
                    print(f"Rate limited, retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    return send_message(subscriber)  # Recursively retry the same subscriber
                else:
                    print(f"Error sending message: {e}")
                    return None

    if messages_sent == 0:  # No messages were sent
        print("No active subscriptions for this room.")
        return None

    return subscriber  # Return subscriber object after all messages are sent



# This sets up 15 workers which individually start a thread of sendMessage defined above

def send_daily_good_boy():
    subscribers = subscribers_collection.find()
      # Define the number of workers for the ThreadPoolExecutor
    workers = 15
    # Use a ThreadPoolExecutor to send messages in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(send_message, subscribers))

def send_daily_good_boy_just_matt():
    subscribers = subscribers_collection.find( { "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vZDVlOTc4MDAtM2QzNi0xMWVlLWFlY2YtNDFlZDFiOTZiNDcx" } )
      # Define the number of workers for the ThreadPoolExecutor
    workers = 15
    # Use a ThreadPoolExecutor to send messages in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(send_message, subscribers))


api = webexteamssdk.WebexTeamsAPI(access_token=BOT_TOKEN)
send_daily_good_boy()
