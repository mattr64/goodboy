# GoodBoy Bot
## A modern solution to no problem at all
---
Brighten your morning with a daily delivery of a Certified Good Boy© direct to your Webex team space.
---
## Components
### Fetch.py
This is designed to run on a cronjob every morning. 
Fetches an image from the Dog CEO API, parses the breed from the filename and stores image, breed and Certified GoodBoy Score© for the day.
If the Dog CEO API stops working then we stop working... but that'll never happen, right?

### Bark.py
This is designed to run on a cronjob every morning, after Fetch.py.
Sends out a Certified Good Boy© Adaptive Card to every subscriber in the database when run.

*Threading*
Utilises threading (ThreadPoolExecutor) with multiple workers to ensure rapid delivery. Number of workers can be tweaked in here changing simultaneous message delivery limits. Also supports backing off and retry if we get a 429 back from the API.

### Rover.py
The main webhook component. This is designed to always run. Needs converting to run inside a proper WSGI server.
This listens for all requests from users and responds accordingly.
This handles subscribe and unsubscribe requests, adding or removing subscribers to/from the database.