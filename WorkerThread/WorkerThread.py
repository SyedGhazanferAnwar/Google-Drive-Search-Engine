import threading
import queue
import os
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from apiclient import discovery
from oauth2client.file import Storage
import io
import httplib2

class Worker(threading.Thread):
    def __init__(self, que,credentials, *args, **kwargs):
        self.que = que
        self.credentials=credentials
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                file = self.que.get()  # 3s timeout then close the thread timeout=3
            except queue.Empty:
                return
            file_id=file["id"]
            file_name=file["name"]

            # To avoid downloading files that already exists
            if not os.path.exists(os.path.join("Data",file_name)):
                print(f"${file_name} downloading")
                self.download_file(file_id,file_name)

            # Task done for notifying que.join()
            self.que.task_done()

    def download_file(self,file_id, output_file):
        try:
            credentials = self.credentials
            http = credentials.authorize(httplib2.Http())
            service = discovery.build("drive", "v3", http=http)
            request = service.files().get_media(fileId=file_id)
            fh = open(os.path.join("Data",output_file),"wb")
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print ("Download %d%%." % int(status.progress() * 100))
            fh.close()
        except Exception as e:
            print(e)

