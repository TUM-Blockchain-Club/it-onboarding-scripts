import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import secrets
import string

# Load environment variables from .env file
load_dotenv()

# Set up the credentials and admin directory service
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

delegated_credentials = credentials.with_subject(ADMIN_EMAIL)

service = build('admin', 'directory_v1', credentials=delegated_credentials)

# Function to generate a random password using a secure cryptographic random function
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

# Function to reset the password for a specific user
def reset_password(user_email):
    new_password = generate_random_password()
    try:
        service.users().update(
            userKey=user_email,
            body={'password': new_password, 'changePasswordAtNextLogin': True}
        ).execute()
        print(f"Password for {user_email} has been reset successfully.")
    except Exception as e:
        print(f"Failed to reset password for {user_email}: {str(e)}")

# Load email list from file or environment variable
EMAIL_LIST_FILE = os.getenv('EMAIL_LIST_FILE')
email_list = []

if EMAIL_LIST_FILE and os.path.exists(EMAIL_LIST_FILE):
    with open(EMAIL_LIST_FILE, 'r') as file:
        email_list = [line.strip() for line in file.readlines()]
else:
    EMAILS = os.getenv('EMAILS')
    if EMAILS:
        email_list = EMAILS.split(',')

# Reset passwords for each email in the list
for email in email_list:
    reset_password(email)
