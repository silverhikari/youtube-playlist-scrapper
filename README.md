# youtube-playlist-scrapper

scrapes a youtube playlist via youtube apiv3 using an google api key and generates a json feed for rss purposes.

this use 1 quota for to get playlist details such as title, description, along with channel id and channel name and 1 quote for every 50 items in a playlist, so for a playlist of 150 items it would cost 4 quota.

> [!IMPORTANT]
> this script requires a google api key. if you do not know how to set one up check inside script.

> [!CAUTION]
> this script only works on public playlists

## Requirements

* python 3.9+
* [google-api-python-client](https://github.com/googleapis/google-api-python-client) v2.194.x or greater

## Usage

### RSSGuard

place script in a folder(recommended called scripts) under the user data folder of rssguard.

switch to advanced mode when adding feed and set type to JSON.

set source to script and in the box add:
`python %data%/scripts/youtube-playlist-scrapper.py youtube_playlist_url`

> [! NOTE]
> currently you need to run the script twice on first creation of feed. 1. to get metadata, 2. to get items.

### Standalone

the script can be run standalone via piping the output into a json file.

`python youtube-playlist-scrapper.py youtube_playlist_url > feed.json`

## Problems

if script malfunctions check the status field in the feed explorer of rssguard or the terminal when running standalone.

four known issues that will be displayed via stderr:

* google client api is not installed or available to the system python
* no youtube-api-key.txt file is found (the program will generate this file next to the script if it is not found)
* no google api key located in youtube-api-key.txt
* invalid youtube url
* invalid google api key

anything else post an issue
