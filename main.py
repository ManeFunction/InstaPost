from instagrapi import Client  # A Python library for Instagram API
from PIL import Image  # A Python library for working with images
from dotenv import load_dotenv  # Parameters environment
import os  # A module for interacting with the operating system
import ast  # A module for converting strings to Python objects
import glob  # A module for working with files
import random  # A module for generating random numbers
import telegram  # A Python library for Telegram API
import asyncio  # A module for asynchronous execution of code
import signal  # A module for working with system signals

# set up environment
load_dotenv()

# load config
login = os.environ.get("LOGIN")
password = os.environ.get("PASS")
hashtags = os.environ.get("HASHTAGS")
images_dir = os.environ.get("IMAGES_PATH")

repeat_time = int(os.environ.get("POST_DELAY"))
repeat_window = int(os.environ.get("POST_WINDOW"))
loop_time = float(os.environ.get("LOOP_TIME"))
post_story_every = int(os.environ.get("POST_STORY_EVERY"))

bot_token = os.environ.get("BOT_TOKEN")
log_to_tg_str = os.environ.get("LOG_TO_TG")
log_to_tg = ast.literal_eval(log_to_tg_str) if log_to_tg_str else False
log_tg_channel_str = os.environ.get("LOG_TG_CHANNEL")
log_tg_channel = int(log_tg_channel_str) if log_tg_channel_str else None

# Pre-define some variables and methods
extensions = ['*.png', '*.jpg', '*.jpeg']
tags_filename = "tags.txt"
stories_dir = os.path.join(images_dir, "!STORIES")
no_images_message = "No files left. Skipping iteration..."

terminate_signal_received = False


# signal handler for termination signals
def signal_handler(sig, frame):
    global terminate_signal_received
    print(f"Received signal {sig}! Stopping...")
    terminate_signal_received = True


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


def convert_to_jpg(path):
    print("Converting PNG to JPG...")
    png_image = Image.open(path)
    rgb_image = png_image.convert('RGB')
    output_file_path = path[:-4] + ".jpg"
    rgb_image.save(output_file_path, quality=100)
    os.remove(path)
    print("Converted to JPG")

    return output_file_path


def get_hashtags(path) -> str:
    result = hashtags
    tags_path = os.path.join(path, tags_filename)
    if os.path.isfile(tags_path):
        with open(tags_path, "r") as f:
            content = f.read()
            result += ' '
            result += content

    # randomize hashtags to prevent ig auto-posting detection
    split = result.split(' ')
    random.shuffle(split)
    result = ' '.join(split)

    return result


def try_post_image_from(client, path, is_story) -> (str, str):
    # Choosing a random file from the subfolder
    images_list = get_images_at(path)
    image = random.choice(images_list)
    print("Selected file: ", image)

    # Getting the full path of the file
    selected_image_path = os.path.join(path, image)

    # If the file is PNG, convert it to JPG
    if image.endswith(".png"):
        selected_image_path = convert_to_jpg(selected_image_path)

    # Manage hashtags
    caption = get_hashtags(path) if is_story else None

    # Uploading the file as a post with a caption
    if is_story:
        story = client.photo_upload_to_story(selected_image_path)
        url = f"https://www.instagram.com/stories/{login}/{story.pk}/"
    else:
        media = client.photo_upload(selected_image_path, caption=caption)
        media_code = media.dict().get("code")
        url = f"https://www.instagram.com/p/{media_code}/"
    print("Uploaded")

    return url, selected_image_path


async def log_message(bot, message):
    if bot is not None:
        await bot.send_message(chat_id=log_tg_channel, text=message, parse_mode=telegram.constants.ParseMode.HTML)


async def log_file(bot, message, file_path):
    if bot is not None:
        await bot.send_photo(chat_id=log_tg_channel, photo=open(file_path, 'rb'), caption=message, parse_mode=telegram.constants.ParseMode.HTML)


