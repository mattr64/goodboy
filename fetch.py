import requests
from PIL import Image
from io import BytesIO
import re
import random
import json

# Go get secrets from the config
with open('/opt/gbb/config.json') as f:
    config = json.load(f)

cat_api_token = config['cat_api_key']

def fetch_dog():
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
    process_image(image_response.content, "/var/www/goodboy.robot64.com/fetch/dog.jpg")
    save_text(breed, goodness_score, "/var/www/goodboy.robot64.com/fetch/breed.txt")

def fetch_capy():
    response = requests.get("https://api.capy.lol/v1/capybaras?random=true&take=1")
    json_data = response.json()
    capy_data = json_data['data'][0]
    image_url = capy_data['url']
    image_response = requests.get(image_url)

    capy_chill = random.randint(8, 15)
    description = capy_data['alt']
    process_image(image_response.content, "/var/www/goodboy.robot64.com/fetch/capy.jpg")
    save_text(description, capy_chill, "/var/www/goodboy.robot64.com/fetch/capy.txt")


def fetch_cat():
    # Step 1: Get a random cat image ID
    response = requests.get(
        "https://api.thecatapi.com/v1/images/search?limit=1",
        headers={"x-api-key": cat_api_token}
    )
    json_data = response.json()
    image_id = json_data[0]['id']
    image_url = json_data[0]['url']
    image_response = requests.get(image_url)

    # Step 2: Get additional information for the cat image
    response = requests.get(
        f"https://api.thecatapi.com/v1/images/{image_id}",
        headers={"x-api-key": cat_api_token}
    )
    json_data = response.json()
    breeds_data = json_data.get("breeds", [])
    if breeds_data:
        breed_name = breeds_data[0].get("name", "Unknown")
        description = breeds_data[0].get("description", "No description available.")
    else:
        breed_name = "Unknown"
        description = "No description available."

    cattitude = random.randint(6, 10)

    process_image(image_response.content, "/var/www/goodboy.robot64.com/fetch/cat.jpg")
    save_text(f"{breed_name}\n{description}", cattitude, "/var/www/goodboy.robot64.com/fetch/cat.txt")

def process_image(image_content, save_path):
    # Open image from bytes
    image = Image.open(BytesIO(image_content))
    
    # Convert Palette-based ('P') images to RGB
    if image.mode == 'P':
        image = image.convert("RGB")
        
    # Your existing code for resizing and other operations
    max_dimension = 800
    if image.width > image.height:
        factor = max_dimension / image.width
    else:
        factor = max_dimension / image.height

    image_resized = image.resize((int(image.width * factor), int(image.height * factor)))
    
    # Save the image
    image_resized.save(save_path, format="JPEG")

def save_text(description, score, save_path):
    with open(save_path, 'w') as file:
        file.write(f"{description}\n{score}")

if __name__ == "__main__":
    fetch_dog()
    fetch_capy()
    fetch_cat()