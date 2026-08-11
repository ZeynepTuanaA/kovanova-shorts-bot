import os
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube'a yükleme yapmak için gerekli kapsam (scope)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    # Token dosyası daha önce alınmış erişim belirteçlerini saklar
    if os.path.exists("youtube_token.json"):
        creds = Credentials.from_authorized_user_file("youtube_token.json", SCOPES)
        
    # Eğer geçerli bir kimlik bilgisi yoksa kullanıcıya giriş yaptır
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Süresi dolmuş token yenileniyor...")
            creds.refresh(Request())
        else:
            print("Tarayıcı açılarak YouTube izni alınacak...")
            if not os.path.exists("client_secrets.json"):
                raise FileNotFoundError(
                    "HATA: 'client_secrets.json' dosyası bulunamadı!\n"
                    "Google Cloud Console üzerinden YouTube Data API v3 yetkili bir OAuth 2.0 İstemci Kimliği indirip "
                    "Kovanova_Shorts klasörüne 'client_secrets.json' olarak kaydetmelisiniz."
                )
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Sonraki kullanımlar için token'ı kaydet
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

    # Güncel tarih (Örn: 24 Ekim)
    today = datetime.datetime.now()
    date_str = f"{today.day} {today.strftime('%B')}"
    
    # Şimdilik varsayılan başlık ve açıklama. İleride script_generator'dan da çekilebilir.
    title = f"Günün Astroloji Mesajı ✨ Kader Çarkı Senin İçin Dönsün! #astroloji #shorts"
    description = (
        "Günlük gizemli astroloji mesajınız.\n\n"
        "Abone olmayı unutmayın!\n\n"
        "#astroloji #burçlar #gizem #shorts #keşfet"
    )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["astroloji", "burçlar", "shorts", "gizem", "koç burcu", "aslan burcu", "yay burcu"],
            "categoryId": "24" # Entertainment
        },
        "status": {
            "privacyStatus": "public", # Test başarılı olduğu için artık Public yüklüyoruz.
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"'{title}' başlıklı video yükleniyor...")
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()
    
    video_id = response.get("id")
    print(f"✅ Video başarıyla yüklendi!")
    print(f"🔗 Video Linki: https://youtube.com/shorts/{video_id}")

if __name__ == "__main__":
    upload_video()
