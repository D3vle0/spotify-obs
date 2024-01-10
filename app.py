from flask import Flask, request, redirect, session, render_template, make_response
from urllib.parse import urlencode
import random
import string
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv(verbose=True)
app = Flask(__name__)
app.secret_key = os.urandom(32)

client_id=os.getenv('CLIENT_ID')
client_secret=os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:8888/callback'

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

@app.route('/')
def main():
    if request.cookies.get('token'):
        # try:
            print(f'access: {request.cookies.get("token")}')
            print(f'refresh: {request.cookies.get("refresh_token")}')
            headers = {
                'Authorization': f'Bearer {request.cookies.get("token")}',
            }

            response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
            if response.status_code == 401 and response.json()['error']['message'] == 'The access token expired':
                refresh_token = request.cookies.get('refresh_token')
                authOptions = {
                    'url': 'https://accounts.spotify.com/api/token',
                    'headers': {
                        'content-type': 'application/x-www-form-urlencoded',
                        'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
                    },
                    'data': {
                        'grant_type': 'refresh_token',
                        'refresh_token': refresh_token
                    }
                }

                response = requests.post(**authOptions)
                print(response.json())
                if response.status_code == 200:
                    resp = make_response(redirect('/'))
                    resp.set_cookie('token', response.json()['access_token'])
                    return resp
                else:
                    return response.content, response.status_code
            response = response.json()
            title = response['item']['name']
            artist = ''
            for i in range(len(response['item']['artists'])):
                artist += f"{response['item']['artists'][i]['name']}, "
            artist = artist[:-2]
            album_art = response['item']['album']['images'][0]['url']
            return render_template('index.html', title=title, artist=artist, album_art=album_art)
        # except:
            return 'check token or play music'
    return '<h1>spotify</h1><a href="/login">login</a>'

@app.route('/login')
def authorize():
    state = generate_random_string(16)
    scope = 'user-read-private user-read-email user-read-currently-playing'

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    }

    return redirect('https://accounts.spotify.com/authorize?' + urlencode(params))

@app.route('/callback')
def callback():
    code = request.args.get('code', None)
    state = request.args.get('state', None)

    if state is None:
        return redirect('/#' + urlencode({'error': 'state_mismatch'}))
    else:
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        auth_options = {
            'url': 'https://accounts.spotify.com/api/token',
            'data': {
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            },
            'headers': {
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Basic ' + auth_header
            }
        }
        response = requests.post(**auth_options)
        resp = make_response(redirect('/'))
        resp.set_cookie('token', response.json()['access_token'])
        resp.set_cookie('refresh_token', response.json()['refresh_token'])
        return resp

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('token', '', expires=0)
    resp.set_cookie('refresh_token', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(port=8888, debug=1)