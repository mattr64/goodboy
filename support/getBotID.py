import requests

# set up auth and endpoint params
BOT_TOKEN = "aaa" 
BOT_EMAIL = "GoodBoy@webex.bot"
WEBEX_PEOPLE_URL = "https://webexapis.com/v1/people"

# set up query and headers
query_params = {
    "email": BOT_EMAIL
}

headers = {
    "Authorization": f"Bearer {BOT_TOKEN}",
    "Content-Type": "application/json"
}

# Run the GET
response = requests.get(WEBEX_PEOPLE_URL, params=query_params, headers=headers)

# Fetch the ID
if response.status_code == 200:
    people = response.json().get("items", [])
    if people:
        BOT_PERSON_ID = people[0]['id']
        print(f"The bot's person ID is {BOT_PERSON_ID}")
    else:
        print("Bot not found.")
else:
    print("Error fetching bot details:", response.json())
