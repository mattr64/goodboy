# Fetch - this is run as a cron (or manually)
# Each run will hit the Dog CEO API, retrieve image and derive breed from filename.
# We also generate the goodboy score using super secret machine learning algorithms.
# The image gets normalised and saved as JPG on public webserver, along with TXT containing
# breed and GBScore.
#
# TO DO: Get location from user. If exist, get weather for user location.
#
import requests
from PIL import Image
from io import BytesIO
import re
import random

# First things first - let's set the scores for the day!
goodness_score = random.randint(10, 16)
cattitude = random.randint(6, 10)

# Get a random dog image
response = requests.get("https://dog.ceo/api/breeds/image/random")
image_url = response.json()['message']
image_response = requests.get(image_url)
print(image_url)
# Extract the breed from the URL
breed_pattern = re.compile(r'/breeds/([^/]+)/')
match = breed_pattern.search(image_url)
breed = match.group(1) if match else "None available"

# Handle multi-word breeds in the URL and reverse word order
if '-' in breed:
    breed_words = breed.split('-')
    breed_words.reverse()
    breed = ' '.join(breed_words)

# We resize to normalise the image, as we can't predict or trust what comes from DogCEO API
image = Image.open(BytesIO(image_response.content))

# We want the longest edge to be 800, this determines the longest edge
max_dimension = 800
if image.width > image.height:
    factor = max_dimension / image.width
else:
    factor = max_dimension / image.height

# Resize the image and save it to public webserver as JPEG. 
# The purpose of this re-save eliminates any errors in the source image that could cause Webex to reject it.
image_resized = image.resize((int(image.width * factor), int(image.height * factor)))
image_resized.save('/var/www/goodboy.robot64.com/fetch/dog.jpg', format="JPEG")
# Store the breed and goodness score in a text file in the local filesystem
# We access this infrequently - fetch writes, bark reads, once a day.
with open('/var/www/goodboy.robot64.com/fetch/dog.txt', 'w') as file:
    file.write(f"{breed}\n{goodness_score}")
print(f"Image of {breed} saved with GoodBoy Rating©: {goodness_score}/10!")

