#!/usr/bin/python

import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


import os
import sys
import httplib2
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.cloud.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "youtube/client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = ['https://www.googleapis.com/auth/youtube.upload']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
OAUTH2_FILE = 'youtube/oauth2.json'

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.cloud.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service_na():
    credentials = None
    OAUTH2_FILE = 'youtube/oauth3.json'  # Path to your OAuth2 file
    CLIENT_SECRETS_FILE = 'youtube/client_secrets.json'  # Path to your client secrets file
    YOUTUBE_UPLOAD_SCOPE = ['https://www.googleapis.com/auth/youtube.upload']
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    # Check if the credentials file exists
    if os.path.exists(OAUTH2_FILE):
        credentials = Credentials.from_authorized_user_file(OAUTH2_FILE, YOUTUBE_UPLOAD_SCOPE)

    # If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                # Use the Request object here for the refresh call
                credentials.refresh(Request())
            except RefreshError:
                # Handle the case where the refresh attempt fails
                os.remove(OAUTH2_FILE)
                return get_authenticated_service_na()  # Restart authentication process
        else:
            # No valid credentials, initiate login process
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=YOUTUBE_UPLOAD_SCOPE)
            credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(OAUTH2_FILE, 'w') as token:
                token.write(credentials.to_json())

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def initialize_upload_na(youtube, options):
    tags = options.get('keywords', [])  # Assume it's already a list

    body = {
        "snippet": {
            "title": options['title'],
            "description": options['description'],
            "tags": tags,
            "categoryId": options['category']
        },
        "status": {
            "privacyStatus": options['privacyStatus']
        }
    }

    # Create the media file upload object
    media_body = MediaFileUpload(options['file'], chunksize=-1, resumable=True)

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media_body
    )

    # Synchronously handle the upload
    response = resumable_upload_na(insert_request)

    # Assuming resumable_upload returns the video ID after upload is complete
    return response  # Return the video ID

def resumable_upload_na(insert_request):
    response = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print("Video id '%s' was successfully uploaded." % response['id'])
                return response['id']  # Return the video ID once the upload is successful
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                print("A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
            else:
                raise  # Reraise non-retriable HTTP errors
        except RETRIABLE_EXCEPTIONS as e:
            print("A retriable error occurred: %s" % e)

        if retry >= MAX_RETRIES:
            print("No longer attempting to retry.")
            raise Exception("Max retries reached")

        retry += 1
        sleep_seconds = random.random() * (2 ** retry)  # Exponential backoff with jitter
        print("Sleeping %f seconds and then retrying..." % sleep_seconds)
        time.sleep(sleep_seconds)

        
        
def youtube(path: str, title: str, description: str, category: str, keywords: str, privacyStatus: str, made_for_kids: bool=False):
    if not os.path.exists(path):
        exit("Please specify a valid file.")

    if privacyStatus not in VALID_PRIVACY_STATUSES:
        exit(f"Invalid privacy status. Choose one of {VALID_PRIVACY_STATUSES}.")

    # Create an options dictionary to pass around the parameters
    options = {
        "file": path,
        "title": title,
        "description": description,
        "category": category,
        "keywords": keywords.split(','),  # Assuming keywords is a comma-separated string
        "privacyStatus": privacyStatus,
        "made_for_kids": made_for_kids,
    }

    print("Getting authenticated service...")
    youtube = get_authenticated_service_na()  # Changed to synchronous call
    
    try:
        print("Trying to upload...")
        video_id = initialize_upload_na(youtube, options)  # Changed to synchronous call
        print(f"Uploaded! video at: https://www.youtube.com/watch?v={video_id}")
        return f"https://www.youtube.com/watch?v={video_id}"  # Construct and return the video URL
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        

    