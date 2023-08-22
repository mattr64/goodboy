#
#
# Good Boy Bot - a work in progress
# # # # # # # # # # # # # # # # # # # # # # # # # #
#     ^
#    / \__
# (    @\__ 
#  /         O
# /   (_____/
# /_____/ U
#[=====]
# # # # # # # # # # # # # # # # # # # # # # # # # #
# mabarber@cisco.com / 'Good Boy' on Cisco Webex  #
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Prob put this on Git soon innit                 #
# # # # # # # # # # # # # # # # # # # # # # # # # #
# TO DO: Abstract the conversation elements away to a JSON file to make things cleaner

from flask import Flask, request
from datetime import datetime
import requests
import json
from pymongo import MongoClient
from webexteamssdk import WebexTeamsAPI

# Load external config file, as to not store secrets in the code
# We replace them below with those loaded in from 'config'
with open('config.json') as f:
    config = json.load(f)

BOT_TOKEN = config['webex_bot_access_token']
BOT_SYSTEM_ID = config['webex_bot_system_id']
YOUR_WEBHOOK_URL = config['bot_webhook_url']
BOT_ID = config['webex_bot_person_id']
WEBEX_WEBHOOK_URL = config['webex_webhook_url']
dbusername = config['db_username']
dbpassword = config['db_password']

api = WebexTeamsAPI(access_token=BOT_TOKEN)

client = MongoClient(f"mongodb://{dbusername}:{dbpassword}@localhost:27017/")
db = client['goodboy']
subscribers_collection = db['subscribers']

app = Flask(__name__)

