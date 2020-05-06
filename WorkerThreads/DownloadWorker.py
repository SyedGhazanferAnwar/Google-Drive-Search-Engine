import threading
import queue
import os
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from apiclient import discovery
from oauth2client.file import Storage
import io
import httplib2


class DownloadWorker(threading.Thread):
    def __init__(self, que,credentials, *args, **kwargs):
        self.que = que
        self.credentials=credentials
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                _file = self.que.get(timeout=3)  # 3s timeout then close the thread timeout=3
            except queue.Empty:
                return
            file_id=_file["id"]
            file_name=_file["name"]

            # To avoid downloading files that already exists
            if not os.path.exists(os.path.join("Data","raw",file_name)) and self.validFile(_file["name"]):
                print(f"${file_name} downloading")
                self.download_file(file_id,file_name)

            # Task done for notifying que.join()
            self.que.task_done()

    def validFile(file_name):
        supportedExt=[".csv",".doc",".docx",".epub",".eml",".gif",".jpg",".jpeg",".json",".html",
        ".htm",".mp3",".msg",".odt",".ogg",".pdf",".png",".pptx",".ps",".rtf",".tiff",".tif",".txt",
        ".wav",".xlsx",".xls"]
        pre, ext = os.path.splitext(os.path.basename(_file))
        print(ext)
        if ext in supportedExt:
            return True
            
        return False
        


    def download_file(self,file_id, output_file):
        try:
            credentials = self.credentials
            http = credentials.authorize(httplib2.Http())
            service = discovery.build("drive", "v3", http=http)
            request = service.files().get_media(fileId=file_id)
            fh = open(os.path.join("Data","raw",output_file),"wb")
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print ("Download %d%%." % int(status.progress() * 100))
            fh.close()
        except Exception as e:
            print(e)

