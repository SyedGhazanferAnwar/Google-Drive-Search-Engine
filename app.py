import os
import flask
import httplib2
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import queue
from WorkerThread import Worker
from flask import jsonify

app = flask.Flask(__name__)
NUM_OF_THREADS=10

# Dummy route
@app.route('/')
def index():
    return "Home Page"

# To delete Existing token, so /authenticate will reauthenticate
@app.route("/delete_token")
def delete_token():
    if os.path.exists("credentials.json"):
        os.remove("credentials.json")   
    return jsonify(Message="Sucessfully Deleted",status=200)

# To actually authenticate the user GDrive access 
@app.route('/authenticate')
def authenticate():
    credentials = get_credentials()
    if credentials == False:
        return flask.redirect(flask.url_for('oauth2callback'))
    elif credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        return jsonify(Message="Already Authenticated",client_id=credentials.client_id,status=200)


# Part of /authenticate internally used for user GDrive access 
@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('client_id.json',
            scope='https://www.googleapis.com/auth/drive',
            redirect_uri=flask.url_for('oauth2callback', _external=True)) # access drive api using developer credentials
    flow.params['include_granted_scopes'] = 'true'
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        open('credentials.json','w').write(credentials.to_json()) # write access token to credentials.json locally
        return jsonify(Message="Authentication Sucessfull",client_id=credentials.client_id,status=200)


# Initates the request to download all files of authenticated GDrive
@app.route("/download_files")
def download_files():
    
    credentials=get_credentials()
    if credentials == False:
        return jsonify(Message="Authentication Failed",status=403)

    all_files = fetch(credentials,sort='modifiedTime desc')
    que = queue.Queue()
    
    for file in all_files:
        que.put_nowait(file)

    for _ in range(NUM_OF_THREADS):
        Worker(que,credentials).start()
    que.join() 

    return jsonify(Message="Downloaded Sucessfully",client_id=credentials.client_id,status=200)



# Part of /authenticate, Utility function for checking the credentials validity
def get_credentials():
    credential_path = 'credentials.json'
    store = Storage(credential_path)
    credentials = store.get()
    # credentials=None 
    if not credentials or credentials.invalid:
        print("Credentials not found.")
        return False
    else:
        print("Credentials fetched successfully.")
        return credentials


# Utility function for querying files in Gdrive
def fetch(credentials,sort='modifiedTime desc'):
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('drive', 'v3', http=http)
	results = service.files().list(orderBy=sort,pageSize=10,fields="nextPageToken, files(id, name)").execute()
	items = results.get('files', [])
	return items


if __name__ == '__main__':
    app.run()
