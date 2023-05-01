import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotify_secrets import *
from datetime import datetime, timedelta
import pandas as pd
from dateutil import parser, tz, relativedelta
import sys

def main():
    if len(sys.argv) > 1: 
        start_date = datetime.strptime(sys.argv[1], '%Y-%m').replace(tzinfo=tz.tzutc())
    
    else:
        start_date = datetime(datetime.now().year, (datetime.now().month - 1) % 12, 1).replace(tzinfo=tz.tzutc())

    print(f'Start date: {start_date.date()}')

    scopes = [
        'user-library-read',
        'playlist-modify-private',
        'playlist-modify-public',
    ]
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scopes,
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI
        )
    )
    print('Spotify connection established')
    liked_songs_raw = []
    offset = 0
    while len(liked_songs_raw) == 0 or parser.parse(liked_songs_raw[-1]['added_at']) > start_date:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        
        liked_songs_raw = liked_songs_raw + results['items']

        offset+=50
    print('Liked song info obtained')

    current_user_id = sp.current_user()['id']
    liked_tracks_df = pd.DataFrame([
        {
            'dt_added': parser.parse(song['added_at']),
            'uri': song['track']['uri']
        } 
        for song 
        in liked_songs_raw
    ])
    months_to_consider = pd.date_range(start_date, liked_tracks_df['dt_added'].max(), freq='MS')

    try:
            with open('created_playlists.csv', 'x') as created_playlists_csv:
                    created_playlists_csv.write('year,month,id\n')
            print('Created \'created_playlists.csv\' file')
    except:
            print('\'created_playlists.csv\' file already exists')

    created_playlists_df = pd.read_csv('created_playlists.csv')
        
    for year, month in zip(months_to_consider.year, months_to_consider.month):
        month_liked_track_uris = liked_tracks_df.query(
            f'dt_added.dt.year == {year} &'
            f'dt_added.dt.month == {month}'
        ).iloc[::-1]['uri'] # reverse order

        year_month_string = datetime(year, month, 1).strftime('%b %y')
        
        if (year, month) not in zip(created_playlists_df['year'], created_playlists_df['month']):
            print(f'{year_month_string}: No record of existing playlist; creating and adding liked songs')
            playlist_create_results = sp.user_playlist_create(
                user=current_user_id, 
                name=year_month_string
            )
            playlist_id = playlist_create_results['id']
            sp.playlist_add_items(
                playlist_id=playlist_id,
                items=month_liked_track_uris
            )
            with open('created_playlists.csv', 'a') as created_playlists_csv:
                created_playlists_csv.write(f'{year},{month},{playlist_id}\n')
        else:
            print(f'{year_month_string}: Playlist already exists')
            playlist_id = created_playlists_df.query(f'year == {year} & month == {month}')['id'].values[0]
            
            # playlist_tracks() max limit is 100; if we have more than 100 songs in the month
            # playlist already we must get the track info in several batches.
            playlist_track_items = []
            need_to_get_more_tracks = True
            while need_to_get_more_tracks:
                track_items_batch = sp.playlist_tracks(
                    playlist_id=playlist_id,
                    limit=100,
                    offset=len(playlist_track_items)
                )['items']
                playlist_track_items = playlist_track_items + track_items_batch
                need_to_get_more_tracks = len(track_items_batch) == 100

            uris_already_in_playlist = [
                item['track']['uri'] 
                for item
                in sp.playlist_tracks(playlist_id=playlist_id)['items']
            ]

            uris_not_yet_in_playlist = list(
                set(month_liked_track_uris)
                .difference(set(uris_already_in_playlist))
            )
            num_new_uris = len(uris_not_yet_in_playlist)
            if num_new_uris != 0:
                print(' ' * (len(year_month_string) + 2) + f'Adding new liked songs ({num_new_uris})')
                sp.playlist_add_items(
                    playlist_id=playlist_id,
                    items=uris_not_yet_in_playlist
                )

if __name__ == '__main__':
    main()
