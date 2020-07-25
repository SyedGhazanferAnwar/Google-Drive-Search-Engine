# Google-Drive-Search-Engine
This is a complete google drive search engine API based on Flask using the Tf-Idf algorithm. The program is capable of searching through word, pdf, images (via OCR), ppt and many more file types.

## Steps to run
1. Clone the repo, install the requirements.txt.
2. Then get your client_id.json from the google dashboard and use redirect URI as `http://localhost:5000/oauth2callback`. Place the client_id.json in the auth folder, replacing the already existing one.
3. Run the app by running command `python app.js`, visit URL `http://localhost:5000/authenticate` to authenticate from your google drive.
4. Visit URL `http://localhost:5000/download_files` to download all files to your pc from the Gdrive.
5. To, extract the text from ppt, jpg, png, word, txt, pdf files visit the URL `http://localhost:5000/extract_text`, and to run Tf-IDf across the extracted text visit `index_files`. Now, your files are searchable. You can search for data within your files by hitting url `http://localhost:5000/search?query=testSearch` with the get parameter of `query`.

