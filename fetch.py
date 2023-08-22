import requests
from PIL import Image
from io import BytesIO
import re
import random

# First things first - let's set the good boy score for the day!
goodness_score = random.randint(10, 16)

# Get a random dog image
response = requests.get("https://dog.ceo/api/breeds/image/random")
image_url = response.json()['message']
image_response = requests.get(image_url)
print(image_url)
# Extract the breed from the URL
breed_pattern = re.compile(r'/breeds/([^/]+)/')
match = breed_pattern.search(image_url)
breed = match.group(1) if match else "Unknown"

# Handle multi-word breeds
if '-' in breed:
    # Split the breed by hyphen and reverse the words
    breed_words = breed.split('-')
    breed_words.reverse()
    # Join the words with spaces
    breed = ' '.join(breed_words)

# Open the image and resize it
image = Image.open(BytesIO(image_response.content))

# Determine the resizing factor
max_dimension = 800
if image.width > image.height:
    factor = max_dimension / image.width
else:
    factor = max_dimension / image.height

# Resize the image
image_resized = image.resize((int(image.width * factor), int(image.height * factor)))

# Save the image locally
image_resized.save('/var/www/goodboy.robot64.com/fetch/dog.jpg', format="JPEG")

with open('/var/www/goodboy.robot64.com/fetch/breed.txt', 'w') as file:
    file.write(f"{breed}\n{goodness_score}")

print(f"Image of {breed} saved with GoodBoy Rating©: {goodness_score}/10!")

