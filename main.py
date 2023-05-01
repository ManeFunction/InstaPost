from instagrapi import Client  # A Python library for Instagram API
from PIL import Image  # A Python library for working with images
from dotenv import load_dotenv  # Parameters environment
import os  # A module for interacting with the operating system
import random  # A module for generating random numbers
import time  # A module for working with time

# set up environment
load_dotenv()

# load config
login = os.environ.get("LOGIN")
password = os.environ.get("PASS")
hashtags = os.environ.get("HASHTAGS")
images_dir = os.environ.get("IMAGES_PATH")
repeat_time = int(os.environ.get("TIME"))

# Creating an instance of the Client class
cl = Client()

# Logging in to Instagram with your username and password
print("Logging in...")
cl.login(login, password)
print("Logged in as ", login)

# Creating an infinite loop
while True:
    # Getting the list of files in the folder
    files = os.listdir(images_dir)
    print("Total files: ", len(files))

    # Choosing a random file from the list
    file = random.choice(files)
    print("Selected file: ", file)

    # Getting the full path of the file
    file_path = os.path.join(images_dir, file)

    # If the file is PNG, convert it to JPG
    if file.endswith(".png"):
        print("Converting PNG to JPG...")
        png_image = Image.open(file_path)
        rgb_image = png_image.convert('RGB')
        output_file_path = file_path[:-4] + ".jpg"
        rgb_image.save(output_file_path, quality=100)
        os.remove(file_path)
        file_path = output_file_path
        print("Converted to JPG")

    # Uploading the file as a post with a caption
    cl.photo_upload(file_path, caption=hashtags)
    print("Uploaded")

    # Deleting the file from the folder
    os.remove(file_path)

    # Stop the script if there are no files left
    if len(files) == 1:
        print("No files left. Stopping...")
        break

    # Waiting for 8 hours (in seconds)
    print("Waiting...")
    time.sleep(repeat_time)
