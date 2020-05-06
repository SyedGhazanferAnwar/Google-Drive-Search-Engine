# import threading
# import queue
# import os
# from apiclient.http import MediaIoBaseDownload, MediaFileUpload
# from apiclient import discovery
# from oauth2client.file import Storage
# import io
# import httplib2
# import textract


# class IndexerWorker(threading.Thread):
#     def __init__(self, que, *args, **kwargs):
#         self.que = que
#         super().__init__(*args, **kwargs)
#     def run(self):
#         while True:
#             try:
#                 filepath = self.que.get(timeout=3)  # 3s timeout then close the thread timeout=3
#             except queue.Empty:
#                 return
#             # print("Threaded   "+filename)
#             text = textract.process(filepath)
#             text=str(text, 'utf-8', 'ignore')
#             pre, ext = os.path.splitext(os.path.basename(filepath))
#             with open(os.path.join("Data","ExtractedText",pre+".txt"),"w") as f:
#                 f.write(text)
#             # print(text)
#             # Task done for notifying que.join()
#             self.que.task_done()


