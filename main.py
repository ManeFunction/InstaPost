import os
import shutil
import fnmatch
import random
import time
from dotenv import load_dotenv
from instabot import Bot

# set up environment
load_dotenv()

# load config
login = os.environ.get("LOGIN")
passw = os.environ.get("PASS")
hashtags = os.environ.get("HASHTAGS")
images_dir = os.environ.get("PATH")
repeat_time = int(os.environ.get("TIME"))

def upload():
	# try to get a random image and upload it
	if os.listdir(images_dir):
		image = images_dir + random.choice(os.listdir(images_dir))
		bot = Bot()
		bot.login(username = login, password = passw)
		bot.upload_photo(image, caption = hashtags)

def pre_clean_up():
	dir = "config"
	# checking whether config folder exists or not
	if os.path.exists(dir):
		try:
			# removing it because in 2021 it makes problems with new uploads
			shutil.rmtree(dir)
		except OSError as e:
			print("Error: %s - %s." % (e.filename, e.strerror))

def post_clean_up():
	# remove already uploaded pictures to prevent duplicates
	for file in os.listdir(images_dir):
		if fnmatch.fnmatch(file, '*REMOVE_ME'):
			os.remove(images_dir + file)

def job():
	pre_clean_up()
	upload()
	post_clean_up()
	
if __name__ == '__main__':
	while True:
		job()
		time.sleep(repeat_time)