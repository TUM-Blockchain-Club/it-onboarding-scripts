import os
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import base64

# File path constants
CSV_FILE = '../resources/participants.csv'
TOKEN_FILE = '../resources/token.json'
CREDENTIALS_FILE = '../resources/credentials.json'
EMAIL_TEMPLATE_FILE = '../resources/team_info_email_template.html'
DISCORD_CHANNEL_NAME = '#it-onboarding-wise-2425'

# Define the required scopes for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Function to send an email to a participant using Gmail API
def send_email(service, receiver_email, name, team, code, teammates):
    # Load the email template from an HTML file
    with open(EMAIL_TEMPLATE_FILE, 'r') as template_file:
        template_content = template_file.read()
    template = Template(template_content)

    # Render the template with dynamic values
    body = template.render(name=name, team=team, code=code, teammates=teammates, discord_channel_name=DISCORD_CHANNEL_NAME)

    # Create the email message
    message = MIMEMultipart()
    message['to'] = receiver_email
    message['subject'] = "Urgent: Appointment as Temporary Detectives"
    message.attach(MIMEText(body, 'html'))

    # Encode the message in a format suitable for the Gmail API
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    # Send the email using Gmail API
    try:
        service.users().messages().send(userId='me', body=raw_message).execute()
        print(f"Email sent to {receiver_email}.")
    except Exception as e:
        print(f"Failed to send email to {receiver_email}: {str(e)}")

# Function to load participant information from CSV file
def load_participants(csv_file):
    participants = []
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            participants.append(row)
    return participants

# Function to group participants by team
def group_participants_by_team(participants):
    teams = {}
    for participant in participants:
        team = participant['Team']
        if team not in teams:
            teams[team] = []
        teams[team].append(participant)
    return teams

def main():
    """Authenticates the user and sends team information emails to participants."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # Build the Gmail service object
    gmail_service = build('gmail', 'v1', credentials=creds)

    # Load participants from CSV
    participants = load_participants(CSV_FILE)
    # Group participants by team
    teams = group_participants_by_team(participants)

    # Send email to each participant
    for participant in participants:
        name = participant['Name']
        email = participant['Email']
        team = participant['Team']
        code = participant['Code']
        teammates = [p['Name'] for p in teams[team] if p['Email'] != email]
        send_email(gmail_service, email, name, team, code, teammates)

if __name__ == '__main__':
    main()
