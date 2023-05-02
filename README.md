# spotify-pl

Cheeky script for creating and updating monthly playlists. 

If playlists not yet created, script creates them and populates with all liked songs from the corresponding months.

If playlists already created, adds new liked songs.

Month at which to start creating playlists can be specified in command line argument, e.g.
```
python create_and_update.py 2023-01
```

Spotify secret information is specified in `spotify_secrets.py`