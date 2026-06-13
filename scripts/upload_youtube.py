"""
Step 3: Upload work/short.mp4 (always) and work/long.mp4 (Sundays only)
to YouTube via Data API v3.
"""

import os
import json
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_ID = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]

creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_uri="https://oauth2.googleapis.com/token",
)

youtube = build("youtube", "v3", credentials=creds)

with open("work/topic.json") as f:
    topic = json.load(f)

title = topic["title"]
year = topic.get("year", "")


def upload(path, title, description, is_short):
    tags = ["FIFA World Cup", "football", "soccer", "cinematic", "highlights"]
    if is_short:
        tags.append("Shorts")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "17",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading {path}: {int(status.progress() * 100)}%")

    print(f"Uploaded {path} -> https://youtu.be/{response['id']}")
    return response["id"]


short_title = f"{title} #Shorts"
short_desc = (
    f"A cinematic moment from FIFA World Cup history ({year}).\n\n"
    "#FIFAWorldCup #Football #Shorts #Cinematic"
)
upload("work/short.mp4", short_title, short_desc, is_short=True)

if datetime.datetime.utcnow().weekday() == 6:
    long_title = f"World Cup Cinematic Recap — {title}"
    long_desc = (
        f"This week's cinematic journey through FIFA World Cup history, "
        f"featuring moments from {year} and beyond.\n\n"
        "#FIFAWorldCup #Football #Cinematic"
    )
    upload("work/long.mp4", long_title, long_desc, is_short=False)
else:
    print("Not Sunday -- skipping long-form upload.")
