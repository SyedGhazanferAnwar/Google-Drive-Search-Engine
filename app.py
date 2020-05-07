import os
import flask
import httplib2
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import queue
from WorkerThreads.DownloadWorker import DownloadWorker
from WorkerThreads.TextExtractWorker import TextExtractWorker
# from WorkerThreads.IndexerWorker import IndexerWorker
from flask import jsonify,request
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

app = flask.Flask(__name__)
NUM_OF_THREADS=10
downloadQueue = queue.Queue()
textExtractQueue = queue.Queue()
vectorizer=TfidfVectorizer()
# Dummy route
@app.route("/")
def index():
    return "Home Page"

# To delete Existing token, so /authenticate will reauthenticate
@app.route("/delete_token")
def delete_token():
    if os.path.exists(os.path.join(".auth","credentials.json")):
        os.remove(os.path.join(".auth","credentials.json"))   
    return jsonify(Message="Sucessfully Deleted",status=200)

# To actually authenticate the user GDrive access 
@app.route("/authenticate")
def authenticate():
    credentials = get_credentials()
    if credentials == False:
        return flask.redirect(flask.url_for("oauth2callback"))
    elif credentials.access_token_expired:
        return flask.redirect(flask.url_for("oauth2callback"))
    else:
        return jsonify(Message="Already Authenticated",client_id=credentials.client_id,status=200)


# Part of /authenticate internally used for user GDrive access 
@app.route("/oauth2callback")
def oauth2callback():
    flow = client.flow_from_clientsecrets(os.path.join(".auth","client_id.json"),
            scope="https://www.googleapis.com/auth/drive",
            redirect_uri=flask.url_for("oauth2callback", _external=True)) # access drive api using developer credentials
    flow.params["include_granted_scopes"] = "true"
    if "code" not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get("code")
        credentials = flow.step2_exchange(auth_code)
        open(os.path.join(".auth","credentials.json"),"w").write(credentials.to_json()) # write access token to credentials.json locally
        return jsonify(Message="Authentication Sucessfull",client_id=credentials.client_id,status=200)


# Initates the request to download all files of authenticated GDrive
@app.route("/download_files")
def download_files():
    
    credentials=get_credentials()
    if credentials == False:
        return jsonify(Message="Authentication Failed",status=403)

    all_files = fetch(credentials,sort="modifiedTime desc")
    with open(os.path.join("Data","rawLinks.txt"),"a+") as f:
        for _file in all_files:
            f.write(_file["name"]+" "+_file["webViewLink"]+"\n")
            downloadQueue.put_nowait(_file)

    for _ in range(NUM_OF_THREADS):
        DownloadWorker(downloadQueue,credentials).start()
    downloadQueue.join() 

    return jsonify(Message="Downloaded Sucessfully",client_id=credentials.client_id,status=200)

# Using textract to extract the text from files in Data/raw (Only works in linux/Mac with config)
@app.route("/extract_text")
def extract_text():
    for filename in glob.glob(os.path.join("Data","raw","*")):
        textExtractQueue.put_nowait(filename)
    for _ in range(NUM_OF_THREADS):
        TextExtractWorker(textExtractQueue).start()

    return jsonify(Message="Text Extraction Started",status=200)


@app.route("/index_files")
def index_files():
    #vectorizer = TfidfVectorizer()
    filesPath,data=getDatasetFromFiles()
    trainedModel = vectorizer.fit_transform(data)

    # Saving the Vectorized TF-IDF (Indexed)
    with open(os.path.join("Data",'trainedModel.pkl'), 'wb') as trainedModelFile:
        pickle.dump(trainedModel, trainedModelFile)                      

    # Saving the Corresponding fileNames
    with open(os.path.join("Data",'filesPath.pkl'), 'wb') as _file:
        pickle.dump(filesPath,_file)
 
    return jsonify(Message="Indexing Completed Sucessfully",status=200)

# The text to search in the documents
@app.route("/search")
def search():
    with open(os.path.join("Data","trainedModel.pkl"), "rb") as trainedModelFile:
        trainedModel = pickle.load(trainedModelFile)
    with open(os.path.join("Data","filesPath.pkl"), "rb") as _file:
        filesPath = pickle.load(_file)
    #vectorizer=TfidfVectorizer()
    query = request.args.get("query")
    query = "image and"
    query_vec = vectorizer.transform([query])
    results = cosine_similarity(trainedModel,query_vec).reshape((-1,))
    print(results)
    for i in results.argsort()[-10:][::-1]:
        print(filesPath[i]+"    Score: "+str(results[i]))
    return "Don"




# Part of /authenticate, Utility function for checking the credentials validity
def get_credentials():
    credential_path = os.path.join(".auth","credentials.json")
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        print("Credentials not found.")
        return False
    else:
        print("Credentials fetched successfully.")
        return credentials


# Utility function for querying files in Gdrive
def fetch(credentials,sort="modifiedTime desc"): 
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)
    results = service.files().list(orderBy=sort,pageSize=1000,fields="nextPageToken, files(id, name,webViewLink)").execute()
    items = results.get("files", [])
    return items

# Utility function for combining all files text in one large list
def getDatasetFromFiles():
    files=[]
    dataset=[]
    # TODO: Change ExtractedText to raw then manually change ext to txt and append original
    for _file in glob.glob(os.path.join("Data","raw","*")):
        # print(_file)
        pre, ext = os.path.splitext(os.path.basename(_file))
        with open(os.path.join("Data","ExtractedText",pre+".txt"), 'rb') as f:
            files.append(os.path.basename(_file))
            dataset.append(str(f.read(), 'utf-8', 'ignore'))
    # print(dataset)
    # print(len(dataset))
    return (files,dataset)


if __name__ == "__main__":
    if not os.path.exists("Data"):
        os.mkdir("Data")
    if not os.path.exists(os.path.join("Data","ExtractedText")):
        os.mkdir(os.path.join("Data","ExtractedText"))
    if not os.path.exists(os.path.join("Data","raw")):
        os.mkdir(os.path.join("Data","raw"))
    app.run()
