import requests
from PIL import Image
from io import BytesIO
import re
import random

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

def process_image(image_content, save_path):
    image = Image.open(BytesIO(image_content))

    # Resize image to normalize it
    max_dimension = 800
    factor = max_dimension / max(image.width, image.height)

    image_resized = image.resize((int(image.width * factor), int(image.height * factor)))
    image_resized.save(save_path, format="JPEG")

def save_text(description, score, save_path):
    with open(save_path, 'w') as file:
        file.write(f"{description}\n{score}")

if __name__ == "__main__":
    fetch_dog()
    fetch_capy()
