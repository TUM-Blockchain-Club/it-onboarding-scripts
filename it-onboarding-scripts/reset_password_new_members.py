import base64
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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

# Load environment variables from a custom .env file location if provided
custom_env_path = sys.argv[1] if len(sys.argv) > 1 else None
if custom_env_path:
    load_dotenv(custom_env_path)
else:
    load_dotenv()

# Define the required scopes for accessing user directory API and sending emails
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/gmail.send'
]

# Function to generate a random password using a secure cryptographic random function
def generate_random_password(length=12):
    # Define the set of characters to use in the password (letters, digits, punctuation)
    characters = string.ascii_letters + string.digits + string.punctuation
    # Use the 'secrets' library to generate a cryptographically secure random password
    return ''.join(secrets.choice(characters) for i in range(length))

# Function to send an email notification to the user's secondary email address using Gmail API
def send_notification_email(service, secondary_email, user_email, new_password):
    # Load the email template from an HTML file
    with open('../resources/reset_password_template.html', 'r') as template_file:
        template_content = template_file.read()
    template = Template(template_content)

    # Render the template with dynamic values
    body = template.render(user_email=user_email, new_password=new_password)

    # Create the email message
    message = MIMEMultipart()
    message['to'] = secondary_email
    message['subject'] = "Password Reset Notification"
    message.attach(MIMEText(body, 'html'))

    # Encode the message in a format suitable for the Gmail API
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    # Send the email using Gmail API
    try:
        service.users().messages().send(userId='me', body=raw_message).execute()
        print(f"Notification email sent to {secondary_email}.")
    except Exception as e:
        print(f"Failed to send notification email to {secondary_email}: {str(e)}")

# Function to reset the password for a specific user
def reset_password(admin_service, gmail_service, user_email):
    # Generate a new random password for the user
    new_password = generate_random_password()
    try:
        # Update the user's password using the Admin SDK API
        # Set 'changePasswordAtNextLogin' to True so the user must change their password on next login
        admin_service.users().update(
            userKey=user_email,
            body={'password': new_password, 'changePasswordAtNextLogin': True}
        ).execute()
        print(f"Password for {user_email} has been reset successfully.")

        # Retrieve the user's details to get the secondary email
        user = admin_service.users().get(userKey=user_email).execute()
        # Extract secondary email from the 'emails' field where 'type' is 'work' and it's not the primary email
        secondary_email = next((email['address'] for email in user.get('emails', []) if
                                 not email.get('primary', False)), None)
        if secondary_email:
            # Send a notification email to the secondary email address
            send_notification_email(gmail_service, secondary_email, user_email, new_password)
        else:
            print(f"No secondary email found for {user_email}.")
    except Exception as e:
        # Handle any errors that occur during the API request
        print(f"Failed to reset password for {user_email}: {str(e)}")

# Load email list from file or environment variable
EMAIL_LIST_FILE = os.getenv('EMAIL_LIST_FILE')
email_list = []

# Check if an email list file is provided and exists
if EMAIL_LIST_FILE and os.path.exists(EMAIL_LIST_FILE):
    # Read the email addresses from the file
    with open(EMAIL_LIST_FILE, 'r') as file:
        email_list = [line.strip() for line in file.readlines()]
else:
    # If no file is provided, try to load email addresses from an environment variable
    EMAILS = os.getenv('EMAILS')
    if EMAILS:
        # Split the comma-separated email addresses into a list
        email_list = EMAILS.split(',')

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

    # Build the service objects for interacting with the Admin SDK API and Gmail API
    admin_service = build('admin', 'directory_v1', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)

    # Reset passwords for each email in the list
    for email in email_list:
        reset_password(admin_service, gmail_service, email)

if __name__ == '__main__':
    main()
