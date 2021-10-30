import requests
import datetime
import json
import base64
from urllib.parse import urlencode
import webbrowser
import math

from requests.api import request
from requests.models import Response


client_id = 'c375df047821412cb70857a90119ebeb'
client_secret = 'd6a1d84044754343b07b2ae4758bd5b6'


class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    authentic_token = None
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def request_auth(self):
        redirect_url = "https://www.google.com"
        response_type = "code"
        client_id = self.client_id
        scope = "playlist-modify playlist-modify-public"
        request_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type={response_type}&redirect_uri={redirect_url}&scope={scope}"
        r = webbrowser.open(request_url)
        
        redirected_code_url = input("Enter the redirected URL: ")  

        if (redirected_code_url == ""):
            raise Exception("Enter a valid URL!")      

        redirect_code = redirected_code_url.split('=')[1]

        post_url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code",
            "code": redirect_code,
            "redirect_uri":"https://www.google.com"
        }

        token_data = {
            "grant_type": "authorization_code", 
            "code": redirect_code, 
            "redirect_uri": redirect_url
            }

        client_creds = f"{client_id}:{client_secret}"
        
        client_cred_b64 = base64.b64encode(client_creds.encode())
        
        token_header = {
            "Authorization": f"Basic {client_cred_b64.decode()}"
        }

        returned = requests.post(post_url, data = token_data, headers=token_header)
        return_data = returned.json()

        if (returned.status_code not in range(200,299)):
            raise Exception("Access code is invalid, enter the correct URL.")
        else:
            print("Access token accepted! \n")  

        authentic_token = return_data['access_token']

        return authentic_token

    def get_Artist_ID(self, access_token):
        query = input("Enter the name of the Artist you would like: ")
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        endpoint = "https://api.spotify.com./v1/search"
        data = urlencode({"q": query, "type": "artist"})
        lookup_url = f"{endpoint}?{data}"
        return_data = requests.get(lookup_url, headers=headers)
        artist_data = return_data.json()

        artist_id = artist_data.get("artists").get("items")[0].get("id")

        if (return_data.status_code not in range(200,299)):
            raise Exception("Search failed!")

        return [artist_id, query]

    def get_User_ID(self, access_token):
        endpoint = "https://api.spotify.com/v1/me"
        header = {
            "Authorization": f"Bearer {access_token}"
        }

        id_data = requests.get(endpoint, headers = header).json()
        user_id = id_data.get('id')

        return user_id


    def create_playlist(self):
        access_token = self.request_auth()
        user_id = self.get_User_ID(access_token)
        artist_info = self.get_Artist_ID(access_token)

        request_body = {
            "name": f"A Compilation of {artist_info[1]}",
            "description": f"A playlist made up of {artist_info[1]}'s best tracks!"
        }
        
        query = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        
        header = {
            "Authorization": f"Bearer {access_token}"
        }
      
        r = requests.post(query, data = json.dumps(request_body), headers = header)
        playlist_data = r.json()

        if (r.status_code not in range(200,299)):
            raise Exception("Playlist creation failed.")
        else:
            print("Playlist created!")

        playlist_id = playlist_data.get("id")

        header = {
            "Authorization": f"Bearer {access_token}",
        }

        limit = 50
        market = "CA"
        groups = "album,single,appears_on"
        artist_endpoint = f"https://api.spotify.com/v1/artists/{artist_info[0]}/albums?include_groups=album,single&limit={limit}&market={market}"
        albums_response = requests.get(artist_endpoint, headers = header)
        album_data = albums_response.json()

        all_albums = []
        album_names = []
        
        print("Please wait while we add your songs!")

        for i in range(len(album_data.get("items"))):
            album_id = album_data.get("items")[i].get("id")
            album_name = album_data.get("items")[i].get("name")

            if album_name in album_names or "Remix" in album_name:
                duplicate = True 
            else:
                duplicate = False        
                album_names.append(album_name)
                     
            if duplicate == False:
                all_albums.append(album_id)

        self.add_to_playlist(access_token, self.get_albums_songs(access_token, all_albums), playlist_id)
        

    def get_albums_songs(self, access_token, all_albums):
        market = "CA"
        all_songs = []
        limit = 50

        header = {
            "Authorization": f"Bearer {access_token}"
        }


        song_names = []
        for album in all_albums:
            query = f"https://api.spotify.com/v1/albums/{album}/tracks?limit={limit}&market={market}"
            album_request = requests.get(query, headers = header)
            data = album_request.json()

            for i in range(len(data.get("items"))):
                song_uri = data.get("items")[i].get("uri")
                song_name = data.get("items")[i].get("name")

                if song_name in song_names or "Remix" in song_name:
                    duplicate = True 
                else:
                    duplicate = False        
                    song_names.append(song_name)
                     
                if duplicate == False:
                    all_songs.append(song_uri)

        return all_songs

    def add_to_playlist(self, access_token, all_songs, playlist_id):
        query = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        header = {
            "Authorization": f"Bearer {access_token}"
        }

        post_nums = math.ceil(len(all_songs) / 100)

        for i in range(0,post_nums):

            request_body = {
                "uris": all_songs[i*100:i*100+100]
            }

            add_song = requests.post(query, data = json.dumps(request_body), headers= header)

            if(add_song.status_code not in range(200,299)):
                print(add_song.json())
            else:
                num_of_songs = len(all_songs[i*100:i*100+100])
                print(f"{num_of_songs} songs added")
            
client = SpotifyAPI(client_id, client_secret)
client.create_playlist()