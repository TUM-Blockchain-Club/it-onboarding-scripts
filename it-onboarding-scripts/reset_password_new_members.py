import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import secrets
import string
import sys

# Load environment variables from a custom .env file location if provided
custom_env_path = sys.argv[1] if len(sys.argv) > 1 else None
if custom_env_path:
    print("Loading custom .env")
    load_dotenv(custom_env_path)
else:
    load_dotenv()

# Define the required scope for accessing user directory API
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']

# Function to generate a random password using a secure cryptographic random function
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

# Function to reset the password for a specific user
def reset_password(service, user_email):
    # Generate a new random password for the user
    new_password = generate_random_password()
    try:
        # Update the user's password using the Admin SDK API
        # Set 'changePasswordAtNextLogin' to True so the user must change their password on next login
        service.users().update(
            userKey=user_email,
            body={'password': new_password, 'changePasswordAtNextLogin': True}
        ).execute()
        print(f"Password for {user_email} has been reset successfully.")
    except Exception as e:
        # Handle any errors that occur during the API request
        print(f"Failed to reset password for {user_email}: {str(e)}")

# Load email list from file or environment variable
EMAIL_LIST_FILE = os.getenv('EMAIL_LIST_FILE')
email_list = []

# Check if an email list file is provided and exists
if EMAIL_LIST_FILE and os.path.exists(EMAIL_LIST_FILE):
    # Read the email addresses from the file
    print(f"Reading the file {EMAIL_LIST_FILE}")
    with open(EMAIL_LIST_FILE, 'r') as file:
        email_list = [line.strip() for line in file.readlines()]
    print(f"Imported {len(email_list)} emails from {EMAIL_LIST_FILE}")
else:
    # If no file is provided, try to load email addresses from an environment variable
    EMAILS = os.getenv('EMAILS')
    if EMAILS:
        print(f"Reading the environment variable EMAILS")
        # Split the comma-separated email addresses into a list
        email_list = EMAILS.split(',')
        print(f"Imported {len(email_list)} emails from environment variable")

def main():
    """Authenticates the user and resets passwords for the given list of emails."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('../resources/token.json'):
        creds = Credentials.from_authorized_user_file('../resources/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../resources/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../resources/token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the service object for interacting with the Admin SDK API
    service = build('admin', 'directory_v1', credentials=creds)

    # Reset passwords for each email in the list
    for email in email_list:
        reset_password(service, email)

if __name__ == '__main__':
    main()
