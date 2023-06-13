from instagrapi import Client  # A Python library for Instagram API
from PIL import Image  # A Python library for working with images
from dotenv import load_dotenv  # Parameters environment
import os  # A module for interacting with the operating system
import glob  # A module for working with files
import random  # A module for generating random numbers
import time  # A module for working with time
from telethon import TelegramClient  # A Python library for Telegram API
import asyncio  # A module for asynchronous execution of code
import signal  # A module for working with system signals
import subprocess  # A module for working with subprocesses

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

tgid = os.environ.get("APPID")
tghash = os.environ.get("APIHASH")
tg_session_name = os.environ.get("SESSION_NAME")
log_tg_channel = int(os.environ.get("LOG_TG_CHANNEL"))

# Pre-define some variables and methods
extensions = ['*.png', '*.jpg', '*.jpeg']
tags_filename = "tags.txt"
no_images_message = "No files left. Abort."


# send service message when script was terminated
def signal_handler(sig, frame):
    subprocess.run(['python3', 'termination_handler.py'])


# register termination signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def get_random_time_window(target_time, window) -> int:
    result_time = target_time
    if window > 0:
        result_time = random.randint(target_time - window, target_time + window)
    return result_time


def get_images_at(path) -> list:
    result = [f for ext in extensions for f in glob.glob(os.path.join(path, ext))]
    return result


def try_post_image_from(path) -> (str, str):
    # Choosing a random file from the subfolder
    images_list = get_images_at(path)
    image = random.choice(images_list)
    print("Selected file: ", image)

    # Getting the full path of the file
    selected_image_path = os.path.join(path, image)

    # If the file is PNG, convert it to JPG
    if image.endswith(".png"):
        print("Converting PNG to JPG...")
        png_image = Image.open(selected_image_path)
        rgb_image = png_image.convert('RGB')
        output_file_path = selected_image_path[:-4] + ".jpg"
        rgb_image.save(output_file_path, quality=100)
        os.remove(selected_image_path)
        selected_image_path = output_file_path
        print("Converted to JPG")

    # Manage hashtags
    caption = hashtags
    tags_path = os.path.join(path, tags_filename)
    if os.path.isfile(tags_path):
        with open(tags_path, "r") as f:
            content = f.read()
            caption += ' '
            caption += content

    # randomize hashtags to prevent instagram auto-posting detection
    split = caption.split(' ')
    random.shuffle(split)
    caption = ' '.join(split)

    # Uploading the file as a post with a caption
    media = cl.photo_upload(selected_image_path, caption=caption)
    media_code = media.dict().get("code")
    url = f"https://www.instagram.com/p/{media_code}/"
    print("Uploaded")

    return url, selected_image_path


async def send_telegram_message(message):
    async with TelegramClient(tg_session_name, tgid, tghash) as client:
        await client.send_message(log_tg_channel, message)


async def send_telegram_file(message, file_path):
    async with TelegramClient(tg_session_name, tgid, tghash) as client:
        await client.send_file(log_tg_channel, file_path, force_document=False, caption=message)
        os.remove(image_path)


def log_to_telegram(message):
    asyncio.run(send_telegram_message(message))


def log_to_telegram(message, file_path):
    asyncio.run(send_telegram_file(message, file_path))


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
        total_images_left = total - 1
        print(f"Total number of images left: {total_images_left}")

        # Keep the cycle running even if there are no files in the folder
        # to prevent painful re-logging operation
        if total == 0:
            print(no_images_message)
            log_to_telegram(f"**{login}**: {no_images_message}")
        else:
            # Posting image from the root folder
            post_url, image_path = try_post_image_from(images_dir)
            log_to_telegram(f"**{login}**: New image was posted!\nImages left: {total_images_left}\n{post_url}", image_path)

    # Subfolders logic
    else:
        # Build up the map
        images_map = {}
        for subfolder in subfolders:
            files = get_images_at(subfolder)
            images_map[subfolder] = len(files)

        # Calculate total number of images left
        total = sum(images_map.values())
        total_images_left = total - 1
        print(f"Total number of images left: {total_images_left}")

        # Keep the cycle running even if there are no files in the folder
        # to prevent painful re-logging operation
        if total == 0:
            print(no_images_message)
            log_to_telegram(f"**{login}**: {no_images_message}")
        else:
            # Choosing a random subfolder with actual images
            non_empty_subfolders = [key for key, value in images_map.items() if value != 0]
            category = random.choice(non_empty_subfolders)
            category_name = os.path.basename(os.path.normpath(category))
            images_in_category_left = images_map[category] - 1
            print("Selected category: ", category_name)
            print(f"Number of images left in the category: {images_in_category_left}")

            # Posting image from the selected category
            post_url, image_path = try_post_image_from(category)
            log_to_telegram(f"**{login}**: New image was posted!\nCategory: {category_name}\nImages left: {images_in_category_left} ({total_images_left})\n{post_url}", image_path)

    # Waiting for some time (in seconds)
    t = get_random_time_window(repeat_time, repeat_window)
    print(f"Waiting {t} seconds...")
    time.sleep(t)
