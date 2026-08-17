import os
import json
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube'a yükleme yapmak için gerekli kapsam (scope)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    if os.path.exists("youtube_token.json"):
        creds = Credentials.from_authorized_user_file("youtube_token.json", SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Süresi dolmuş token yenileniyor...")
            creds.refresh(Request())
        else:
            print("Tarayıcı açılarak YouTube izni alınacak...")
            if not os.path.exists("client_secrets.json"):
                raise FileNotFoundError("HATA: 'client_secrets.json' dosyası bulunamadı!")
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open("youtube_token.json", "w") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_video():
    print("YouTube API servisine bağlanılıyor...")
    youtube = get_authenticated_service()

    file_path = "final_short.mp4"
    if not os.path.exists(file_path):
        print(f"HATA: Yüklenecek video bulunamadı: {file_path}")
        return

    # Scriptten burç adını al
    sign_name = "Kova"
    if os.path.exists("current_script.json"):
        try:
            with open("current_script.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                script = data.get("script", "")
                for s in ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]:
                    if s.lower() in script.lower()[:30]:
                        sign_name = s
                        break
        except Exception:
            pass

    title = f"{sign_name} Burcu İçin Kozmik Mesaj ✨ Kader Çarkı Senin İçin Dönsün! #shorts #astroloji"
    description = (
        f"{sign_name} burcu için bugünün astroloji mesajı ve kozmik rehberliği.\n\n"
        "Kader çarkı senin için dönsün! ✨\n\n"
        f"#astroloji #{sign_name.lower()}burcu #burçlar #gizem #shorts #keşfet"
    )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["astroloji", "burçlar", "shorts", "gizem", f"{sign_name.lower()} burcu", "kova burcu", "günlük burç"],
            "categoryId": "24" # Entertainment
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"'{title}' başlıklı video YouTube'a yükleniyor...")
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()
    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"✅ Video başarıyla yüklendi!")
    print(f"🔗 Video Linki: {video_url}")
    return video_url

if __name__ == "__main__":
    upload_video()