def login_to_ig() -> Client:
    client = Client()

    try:
        print("Logging in...")
        client.login(login, password)
        print("Logged in as", login)
    except Exception as e:
        print(e)
        print("⛔️ Failed to log in. Terminating...")
        exit()

    return client


async def select_and_post(ig, tg, is_story):
    directory = stories_dir if is_story else images_dir
    images = get_images_at(directory)
    total = len(images)
    total_images_left = max(0, total - 1)
    print(f"Total number of images left: {total_images_left}")

    # Keep the cycle running even if there are no files in the folder
    # to prevent painful re-logging operation
    if total == 0:
        print(no_images_message)
        await log_message(tg, f"⚠️ <b>{login}</b>: {no_images_message}")
    else:
        # Posting image from the root folder
        post_url, image_path = try_post_image_from(ig, directory, is_story)
        post_type = "story" if is_story else "picture"
        await log_file(tg,
                       f"<b>{login}</b>: New {post_type} was posted!\nImages left: {total_images_left}\n{post_url}",
                       image_path)
        os.remove(image_path)


async def select_and_post_from_subfolders(ig, tg, subfolders):
    # Build up the map
    images_map = {}
    for subfolder in subfolders:
        files = get_images_at(subfolder)
        images_map[subfolder] = len(files)

    # Calculate total number of images left
    total = sum(images_map.values())
    total_images_left = max(0, total - 1)
    print(f"Total number of images left: {total_images_left}")

    # Keep the cycle running even if there are no files in the folder
    # to prevent painful re-logging operation
    if total == 0:
        print(no_images_message)
        await log_message(tg, f"<b>{login}</b>: {no_images_message}")
    else:
        # Choosing a random subfolder with actual images
        non_empty_subfolders = [key for key, value in images_map.items() if value != 0]
        category = random.choice(non_empty_subfolders)
        category_name = os.path.basename(os.path.normpath(category))
        images_in_category_left = images_map[category] - 1
        print("Selected category: ", category_name)
        print(f"Number of images left in the category: {images_in_category_left}")

        # Posting image from the selected category
        post_url, image_path = try_post_image_from(ig, category, False)
        await log_file(tg,
                       f"<b>{login}</b>: New image was posted!\nCategory: {category_name}\nImages left: {images_in_category_left} ({total_images_left})\n{post_url}",
                       image_path)
        os.remove(image_path)


# >>> MAIN LOOP <<<
async def main():
    global terminate_signal_received
    story_counter = 1 if post_story_every > 0 else -1

    # Creating an instances of social network clients
    ig_client = login_to_ig()
    tg_bot = telegram.Bot(token=bot_token) if log_to_tg is True else None

    try:
        while True:
            # Getting the list of subfolders
            subfolders = [f.path for f in os.scandir(images_dir) if f.is_dir() and not f.name.startswith('!')]

            # One root folder logic
            print("Posting a picture...")
            if len(subfolders) == 0:
                await select_and_post(ig_client, tg_bot, False)
            # Subfolders logic
            else:
                await select_and_post_from_subfolders(ig_client, tg_bot, subfolders)

            # Posting stories
            if os.path.isdir(stories_dir):
                print("Posting a story...")
                if story_counter > 1:
                    story_counter -= 1
                elif story_counter > 0:
                    await select_and_post(ig_client, tg_bot, True)
                    story_counter = post_story_every

            # Waiting for some time (in seconds)
            t = get_random_time_window(repeat_time, repeat_window)
            print(f"Waiting {t} seconds...")

            # Run until termination signal is received or an exception occurs
            while not terminate_signal_received and t > 0:
                t -= loop_time
                await asyncio.sleep(loop_time)
                
            if terminate_signal_received:
                break

    except asyncio.CancelledError:
        print("Cancelled!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Termination...")
        await log_message(tg_bot, f"⛔️ <b>{login}</b> was terminated!")


if __name__ == '__main__':
    asyncio.run(main())