# Function definitions
# Delete existing webhook with the same target URL
def delete_existing_webhooks():
    headers = {
        "Authorization": f"Bearer {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    webhooks_response = requests.get("https://webexapis.com/v1/webhooks", headers=headers)
    webhooks = webhooks_response.json().get("items", [])

    for webhook in webhooks:
        if webhook['targetUrl'] == YOUR_WEBHOOK_URL:
            webhook_id = webhook['id']
            delete_url = f"https://webexapis.com/v1/webhooks/{webhook_id}"
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code == 204:
                print(f"Deleted webhook with ID {webhook_id}")

def create_webhook(url):
    headers = {
        "Authorization": f"Bearer {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": "Daily Good Boy Webhook",
        "targetUrl": url,
        "resource": "messages",
        "event": "created"
    }
    response = requests.post(WEBEX_WEBHOOK_URL, json=payload, headers=headers)
    print("Webhook created:", response.json())

def send_message_to_webex(room_id, message):
    api.messages.create(roomId=room_id, markdown=message)

# Changed from using person to room for unique subscriptions. 
# This way, one person can sign up many rooms (group chats, etc.),
# and others can unsubscribe a room if they are inside the room.
def handle_subscription(person_id, person_email, room_id):
    subscriber = {
        "personEmail": person_email,
        "personId": person_id,
        "subscribedTime": datetime.now(),
        "roomId": room_id
    }
    #existing_subscriber = subscribers_collection.find_one({"personId": person_id})
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        return "This room is already subscribed! (If this is wrong, ping Matt)"
    #if existing_subscriber:
    #    return "Hey! You're already subscribed! (If this is wrong, ping Matt)"

    subscribers_collection.insert_one(subscriber)
    return "You've successfully subscribed to the Daily Good Boy!"

def handle_unsubscription(room_id):
    #result = subscribers_collection.delete_one({"personId": person_id})
    result = subscribers_collection.delete_one({"roomId": room_id})
    if result.deleted_count > 0:
        return "You've successfully unsubscribed from the Daily Good Boy!"
    else:
        return "You are not yet subscribed - nothing to do. If this is in error, ping Matt"

@app.route('/barkbarkbark', methods=['POST'])
def webhook():
    print("Received a request:")
    print(request.json)  # Print the JSON body of the request
    data = request.json
    message_id = data['data']['id']
    person_id = data['data']['personId']
    person_email = data['data']['personEmail']
    room_id = data['data']['roomId']
    
    # Fetch the message details using message_id
    message_url = f"https://webexapis.com/v1/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    message_response = requests.get(message_url, headers=headers)
    message_text = message_response.json().get("text")
    print(message_text)
    
    # Check if the message is from the bot itself
    if message_response.json().get("personId") == BOT_ID:
        print("From the bot - not processing.")
        return '', 204
    
    # Handle empty, none or whitespace messages (i.e. screenshots, thanks Rosie! :)
    # For now, if empty, just replace with 'bark' which gets interpreted as a dog command later on
    if not message_text or message_text.isspace():
        print("Received an empty or whitespace-only message; treating as 'bark'.")
        message_text = "bark"

    # make it all lower case
    message_text = message_text.lower()
    
    # Message processing - the order is important. The top four stay at the top.
    # people should be able to remove their entry from the DB with unsubscribe ANYWHERE in the message and 'stop' on one line.
    # Fun commands are always after these four.
    # UNSUB is always first, as a catch-all if someone says 'unsubscribe' in the message.
    # Matching 'subscribe explicitly is then important, and then we need to do a 'in' because in group chats we can never address the bot without mentioning it, so the message will never 'just be' subscribe.
    
    if 'unsubscribe' in message_text:
        response_message = handle_unsubscription(room_id)
        send_message_to_webex(room_id, response_message)
    elif message_text == 'subscribe':
        response_message = handle_subscription(person_id, person_email, room_id)
        send_message_to_webex(room_id, response_message)
    elif 'subscribe' in message_text:
        response_message = handle_subscription(person_id, person_email, room_id)
        send_message_to_webex(room_id, response_message)
    elif message_text == 'stop':
        response_message = handle_unsubscription(room_id)
        send_message_to_webex(room_id, response_message)

    # non critical but useful messages
    elif 'help' in message_text:
        response_message = "Help message (bark bark)\n\nTo subscribe to a daily image of a dog (7AM UK time each morning, unguaranteed), reply 'subscribe'.\n\nThis is totally for fun and not in any way guaranteed. The images are from an external source (The Dog CEO API - yeah I didn't know it existed either) and are unvetted and uncontrolled. This may stop working at any time.\n\nIf I go haywire please tell my master, Matt (mabarber@).\nIf you need to unsubscribe, write 'unsubscribe' anywhere in a message.\nTry some other commands - I maybe trained, after all, I am a very good boy!! Bark Bark Bark\n\n\n"
        send_message_to_webex(room_id, response_message)
    elif 'hello' in message_text:
        response_message = "Help message (bark bark)\n\nTo subscribe to a daily image of a dog (7AM UK time each morning, unguaranteed), reply 'subscribe'.\n\nThis is totally for fun and not in any way guaranteed. The images are from an external source (The Dog CEO API - yeah I didn't know it existed either) and are unvetted and uncontrolled. This may stop working at any time.\n\nIf I go haywire please tell my master, Matt (mabarber@).\nIf you need to unsubscribe, write 'unsubscribe' anywhere in a message.\nTry some other commands - I maybe trained, after all, I am a very good boy!! Bark Bark Bark\n\n\n"
        send_message_to_webex(room_id, response_message)
    elif 'about' in message_text:
        response_message = "About this bot\n\nA 'for fun' project which after the dawn of OpenAI pair programming I can finally realise and have fun making. Learning loads about Webex API, webhooks in general and Python, here is the Good Boy Bot.\n\nUntil I break it.\n"
        send_message_to_webex(room_id, response_message)

    # stupid responses that will hopefully entertain
    elif 'bark' in message_text:
        response_message = "Woof woof! Bark bark! 🐶"
        send_message_to_webex(room_id, response_message)
    elif 'woof' in message_text:
        response_message = "Bark! Bark bark bark bark! Ruff ruff! 🐾"
        send_message_to_webex(room_id, response_message)
    elif 'sit' in message_text:
        response_message = "*sits obediently... and then immediately stands up again*"
        send_message_to_webex(room_id, response_message)
    elif 'other paw' in message_text:
        response_message = "*gives other paw* Bark!"
        send_message_to_webex(room_id, response_message)
    elif 'paw' in message_text:
        response_message = "*tilts head, confused* 🐾"
        send_message_to_webex(room_id, response_message)
    elif 'stay' in message_text:
        response_message = "*Gets distracted by a virtual squirrel* 🐿️"
        send_message_to_webex(room_id, response_message)
    elif 'fetch' in message_text:
        response_message = "🎾"
        send_message_to_webex(room_id, response_message)
    elif 'roll over' in message_text:
        response_message = "*rolls over* *goes to sleep*"
        send_message_to_webex(room_id, response_message)
    elif 'shake' in message_text:
        response_message = "*Shakes tail instead*"
        send_message_to_webex(room_id, response_message)
    elif 'heel' in message_text:
        response_message = "I'm here! 🦴"
        send_message_to_webex(room_id, response_message)
    elif 'play dead' in message_text:
        response_message = "*Sneezes loudly* 💤"
        send_message_to_webex(room_id, response_message)
    elif 'speak' in message_text:
        response_message = "Bark! Woof! Ruff ruff! 🗣️"
        send_message_to_webex(room_id, response_message)

    return '', 204

if __name__ == '__main__':
    delete_existing_webhooks()          # Delete existing webhooks before starting
    create_webhook(YOUR_WEBHOOK_URL)    # Create a new webhook
    app.run(port=5000)                  # We front with NGINX HTTPS, so we just run HTTP here on localhost