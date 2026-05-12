#! /usr/bin/env python3

# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "google-api-python-client>=2.194.0",
# ]
# ///

'''
Copyright 2026 Ethan Kerrick

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Youtube API v3 playlist scrapper

VERSION: v2.1.0

this scrapper use the Youtube APIv3 to allow for podcasts/playlists to have more than 15 items, useful if you want to watch a long running series.
this use 1 quota for to get playlist details such as title, description, along with channel id and channel name and 1 quote for every 50 items in a playlist, so for a playlist of 150 items it would cost 4 quota.

!!!THIS REQUIRES A GOOGLE CLOUD API KEY!!!
!!!THIS SCRIPT ONLY WORKS ON PUBLIC PLAYLISTS!!!

Steps:

1. create a project at "console.cloud.google.com", and name it "youtube-rss" or something like that

2. select the newly create project

2. hit the "library" tab on the sidebar, and using the search bar look for "Youtube Data API v3", and enable it for the project

3. go to credentials and click "create credentials" and select api key

4. in sidebar that pops up, name the keys something and under api restrictions select "Youtube Data Api v3"

5. once done click show key, and copy api key

6. either create the file "youtube-api-key.txt" next to this script, and place the generated key into the first line of the file with nothing before or after
(the program will attempt to remove whitespace when reading the key but still better to not add it), or you can run the script first it will generate the file if it is not there

Changelog:

Major.Minor.Fix

Major: anything that changes how users input the url but not a background input change or the addition of optional arguments

Minor: anthing that changes in the program usually on the processing end

Fix: anything that fixes a small issue or problem that isn't bigger than a few lines

version 1.0.0: inital creation

version 1.1.0: modular refactor into functions

version 1.1.1: various fixes with missing sys.exits and correcting with opener using incorrect variable

version 1.2.0: added argparse support instead of basic varg handling

version 2.0.0: added playlist id support in url input

version 2.1.0: added pretty file output support

'''

import json
import sys
import re
from pathlib import Path
import argparse

try:
    from googleapiclient.discovery import build
except(ModuleNotFoundError):
    print("module google-api-python-client not found", file=sys.stderr)
    sys.exit(1)
from googleapiclient.discovery import build, HttpError

current_dir = Path(__file__).resolve().parent
api_file = Path(f"{current_dir}/youtube-api-key.txt")

def get_api_key() -> str:
    if api_file.is_file():
        with open(api_file, 'r', encoding="utf-8") as keyfile:
            API_Key = keyfile.readline().strip()
            if API_Key == "":
                print("no google cloud api key found", file=sys.stderr)
                sys.exit(3)
            else:
                return API_Key
    else:
        with open(api_file, 'w', encoding="utf-8"):
            print("place google api key in youtube-api-key.txt, without any extra characters", file=sys.stderr)
            sys.exit(2)

def get_playlist_details(playlist_id: str, youtube) -> list:
    details = youtube.playlists().list(
        part='snippet',
        id=[playlist_id],
        fields="items(snippet(channelId,title,description,channelTitle))"
    ).execute()
    return details['items']

def get_playlist_videos(playlist_id: str, youtube) -> list:
    videos = []
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
            fields="nextPageToken,items(snippet(publishedAt,title,description,thumbnails(high),resourceId(videoId)))",
        ).execute()
        
        videos.extend(res['items'])
        next_page_token = res.get('nextPageToken')
        
        if not next_page_token:
            break
    return videos

def get_playlist_info(playlist_id) -> tuple:
    try:
        with build('youtube', 'v3', developerKey=get_api_key()) as youtube:
            channel_json = get_playlist_details(playlist_id, youtube)[0]
            playlist_json = get_playlist_videos(playlist_id, youtube)
            return (channel_json, playlist_json)
    except(HttpError):
        print("invalid google api key", file=sys.stderr)
        sys.exit(5)


def generate_json_feed(playlist_info: tuple) -> dict:
    channel_json = playlist_info[0]
    playlist_json = playlist_info[1]
    formatted_items = []
    json_feed = {"version": "https://jsonfeed.org/version/1.1", "title": f"{channel_json["snippet"]["title"]}",
        "home_page_url": f"www.youtube.com/channel/{channel_json["snippet"]["channelId"]}", 
        "description": f"{channel_json["snippet"]["description"]}",
        "authors": [{"name": f"{channel_json["snippet"]["channelTitle"]}", "url": f"www.youtube.com/channel/{channel_json["snippet"]["channelId"]}"}]}             

    for video in playlist_json:
        if f"{video["snippet"]["title"]}" == "Deleted video" or f"{video["snippet"]["title"]}" == "Private video":
            continue
        else:
            item = {"id": f"www.youtube.com/watch?v={video["snippet"]["resourceId"]["videoId"]}", "url": f"https://www.youtube.com/watch?v={video["snippet"]["resourceId"]["videoId"]}/", 
            "title": f"{video["snippet"]["title"]}", "content_text": f"{video["snippet"]["description"]}", "date_published": f"{video["snippet"]["publishedAt"]}",
            "attachments": [{"url": f"{video["snippet"]["thumbnails"]["high"]["url"]}", "mime_type": "image/jpeg", "title":"thumbnail"}]
            }
            formatted_items.append(item)
    json_feed["items"] = formatted_items
    return json_feed

def output_file(filename_path:Path, json_feed):
    filename = filename_path.stem
    suffix = filename_path.suffix
    if suffix == "":
        filename_path = filename_path.with_suffix(".json")
    counter = 1

    while Path.exists(filename_path):
        filename_path = filename_path.with_stem(f"{filename} ({counter})")
        counter += 1
    
    with filename_path.open('w') as json_file:
        json.dump(json_feed, json_file, indent=2)
    sys.exit(f"json feed file created at '{filename_path}'")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("playlist_url", help="url of playlist or id. example: youtube.com/playlist?list=PLnumbers or PLnumbers", type=str)
    parser.add_argument("-o", "--output", help="path of output file, if no suffix is given will default to .json", type=Path)
    args = parser.parse_args()

    if match := re.search(r'^(?:https?:\/\/)?(?:www.)?youtube\.com\/playlist\?list=(PL[A-Za-z0-9_-]{32}|PL[0-9A-F]{14})$', args.playlist_url):
        playlist_id = match.group(1)
    elif match := re.search(r'^(PL[A-Za-z0-9_-]{32}|PL[0-9A-F]{14})$', args.playlist_url):
        playlist_id = match.group(1)
    else: 
        print("invalid youtube url or playlist id", file=sys.stderr)
        sys.exit(4)
    
    json_feed = generate_json_feed(get_playlist_info(playlist_id))
    if args.output and not args.output == "":
            output_file(args.output, json_feed)
    print(json.dumps(json_feed))

if __name__ == "__main__":
    main()
