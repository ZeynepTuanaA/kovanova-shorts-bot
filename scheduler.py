import schedule
import time
import subprocess
import os
import base64

def initialize_secrets():
    # Railway'den gelen Base64 şifreleri dosyalara dönüştür (eğer varsa)
    secrets_map = {
        "GOOGLE_CREDS_B64": "google-credentials.json",
        "YT_CLIENT_SECRETS_B64": "client_secrets.json",
        "YT_TOKEN_B64": "youtube_token.json"
    }
    for env_var, filename in secrets_map.items():
        b64_content = os.environ.get(env_var)
        if b64_content:
            try:
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(b64_content))
                print(f"[+] {filename} oluşturuldu.")
            except Exception as e:
                print(f"[-] {filename} oluşturulamadı: {e}")

# İlk başta secret'ları başlat
initialize_secrets()

# Sistemin kurulduğu dizin (Kovanova_Shorts klasörü)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")

def run_step(script_name):
    """Belirtilen Python betiğini çalıştırır ve sonucunu döner."""
    print(f"\n[{time.strftime('%H:%M:%S')}] BAŞLIYOR: {script_name}...")
    
    script_path = os.path.join(BASE_DIR, script_name)
    
    try:
        # Alt işlemi çalıştır
        result = subprocess.run([PYTHON_EXEC, script_path], cwd=BASE_DIR, check=True, text=True)
        print(f"[{time.strftime('%H:%M:%S')}] BAŞARILI: {script_name} tamamlandı.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{time.strftime('%H:%M:%S')}] HATA: {script_name} çalışırken hata verdi!")
        print(f"Hata kodu: {e.returncode}")
        return False

def job_create_and_upload():
    """Tüm üretim bandını sırasıyla çalıştırır."""
    print(f"\n=======================================================")
    print(f"🚀 YENİ VİDEO ÜRETİM VE YÜKLEME DÖNGÜSÜ BAŞLADI!")
    print(f"=======================================================\n")
    
    steps = [
        "1_script_generator.py",
        "2_tts_generator.py",
        "3_visual_generator.py",
        "4_video_assembler.py",
        "5_youtube_uploader.py"
    ]
    
    for step in steps:
        success = run_step(step)
        if not success:
            print("\n❌ Döngü durduruldu. Bir önceki adımda hata oluştu.")
            return # Hata varsa sonraki adımlara geçme
            
    print(f"\n=======================================================")
    print(f"✅ GÖREV TAMAMLANDI! YENİ VİDEO YOUTUBE'A YÜKLENDİ.")
    print(f"=======================================================\n")


def main():
    print("Kovanova Studios Otomatik Zamanlayıcı Başlatıldı!")
    print("Sistem arka planda bekliyor...")
    
    # -------------------------------------------------------------------
    # SAATLERİ BURADAN DEĞİŞTİREBİLİRSİNİZ
    # -------------------------------------------------------------------
    schedule.every().day.at("10:00").do(job_create_and_upload)
    schedule.every().day.at("15:00").do(job_create_and_upload)
    schedule.every().day.at("20:00").do(job_create_and_upload)
    
    print("Ayarlanan saatler: 10:00, 15:00, 20:00")
    print("Kapatmak için CTRL+C tuşlarına basabilirsiniz.\n")

    # Bekleme döngüsü
    while True:
        schedule.run_pending()
        time.sleep(60) # Her 60 saniyede bir saati kontrol et

if __name__ == "__main__":
    main()
