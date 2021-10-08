import requests
import datetime
from urllib.parse import urlencode
import base64
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
from matplotlib import pyplot as plt

#insert your id and secret for connection to API
client_id = '<here goes your client id>'
client_secret = '<here goes your client secret'

#create a class for connection to API
class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now() #if there is a token, it must expire now.
    access_token_did_expire = True                 #it is expired by default
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        """
        return a string codified in Base64
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must insert a valid id and secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }
    
    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        } 
    
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers) #making a POST request
        if r.status_code not in range(200, 299): #if the status code in between 200 and 299 it was a successful request
            raise Exception("Autenticazione fallita")
        data = r.json() #getting data from POST request in JSON format
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] # seconds
        expires = now + datetime.timedelta(seconds=expires_in) #when will the token expire?
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now #check where the token is expired or not
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token() 
        return token
    
    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers
        
        
    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')
    
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')
    
    def search(self, query, search_type='artist'): #by default, we'll search for an artist
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        data = urlencode({"q":query, "type":search_type.lower()}) #it must be in lower case, otherwise will give an error
        lookup_url = f"{endpoint}?{data}" #formatting the url
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):  #if the status code in between 200 and 299 it was a successful request
            return {}
        return r.json()

spotify = SpotifyAPI(client_id, client_secret)
spotify.search(query="Post Malone", search_type='artist')

#insert id and secret
client_id = '<here goes your client id>'
client_secret = '<here goes your client secret'

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

#a method that get tracks from a given playlist
def getTrackIDs(user, playlist_id):
    ids = []
    playlist = sp.user_playlist(user, playlist_id)
    for item in playlist['tracks']['items']:
        track = item['track']
        ids.append(track['id'])
    return ids

ids = getTrackIDs('7r0cXaVKRQ6IGSqj_NYJ5Q', '37i9dQZEVXbMDoHDwVN2tF')

#a method that gets features for every track in a playlist, such as name, artist, popularity ect
def getTrackFeatures(id):
    meta = sp.track(id) #track's metadata
    features = sp.audio_features(id) #features of the given song
    
    
    #metadata
    name = meta['name']
    album = meta['album']['name']
    artist = meta['album']['artists'][0]['name']
    artist_id = meta['album']['artists'][0]['id']
    release_date = meta['album']['release_date']
    lenght = meta['duration_ms']
    popularity = meta['popularity']
    genres = genreArtist(meta['album']['artists'][0]['name'])[0]
    
    #features
    acousticness = features[0]['acousticness']
    danceability = features[0]['danceability']
    energy = features[0]['energy']
    instrumentalness = features[0]['instrumentalness']
    liveness = features[0]['liveness']
    loudness = features[0]['loudness']
    speechiness = features[0]['speechiness']
    
    #return every metadata and features of the track
    track = [name, album, artist, artist_id, release_date, lenght, popularity, genres, danceability, acousticness, energy, instrumentalness, liveness, loudness, speechiness]
    return track

#method that return genres of an artist
def genreArtist(name):
    risultato = sp.search(q=name, type='artist')['artists']['items'][0]['genres']
    type(risultato)
    return risultato
    
#method that gets features of every song in a playlist, put it in a Pandas DataFrame and also download it as a .csv file
tracks = []
for i in range(len(ids)):
    time.sleep(.5)
    track = getTrackFeatures(ids[i])
    tracks.append(track)
    
    #create a DataFrame using our data and exporting it in .csv
    df = pd.DataFrame(tracks, columns = ['name', 'album', 'artist', 'artist_id', 'release_date', 'lenght', 'popularity', 'genres', 'danceability', 'acousticness', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness'])
    #df.to_csv("spotify.csv", sep= ',')

df.sort_values(by='popularity', ascending=False).head()
df.describe().drop('count', axis=0)
#analysis
plt.figure(figsize=(8,8))
my_labels = df['genres'].unique()
df.groupby('genres')['genres'].count().plot.pie(labels=None)
plt.legend(loc="lower left", labels=my_labels, bbox_to_anchor=(1.0,0.1))
plt.title("Number of songs by genre", fontsize=20)
plt.show()

df["genres"].replace({"australian pop": "pop", "bedroom pop": "pop", "brooklyn drill" : "drill"}, inplace=True)
df["genres"].replace({"cali rap": "rap", "canadian contemporary r&b": "r&b", "canadian hip hop" : "hip hop"}, inplace=True)
df["genres"].replace({"canadian pop": "pop", "colombian pop": "pop", "country rap" : "rap", "dance pop" : "pop"}, inplace=True)
df["genres"].replace({"melodic rap": "rap", "north carolina hip hop": "hip hop", "nz pop" : "pop"}, inplace=True)
df["genres"].replace({"latin pop": "pop", "pop rap": "rap"}, inplace=True)

plt.figure(figsize=(8,8))
my_labels = df['genres'].unique()
df.groupby('genres')['genres'].count().plot.pie(labels=None)
plt.legend(loc="lower left", labels=my_labels, bbox_to_anchor=(1.0,0.1))
plt.title("Number of songs by genre", fontsize=20)
plt.show()

plt.figure(figsize=(8,8))
df.groupby('genres')['popularity'].mean().plot.bar()
plt.grid()
plt.title("Mean popularity by genre", fontsize=20)
plt.show()