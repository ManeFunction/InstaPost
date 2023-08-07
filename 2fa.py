from dotenv import load_dotenv  # Parameters environment
import os  # A module for interacting with the operating system
import pyotp  # A Python library for generating OTP codes

# set up environment
load_dotenv()

# load config
secret = os.environ.get("SECRET")

totp = pyotp.TOTP(secret)
code = totp.now()
print(code)
