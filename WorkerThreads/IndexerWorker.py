import threading
import queue
import os
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from apiclient import discovery
from oauth2client.file import Storage
import io
import httplib2
import textract


class IndexerWorker(threading.Thread):
    def __init__(self, que, *args, **kwargs):
        self.que = que
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                filename = self.que.get(timeout=3)  # 3s timeout then close the thread timeout=3
            except queue.Empty:
                return
            print("Threaded   "+filename)
            text = textract.process(filename)
            print(text)
            # Do task here
            # Task done for notifying que.join()
            self.que.task_done()


