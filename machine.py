import spotipy
from flask import Flask, request, url_for, redirect, session
from spotipy.oauth2 import SpotifyOAuth
import time
from datetime import datetime



app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'notsecretkey'

TOKEN_INFO = 'token_info'


@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('monthlyRecap', _external=True))
#Monthly Recap
@app.route('/monthlyRecap')
def monthlyRecap():
    try:
        token_info = get_token()
    except:
        print("Failed")
        return redirect('/')
    #Access spotipy
    sp = spotipy.Spotify(auth=token_info['access_token'])
    username = sp.current_user()['id']
    #Get users top tracks for the month
    top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')['items']

    #Get top 5 tracks and Artists
    result = ""
    top5artists = []
    tracksTop = []
    for track in top_tracks:
        result += f"Track: {track['name']} by {track['artists'][0]['name']}<br>"
    for tracks in top_tracks[:5]:
        artist = (tracks['artists'][0]['id'])
        if artist not in top5artists:
            top5artists.append(artist)
        tracksA = (tracks['id'])
        tracksTop.append(tracksA)
    now = datetime.now()
    current_month_name = now.strftime("%B")


    new_playlist = sp.user_playlist_create(username,  current_month_name + ' Recap', public=True)
    saved_weekly_playlist_id = new_playlist['id']
    song_uris = [song['uri'] for song in top_tracks]
    sp.user_playlist_add_tracks(username, saved_weekly_playlist_id, song_uris, position=None)
    top5 = top5artists[:4]
    top5songs = tracksTop[:(5 - len(top5))]

    #Recommendation from top 5 songs/artists

    songs = sp.recommendations(limit = 10,seed_artists=top5,seed_tracks= top5songs)
    song_uris1 = [track['uri'] for track in songs['tracks']]
    sp.user_playlist_add_tracks(username, saved_weekly_playlist_id,  song_uris1, position=None)
    return "Monthly Recap playlist saved!"

#Token indo
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return redirect(url_for('login', _external=False))

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id='id',
        client_secret='secret',
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-top-read user-library-read playlist-modify-public playlist-modify-private user-read-recently-played'
    )


if __name__ == '__main__':
    app.run(debug=True)
