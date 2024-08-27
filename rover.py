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
# # # # # # # # # # # # # # # # # # # # # # # # # #
# TO DO: Abstract the conversation elements away to a JSON file to make things cleaner

from flask import Flask, request
from datetime import datetime
import requests
import json
from pymongo import MongoClient
from webexteamssdk import WebexTeamsAPI
import threading

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
    if 'created' in response.json():
        print(f"Webhook created at: {response.json()['created']}")
    if 'expires' in response.json():  # if the API provides expiration info
        print(f"Webhook expires at: {response.json()['expires']}")

def refresh_webhook():
    delete_existing_webhooks()
    create_webhook(YOUR_WEBHOOK_URL)
    # call this function again in one hour
    threading.Timer(3600, refresh_webhook).start()

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
        "roomId": room_id,
        "animals": {
            "dog": True,
            "cat": False,
            "capy": False
        }
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


def enable_catperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.cat": True}}
        )
        return "Hey cat person! You've enabled cat updates for this room. Use 'disable cat' to do the opposite. 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."
def enable_dogperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.dog": True}}
        )
        return "Hey dog person! You've enabled dog updates for this room. Use 'disable dog' to do the opposite (but you wouldn't, would you?!). 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."
def enable_capyperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.capy": True}}
        )
        return "Hey capy person! You've enabled capy updates for this room. Use 'disable capy' to do the opposite (how could you?!). 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."
def disable_dogperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.dog": False}}
        )
        return "Who's a bad dog? Well, no dogs for you, then. You've disabled dog updates for this room. Use 'enable dog' to bring back the good boys. 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."
def disable_catperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.cat": False}}
        )
        return "No more meows for you. You've disabled cat updates for this room. Use 'enable cat' to welcome back our feline friends. 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."
def disable_capyperson(room_id):
    existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
    if existing_subscriber_by_room:
        subscribers_collection.update_one(
            {"roomId": room_id},
            {"$set": {"animals.capy": False}}
        )
        return "Not cool, human. You've disabled capybara updates for this room. Use 'enable capy' to fix this travesty. 'Help' for more. 'unsubscribe' or 'stop' to stop all."
    else:
        return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."

def get_subscription_status(room_id):
        existing_subscriber_by_room = subscribers_collection.find_one({"roomId": room_id})
        if existing_subscriber_by_room:
            animal_prefs = existing_subscriber_by_room.get("animals", {})
            dog_status = "enabled" if animal_prefs.get("dog", False) else "disabled"
            cat_status = "enabled" if animal_prefs.get("cat", False) else "disabled"
            capy_status = "enabled" if animal_prefs.get("capy", False) else "disabled"

            return f"""Subscription status for this room:
- Dog updates: {dog_status}
- Cat updates: {cat_status}
- Capy updates: {capy_status}

Use 'enable [animal]' or 'disable [animal]' to change these settings.
'Help' for more commands. 
'Unsubscribe' or 'stop' to stop all."""
        else:
            return "You've not subscribed this room yet. Please send me a subscribe command, then enable or disable options. By subscribing, you give consent to store these preferences, so it is a required first step."

@app.route('/barkbarkbark', methods=['POST'])
def webhook():
    print("Received a request:")
    print(request.json)  # Print the JSON body of the request
    data = request.json
    message_id = data['data']['id']
    person_id = data['data']['personId']
    person_email = data['data']['personEmail']
    room_id = data['data']['roomId']
    print("Headers:")
    print(request.headers)
    
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
        response_message = """Help message (bark bark)
        To subscribe to daily delivery, reply 'subscribe'
        To stop messages and remove your preferences, reply 'unsubscribe' or 'stop'
        To check your subscriptions, reply 'status'

        Setting individual preferences
        'enable dog':  Get daily dog deliveries
        'enable cat':  Get daily cat deliveries
        'enable capy': Get daily capybara deliveries
        'disable dog', 'disable cat', 'disable capy' will stop that particular channel.
        """
        send_message_to_webex(room_id, response_message)
        
    elif 'about' in message_text:
        response_message = """About this bot
        A 'for fun' project which, after the dawn of OpenAI pair programming I can finally realise and have fun making.
        Learning loads about Webex API and Python, here is the Good Boy Bot.\n\nUntil I break it.\n
        """
        send_message_to_webex(room_id, response_message)
    
    # Individual service enable and disable handling
    if 'enable cat' in message_text:
        response_message = enable_catperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'enable capy' in message_text:
        response_message = enable_capyperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'enable dog' in message_text:
        response_message = enable_dogperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'disable cat' in message_text:
        response_message = disable_catperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'disable capy' in message_text:
        response_message = disable_capyperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'disable dog' in message_text:
        response_message = disable_dogperson(room_id)
        send_message_to_webex(room_id, response_message)
    if 'status' in message_text:
        response_message = get_subscription_status(room_id)
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
    elif 'meow' in message_text:
        response_message = "*Bats ball of string across the room*"
        send_message_to_webex(room_id, response_message)
    elif 'hup' in message_text:
        response_message = "OK I pull up"
        send_message_to_webex(room_id, response_message)
    elif 'good boy' in message_text:
        response_message = "*Wags tail*"
        send_message_to_webex(room_id, response_message) 
    return '', 204

if __name__ == '__main__':
    refresh_webhook()                   # Init first webhook and refresh every hour
    app.run(host='0.0.0.0', port=9900)                  # We front with NGINX HTTPS, so we just run HTTP here on localhost
