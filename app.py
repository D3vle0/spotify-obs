from flask import Flask, request, redirect, session
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
    if "token" in session:
        try:
            headers = {
                'Authorization': f'Bearer {session["token"]}',
            }

            response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
            return response.json()
        except:
            return 'check token or play music'
    return '<h1>spotify</h1><a href="/login">login</a>'

@app.route('/login')
def authorize():
    state = generate_random_string(16)
    scope = 'user-read-private user-read-email user-read-currently-playing' # replace with your client id
      # replace with your redirect uri

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
        # return redirect('/')
        session['token'] = response.json()['access_token']
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(port=8888, debug=1)