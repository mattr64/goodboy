# Stop trying to make fetch happen
import os
import requests
from PIL import Image
from io import BytesIO
import re
import random
import json
from multiprocessing import Process
from pathlib import Path

# Go get secrets from the config

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

with open(config_path) as f:
    config = json.load(f)
# Use the cat API in the secrets file
cat_api_token = config['cat_api_key']

# Use the Dog CEO API to fetch the dog of the day.
def fetch_dog():
    print("Fetching dog")
    response = requests.get("https://dog.ceo/api/breeds/image/random")
    image_url = response.json()['message']
    image_response = requests.get(image_url)

    # Extract the breed from the URL
    breed_pattern = re.compile(r'/breeds/([^/]+)/')
    match = breed_pattern.search(image_url)
    breed = match.group(1) if match else "Unknown"

    # Handle multi-word breeds in the URL and reverse word order
    if '-' in breed:
        breed_words = breed.split('-')
        breed_words.reverse()
        breed = ' '.join(breed_words)

    goodness_score = random.randint(10, 16)
    process_image(image_response.content, "/var/www/goodboy/fetch/dog.jpg")
    save_text(breed, goodness_score, "/var/www/goodboy/fetch/dog.txt")
    print("fetched dog")

# Use the capy.lol api to grab the capy of the day
def fetch_capy():
    print("Fetching capy")
    response = requests.get("https://api.capy.lol/v1/capybaras?random=true&take=1")
    json_data = response.json()
    capy_data = json_data['data'][0]
    image_url = capy_data['url']
    image_response = requests.get(image_url)

    capy_chill = random.randint(8, 15)
    description = capy_data['alt']
    process_image(image_response.content, "/var/www/goodboy/fetch/capy.jpg")
    save_text(description, capy_chill, "/var/www/goodboy/fetch/capy.txt")
    print("fetched capy")

# Use the cat API to fetch the cat of the day
def fetch_cat():
    print("Fetching cat")
    # We first need to get the UID for the cat image which is returned as JSON
    response = requests.get(
        "https://api.thecatapi.com/v1/images/search?limit=1",
        headers={"x-api-key": cat_api_token}
    )
    json_data = response.json()
    image_id = json_data[0]['id']
    image_url = json_data[0]['url']
    image_response = requests.get(image_url)

    # Using this UID we re-query the API and grab the image URL and breed/desc if available
    response = requests.get(
        f"https://api.thecatapi.com/v1/images/{image_id}",
        headers={"x-api-key": cat_api_token}
    )
    json_data = response.json()
    breeds_data = json_data.get("breeds", [])
    if breeds_data:
        breed_name = breeds_data[0].get("name", "None available")
        description = breeds_data[0].get("description", "None available")
    else:
        breed_name = "None available"
        description = "None available"

    # Use extremely advanced algorithms to generate the cattitude score
    cattitude = random.randint(6, 10)

    process_image(image_response.content, "/var/www/goodboy/fetch/cat.jpg")
    save_text(f"{breed_name}", cattitude, "/var/www/goodboy/fetch/cat.txt")
    print("Fetched cat")

# Image processing is abstracted out to a function as all three animals use it
# This function converts to RGB, re-sizes and re-saves as JPEG so we can be sure webex will handle it
def process_image(image_content, save_path):
    print("Processing image")
    # Open image from bytes
    image = Image.open(BytesIO(image_content))
    
    # Convert Palette-based ('P') images to RGB
    if image.mode in ("RGBA", "P"): image = image.convert("RGB") 
    if image.mode == 'P':
        image = image.convert("RGB")
        
    # Resize to 800 on max edge
    max_dimension = 800
    if image.width > image.height:
        factor = max_dimension / image.width
    else:
        factor = max_dimension / image.height

    image_resized = image.resize((int(image.width * factor), int(image.height * factor)))
    
    # Save the image
    image_resized.save(save_path, format="JPEG")

def save_text(description, score, save_path):
    print("Saving scores")
    with open(save_path, 'w') as file:
        file.write(f"{description}\n{score}")

# Some paralleling code to speed up fetching. Totally not needed. But why not.
def runInParallel(*fns):
  proc = []
  for fn in fns:
    p = Process(target=fn)
    p.start()
    proc.append(p)
  for p in proc:
    p.join()

if __name__ == "__main__":
    runInParallel(fetch_cat, fetch_dog, fetch_capy)
