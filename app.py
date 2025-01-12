from flask import Flask, render_template, request
import os
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Charger la clé API YouTube depuis un fichier
with open('api_youtube.txt', 'r') as f:
    API_KEY = f.read().strip()

def get_download_folder():
    """Retourne le chemin du dossier Téléchargements par défaut de l'utilisateur."""
    return os.path.join(os.path.expanduser('~'), 'Downloads')

# Fonction pour rechercher des vidéos sur YouTube
def search_youtube(query, max_results=10):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.search().list(q=query, part='snippet', type='video', maxResults=max_results)
        response = request.execute()
        return response.get('items', [])
    except Exception as e:
        print(f"Erreur lors de la recherche sur YouTube : {e}")
        return []

# Fonction pour télécharger une vidéo YouTube avec yt-dlp
def download_youtube_video(url):
    try:
        output_path = get_download_folder()
        os.makedirs(output_path, exist_ok=True)  # Crée le dossier s'il n'existe pas

        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',  # Fusionner en MP4
            'noplaylist': True,
            'cachedir': False,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'overwrites': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return f"Vidéo téléchargée : {info_dict.get('title', '')}"
    except Exception as e:
        return f"Erreur lors du téléchargement : {e}"

# Fonction pour rechercher des documents sur des sites fiables
def search_documents(query, max_results=10):
    try:
        query = f"{query} filetype:pdf site:.edu OR site:.gov OR site:.org"
        url = f"https://www.google.com/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        
        pdf_links = []
        for link in links:
            href = link['href']
            if re.search(r'\.pdf$', href):
                pdf_links.append(href)
                if len(pdf_links) >= max_results:
                    break
        
        return pdf_links
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la recherche de documents : {e}")
        return []

# Fonction pour télécharger un document
def download_document(url):
    try:
        output_path = get_download_folder()
        os.makedirs(output_path, exist_ok=True)  # Crée le dossier s'il n'existe pas

        if not url.lower().endswith('.pdf'):
            return "Erreur : L'URL fournie n'est pas un fichier PDF."

        response = requests.get(url)
        response.raise_for_status()  # Lève une exception si le statut n'est pas 200

        file_name = os.path.basename(url)
        file_path = os.path.join(output_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return f"Document téléchargé : {file_name}"
    except Exception as e:
        return f"Erreur lors du téléchargement : {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        search_type = request.form['search_type']  # Récupérer le type de recherche
        
        if search_type == 'video':
            videos = search_youtube(query)
            return render_template('index.html', videos=videos, query=query, search_type=search_type)
        elif search_type == 'document':
            documents = search_documents(query)
            return render_template('index.html', documents=documents, query=query, search_type=search_type)
    
    return render_template('index.html')

@app.route('/download_video/<video_id>')
def download_video(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    result = download_youtube_video(url)
    return result

@app.route('/download_document/<path:doc_url>')
def download_document_route(doc_url):
    result = download_document(doc_url)
    return result

if __name__ == '__main__':
    app.run(debug=True)