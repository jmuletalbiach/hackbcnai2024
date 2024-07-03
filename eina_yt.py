#EINA TRCP

"""
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

def download_youtube_video(url):
    try:
        # Configuración de opciones para yt-dlp
        ydl_opts = {'format': 'best', 'outtmpl': '%(title)s.%(ext)s'}
        
        # Descargar el video de YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'video')
            video_filename = f"{video_title}.mp4"
            print(f"Video descargado como: {video_filename}")

        ####PER OBTENIR LA TRANSCRIPCIÓ DEL VIDEO.
        
        video_id = info_dict.get('id')
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = "\n".join([entry['text'] for entry in transcript])
            transcript_filename = f"{video_title}.txt"
            with open(transcript_filename, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            print(f"Transcripción guardada como: {transcript_filename}")
        except Exception as e:
            print(f"No se pudo obtener la transcripción: {e}")
        
    except yt_dlp.utils.DownloadError as e:
        print(f"Error al descargar el video: {e}")
    except Exception as e:
        print(f"Error desconocido: {e}")

# URL del video de YouTube (enlace permanente)
youtube_url = 'https://www.youtube.com/watch?v=nuXFAoU188c&list=PLvIaFuGCd7G-oUHRnwMY2E-lxEhmQLQdu&index=6'  # Reemplaza con la URL del video que desees
download_youtube_video(youtube_url)

"""

import os
from pytube import YouTube
from google.cloud import storage, speech
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:\\Users\\jmule\\prova\\hardy-antonym-427911-g8-1a6c0736010a.json"

def descarregar_audio_desde_video(url_video):
    yt = YouTube(url_video)
    titol_video = yt.title.replace("/", "_")
    stream_audio = yt.streams.filter(only_audio=True).first()
    nom_fitxer_audio = f"{titol_video}.mp4"
    stream_audio.download(filename=nom_fitxer_audio)


def convertir_audio_a_wav(nom_fitxer_audio):
    nom_fitxer_wav = nom_fitxer_audio.replace(".mp4", ".wav")
    os.system(f"ffmpeg -i {nom_fitxer_audio} -ac 1 -ar 16000 {nom_fitxer_wav}")
    if not os.path.exists(nom_fitxer_wav):
        raise FileNotFoundError(f"No s'ha creat correctament l'arxiu WAV {nom_fitxer_wav}.")
    return nom_fitxer_wav

def pujar_a_google_storage(nom_bucket, nom_fitxer_origen, nom_blob_desti):
    client_emmagatzematge = storage.Client()
    cubell = client_emmagatzematge.bucket(nom_bucket)
    blob = cubell.blob(nom_blob_desti)
    blob.upload_from_filename(nom_fitxer_origen)
    print(f"Fitxer {nom_fitxer_origen} pujat a {nom_blob_desti}.")

def pujar_text_a_google_storage(nom_bucket, contingut_texte, nom_blob_desti):
    client_emmagatzematge = storage.Client()
    cubell = client_emmagatzematge.bucket(nom_bucket)
    blob = cubell.blob(nom_blob_desti)
    blob.upload_from_string(contingut_texte)
    print(f"Fitxer de transcripció pujat a {nom_blob_desti}.")

def transcriure_audio_google_storage(uri_gcs):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=uri_gcs)
    configuracio = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ca-ES",
    )
    operacio = client.long_running_recognize(config=configuracio, audio=audio)
    resposta = operacio.result(timeout=90)
    transcripcio = ""
    for resultat in resposta.results:
        transcripcio += resultat.alternatives[0].transcript + "\n"
    return transcripcio

def desar_transcripcio_video(url, nom_bucket):
    try:
        nom_fitxer_audio, titol_video = descarregar_audio_desde_video(url)
        nom_fitxer_wav = convertir_audio_a_wav(nom_fitxer_audio)
        
        uri_gcs = f"gs://{nom_bucket}/{nom_fitxer_wav}"
        pujar_a_google_storage(nom_bucket, nom_fitxer_wav, nom_fitxer_wav)
        
        transcripcio = transcriure_audio_google_storage(uri_gcs)
        nom_blob_transcripcio = f"{titol_video}.txt"
        pujar_text_a_google_storage(nom_bucket, transcripcio, nom_blob_transcripcio)
        print(f"Transcripció desada al núvol com a: {nom_blob_transcripcio}")

    except Exception as e:
        print(f"S'ha produït un error en processar el vídeo: {e}")

def principal(urls_videos, nom_bucket):
    for url_video in urls_videos:
        id_video = url_video.split("v=")[1]
        try:
            transcripcio = YouTubeTranscriptApi.get_transcript(id_video)
            text_transcripcio = "\n".join([entrada['text'] for entrada in transcripcio])
            titol_video = YouTube(url_video).title.replace("/", "_")
            nom_blob_transcripcio = f"{titol_video}.txt"
            pujar_text_a_google_storage(nom_bucket, text_transcripcio, nom_blob_transcripcio)
            print(f"Transcripció desada al núvol com a: {nom_blob_transcripcio}")
        except (TranscriptsDisabled, NoTranscriptFound):
            print("Transcripció no disponible, utilitzant Google Cloud Speech-to-Text..")
            desar_transcripcio_video(url_video, nom_bucket)
        except Exception as e:
            print(f"S'ha produït un error en obtenir la transcripció: {e}")

if __name__ == "__main__":
    urls_videos = [
        "https://www.youtube.com/watch?v=TgcgRo_HrHg",
        "https://www.youtube.com/watch?v=m_3q3XnLlTI",
    ]
    nom_bucket = 'hackbcnai2024'
    principal(urls_videos, nom_bucket)
