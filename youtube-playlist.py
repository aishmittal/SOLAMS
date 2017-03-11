""" Pull All Youtube Videos from a Playlist """

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import configparser
config = configparser.ConfigParser()
config.read('cfg.ini')

DEVELOPER_KEY = config['YOUTUBE']['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = config['YOUTUBE']['YOUTUBE_API_SERVICE_NAME']
YOUTUBE_API_VERSION = config['YOUTUBE']['YOUTUBE_API_VERSION']

import sqlite3

conn = sqlite3.connect('solams.db')
TABLE_NAME="students"
cursor = conn.cursor()


def fetch_all_youtube_videos(playlistId):
    """
    Fetches a playlist of videos from youtube
    We splice the results together in no particular order

    Parameters:
        parm1 - (string) playlistId
    Returns:
        playListItem Dict
    """
    youtube = build(YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
    res = youtube.playlistItems().list(
    part="snippet",
    playlistId=playlistId,
    maxResults="50"
    ).execute()

    nextPageToken = res.get('nextPageToken')
    while ('nextPageToken' in res):
        nextPage = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlistId,
        maxResults="50",
        pageToken=nextPageToken
        ).execute()
        res['items'] = res['items'] + nextPage['items']

        if 'nextPageToken' not in nextPage:
            res.pop('nextPageToken', None)
        else:
            nextPageToken = nextPage['nextPageToken']

    return res

if __name__ == '__main__':
    # comedy central playlist, has 332 video
    # https://www.youtube.com/watch?v=tJDLdxYKh3k&list=PLD7nPL1U-R5rDpeH95XsK0qwJHLTS3tNT
    courseid = 5
    conn = sqlite3.connect('solams.db')
    TABLE_NAME="students"
    cursor = conn.cursor()
    playlistId = "PLUl4u3cNGP63B2lDhyKOsImI7FjCf6eDW"
    videos = fetch_all_youtube_videos(playlistId)
    items = videos['items']
    
    for i,item in enumerate(items):
        
        titlelbl = item['snippet']['title']
        if ":" in titlelbl:
            title = titlelbl.split(':')[1][1:]
        elif "." in titlelbl:
            title = titlelbl.split('.')[1][1:]
        else:
            title = titlelbl
        
                
        
        print title
        print titlelbl
        videoid = item['snippet']['resourceId']['videoId']
        url = 'https://www.youtube.com/embed/'+ videoid + '?list=' + playlistId 

        comm = """UPDATE lectures\
        SET title ='%s', titlelbl = '%s', videoid = '%s', url = '%s'\
        WHERE courseid = %d AND lectureno = %d""" %(title,titlelbl,videoid,url,courseid,i+1)
        #print comm
        conn.execute(comm)
        conn.commit() 


