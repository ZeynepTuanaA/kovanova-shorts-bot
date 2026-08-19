import os
import sys
import time
import base64
import subprocess
from datetime import datetime, timezone, timedelta

# Türkiye Saati (UTC+3) Sabit Zaman Dilimi
TR_TZ = timezone(timedelta(hours=3))

# Sistemin kurulduğu dizin (Kovanova_Shorts klasörü)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
                target_path = os.path.join(BASE_DIR, filename)
                with open(target_path, "wb") as f:
                    f.write(base64.b64decode(b64_content))
                print(f"[+] {filename} oluşturuldu.")
            except Exception as e:
                print(f"[-] {filename} oluşturulamadı: {e}")

# İlk başta secret'ları başlat
initialize_secrets()

PYTHON_EXEC = sys.executable
print(f"[+] Kullanılan Python Yolu: {PYTHON_EXEC}")

def run_step(script_name):
    """Belirtilen Python betiğini çalıştırır ve sonucunu döner."""
    now_str = datetime.now(TR_TZ).strftime('%H:%M:%S')
    print(f"\n[{now_str}] BAŞLIYOR: {script_name}...")
    
    script_path = os.path.join(BASE_DIR, script_name)
    
    try:
        # Alt işlemi çalıştır
        result = subprocess.run([PYTHON_EXEC, script_path], cwd=BASE_DIR, check=True, text=True)
        print(f"[{datetime.now(TR_TZ).strftime('%H:%M:%S')}] BAŞARILI: {script_name} tamamlandı.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now(TR_TZ).strftime('%H:%M:%S')}] HATA: {script_name} çalışırken hata verdi (Kod: {e.returncode})")
        return False
    except Exception as e:
        print(f"[{datetime.now(TR_TZ).strftime('%H:%M:%S')}] BEKLENMEYEN HATA: {script_name} - {e}")
        return False

def job_create_and_upload():
    """Tüm üretim bandını sırasıyla çalıştırır."""
    now_str = datetime.now(TR_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=======================================================")
    print(f"🚀 YENİ VİDEO ÜRETİM VE YÜKLEME DÖNGÜSÜ BAŞLADI! [TSİ: {now_str}]")
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
    print(f"✅ GÖREV TAMAMLANDI! YENİ VİDEO YOUTUBE'A YÜKLENDİ. [TSİ: {datetime.now(TR_TZ).strftime('%Y-%m-%d %H:%M:%S')}]")
    print(f"=======================================================\n")

def main():
    # -------------------------------------------------------------------
    # SAATLER (Türkiye Saati / UTC+3): 10:00, 15:00, 20:00 + Test Saatleri
    # -------------------------------------------------------------------
    TARGET_TIMES = ["10:00", "15:00", "20:00", "20:41", "20:43", "20:45"]
    
    print("=" * 60)
    print("🌟 Kovanova Studios Otomatik Zamanlayıcı Başlatıldı!")
    print(f"⏰ Ayarlanan Görev Saatleri (Türkiye Saati): {', '.join(TARGET_TIMES)}")
    print(f"🕒 Başlangıç Türkiye Zamanı: {datetime.now(TR_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    last_executed_minute = None
    
    while True:
        now = datetime.now(TR_TZ)
        current_time_str = now.strftime("%H:%M")
        
        if current_time_str in TARGET_TIMES and current_time_str != last_executed_minute:
            last_executed_minute = current_time_str
            print(f"\n⏰ [TETİKLENDİ] Hedef saat {current_time_str} geldi, video üretim süreci başlatılıyor...")
            job_create_and_upload()
            
        time.sleep(5)

if __name__ == "__main__":
    main()
