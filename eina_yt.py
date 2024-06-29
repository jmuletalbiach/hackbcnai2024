#EINA TRCP
"""
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

def download_youtube_video(url):
    # Descargar el video de YouTube
    yt = YouTube(url)
    video_title = yt.title
    video_stream = yt.streams.get_highest_resolution()
    video_filename = f"{video_title}.mp4"
    video_stream.download(filename=video_filename)

    # Obtener la transcripción del video
    video_id = yt.video_id
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = "\n".join([entry['text'] for entry in transcript])
        transcript_filename = f"{video_title}.txt"
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
    except Exception as e:
        print(f"No se pudo obtener la transcripción: {e}")

    print(f"Video descargado como: {video_filename}")
    print(f"Transcripción guardada como: {transcript_filename}")

# URL del video de YouTube
youtube_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Reemplaza con la URL del video que desees
download_youtube_video(youtube_url)

"""

import environment_var
import os
from googleapiclient.discovery import build
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from datetime import datetime, timedelta




# Configura tu clave de API de YouTube y credenciales de Google Cloud
API_KEY = environment_var.variable_key_ricard  # Revariable_key_ricard emplaza con tu clave de API de YouTube
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = environment_var.variable_ruta_credentials  # Reemplaza con la ruta a tu archivo JSON de credenciales

def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def get_videos_from_channel(youtube, channel_id, start_date, end_date):
    videos = []
    next_page_token = None
    while True:
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            publishedAfter=start_date,
            publishedBefore=end_date,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        for item in response['items']:
            if item['id']['kind'] == 'youtube#video':
                videos.append(item['id']['videoId'])
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return videos

def download_audio(video_id):
    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
    video_title = yt.title.replace("/", "_")  # Reemplazar caracteres no permitidos en nombres de archivo
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_filename = f"{video_title}.mp4"
    audio_stream.download(filename=audio_filename)
    return audio_filename, video_title

def convert_audio_to_wav(audio_filename):
    wav_filename = audio_filename.replace(".mp4", ".wav")
    os.system(f"ffmpeg -i {audio_filename} -ac 1 -ar 16000 {wav_filename}")
    return wav_filename

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"Archivo {source_file_name} subido a {destination_blob_name}.")

def transcribe_gcs(gcs_uri):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=90)
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + "\n"
    return transcript

def save_transcription(video_id, bucket_name):
    try:
        audio_filename, video_title = download_audio(video_id)
        wav_filename = convert_audio_to_wav(audio_filename)
        
        gcs_uri = f"gs://{bucket_name}/{wav_filename}"
        upload_to_gcs(bucket_name, wav_filename, wav_filename)
        
        transcript = transcribe_gcs(gcs_uri)
        transcript_filename = f"{video_title}.txt"
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(transcript)
        print(f"Transcripción guardada como: {transcript_filename}")

    except Exception as e:
        print(f"Error al procesar el video: {e}")

def main():
    # ID del canal de YouTube (puedes encontrarlo en la URL del canal)
    channel_id = 'UCy-EInfqJ08c_hU5VFzcODQ'  # Reemplaza con el ID del canal que desees
    start_date = datetime(2007, 1, 1).isoformat("T") + "Z"
    end_date = datetime(2023, 12, 31).isoformat("T") + "Z"
    bucket_name = 'tu-nombre-de-bucket'  # Reemplaza con el nombre de tu bucket de Google Cloud Storage

    youtube = get_youtube_client(API_KEY)
    video_ids = get_videos_from_channel(youtube, channel_id, start_date, end_date)

    for video_id in video_ids:
        # Primero intentamos con youtube_transcript_api
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = "\n".join([entry['text'] for entry in transcript])
            video_title = YouTube(f'https://www.youtube.com/watch?v={video_id}').title.replace("/", "_")
            transcript_filename = f"{video_title}.txt"
            with open(transcript_filename, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            print(f"Transcripción guardada como: {transcript_filename}")
        except (TranscriptsDisabled, NoTranscriptFound):
            print("Transcripción no disponible, utilizando Google Cloud Speech-to-Text")
            save_transcription(video_id, bucket_name)
        except Exception as e:
            print(f"Error al obtener la transcripción: {e}")

if __name__ == "__main__":
    main()
