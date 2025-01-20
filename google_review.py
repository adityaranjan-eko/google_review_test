import os
import json
import google.auth
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask import Flask, redirect, url_for, request, session, jsonify
import sys

# Set up Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace with your client secrets file path from Google Cloud Console
# CLIENT_SECRETS_FILE = "client_secret_496487939262-sedfkmh5mqra7lnqarastbj7kdfl78kc.apps.googleusercontent.com.json"  # Sadanand
CLIENT_SECRETS_FILE = "sample.json"   # project- google analytics, app- ThinnkAI

# OAuth 2.0 scopes you need to request
SCOPES = ['https://www.googleapis.com/auth/business.manage']

# Initialize OAuth flow
flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='https://google-review-test.onrender.com/oauth2callback'
)

# Google My Business API service
mybusiness_service = None

# Home route
@app.route('/')
def home():
    if 'credentials' not in session:
        print("AAAAAAAAAAAAA")
        print(session.__dict__)
        return redirect(url_for('login'))
    print("BBBBBBBBBBBBBBBB")
    print(session.__dict__)
    return 'Welcome to your Google Reviews Platform. <a href="/reviews">View Reviews</a>'

# Login route
@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    print("CCCCCCCCCCCCC")
    print(session.__dict__)
    return redirect(authorization_url)

# OAuth callback route
@app.route('/oauth2callback')
def oauth2callback():
    print("Here in oauthcallback")
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    print("DDDDDDDDDDDDDDDDDDDD")
    print(session.__dict__)
    
    return redirect(url_for('reviews'))

# Route to fetch Google reviews
@app.route('/reviews')
def reviews():
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    
    # Refresh credentials if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = credentials_to_dict(credentials)
    
    # Create Google My Business API client
    service = build('mybusinessbusinessinformation', 'v1', credentials=credentials)
    
    # List businesses (locations)
    accounts = service.accounts().list().execute()
    
    if not accounts['accounts']:
        return 'No Google My Business accounts found.'

    # Assuming the first account and location is the one to fetch reviews for
    account_id = accounts['accounts'][0]['name']
    location_id = 'locations_id'  # Replace with actual location ID
    
    reviews = service.accounts().locations().reviews().list(parent=f'{account_id}/{location_id}').execute()

    return jsonify(reviews)

# Route to reply to a review
@app.route('/reply_review/<review_id>', methods=['POST'])
def reply_review(review_id):
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    
    # Refresh credentials if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = credentials_to_dict(credentials)
    
    # Create Google My Business API client
    service = build('mybusinessbusinessinformation', 'v1', credentials=credentials)
    
    account_id = 'accounts/{account_id}'
    location_id = 'locations/{location_id}'

    reply_text = request.json.get('reply_text')
    reply = {
        "comment": reply_text
    }
    
    # Respond to the review
    service.accounts().locations().reviews().reply(
        parent=f'{account_id}/{location_id}/reviews/{review_id}',
        body=reply
    ).execute()

    return jsonify({"message": "Reply posted successfully!"})

# Helper function to convert credentials to dictionary
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    # app.run(ssl_context=('cert.pem', 'key.pem'),debug=True)
    host = '0.0.0.0'
    port = 5000
    # Allow passing arguments from the command line
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    app.run(host=host, port=port, debug=True)
