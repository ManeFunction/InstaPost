from instagrapi import Client  # A Python library for Instagram API
from PIL import Image  # A Python library for working with images
from dotenv import load_dotenv  # Parameters environment
import os  # A module for interacting with the operating system
import glob  # A module for working with files
import random  # A module for generating random numbers
import time  # A module for working with time

# set up environment
load_dotenv()

# load config
login = os.environ.get("LOGIN")
password = os.environ.get("PASS")
hashtags = os.environ.get("HASHTAGS")
images_dir = os.environ.get("IMAGES_PATH")
repeat_time = int(os.environ.get("POST_DELAY"))
repeat_window = int(os.environ.get("POST_WINDOW"))
login_time = int(os.environ.get("LOGIN_DELAY"))
login_window = int(os.environ.get("LOGIN_WINDOW"))

# Pre-define some variables and methods
extensions = ['*.png', '*.jpg', '*.jpeg']
tags_filename = "tags.txt"
no_images_message = "No files left. Abort."


def get_random_time_window(target_time, window) -> int:
    result_time = target_time
    if window > 0:
        result_time = random.randint(target_time - window, target_time + window)
    return result_time


def get_images_at(path) -> list:
    result = [f for ext in extensions for f in glob.glob(os.path.join(path, ext))]
    return result


def try_post_image_from(path):
    # Choosing a random file from the subfolder
    images_list = get_images_at(path)
    image = random.choice(images_list)
    print("Selected file: ", image)

    # Getting the full path of the file
    image_path = os.path.join(path, image)

    # If the file is PNG, convert it to JPG
    if image.endswith(".png"):
        print("Converting PNG to JPG...")
        png_image = Image.open(image_path)
        rgb_image = png_image.convert('RGB')
        output_file_path = image_path[:-4] + ".jpg"
        rgb_image.save(output_file_path, quality=100)
        os.remove(image_path)
        image_path = output_file_path
        print("Converted to JPG")

    # Manage hashtags
    caption = hashtags
    tags_path = os.path.join(path, tags_filename)
    if os.path.isfile(tags_path):
        with open(tags_path, "r") as f:
            content = f.read()
            caption += ' '
            caption += content

    # Uploading the file as a post with a caption
    cl.photo_upload(image_path, caption=caption)
    print("Uploaded")

    # Deleting the file from the folder
    os.remove(image_path)


# Creating an instance of the Client class
cl = Client()

# Logging in cycle (trying to log in until successful)
while True:
    try:
        print("Logging in...")
        cl.login(login, password)
        print("Logged in as", login)
        break
    except:
        t = get_random_time_window(login_time, login_window)
        print(f"Failed to log in. Trying again in {t} seconds...")
        time.sleep(t)


# >>> MAIN LOOP <<<
while True:
    # Getting the list of subfolders
    subfolders = [f.path for f in os.scandir(images_dir) if f.is_dir()]

    # One root folder logic
    if len(subfolders) == 0:
        images = get_images_at(images_dir)
        total = len(images)

        # Keep the cycle running even if there are no files in the folder
        # to prevent painful re-logging operation
        if total == 0:
            print(no_images_message)
        else:
            # Posting image from the root folder
            try_post_image_from(images_dir)

    # Subfolders logic
    else:
        # Build up the map
        images_map = {}
        for subfolder in subfolders:
            files = get_images_at(subfolder)
            images_map[subfolder] = len(files)

        # Calculate total number of images left
        total = sum(images_map.values())

        # Keep the cycle running even if there are no files in the folder
        # to prevent painful re-logging operation
        if total == 0:
            print(no_images_message)
        else:
            # Choosing a random subfolder with actual images
            non_empty_subfolders = [key for key, value in images_map.items() if value != 0]
            category = random.choice(non_empty_subfolders)
            print("Selected category: ", os.path.basename(os.path.normpath(category)))

            # Posting image from the selected category
            try_post_image_from(category)

    # Waiting for some time (in seconds)
    t = get_random_time_window(repeat_time, repeat_window)
    print(f"Waiting {t} seconds...")
    time.sleep(t)
