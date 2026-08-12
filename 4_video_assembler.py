import os
import json
import glob
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip

def create_video():
    print("Video Montajlayıcı (MoviePy) başlatılıyor...")
    
    audio_path = "audio.mp3"
    images_dir = "images"
    script_path = "current_script.json"
    output_path = "final_short.mp4"
    
    if not os.path.exists(audio_path):
        print("Hata: audio.mp3 bulunamadı. Lütfen önce 2_tts_generator.py'yi çalıştırın.")
        return
        
    if not os.path.exists(images_dir) or not os.listdir(images_dir):
        print("Hata: images klasörü boş. Lütfen önce 3_visual_generator.py'yi çalıştırın.")
        return
        
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
            text_content = script_data.get("script", "")
    except Exception as e:
        print(f"Uyarı: current_script.json okunamadı ({e}). Altyazı eklenmeyecek.")
        text_content = ""

    # Ses dosyasını yükle
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    
    # Görselleri bul
    image_files = sorted(glob.glob(os.path.join(images_dir, "*.jpg")))
    
    if not image_files:
        print("Hata: Yeterli JPG görseli bulunamadı.")
        return
        
    # Her görselin ekranda kalma süresini hesapla
    duration_per_image = total_duration / len(image_files)
    
    clips = []
    for img_path in image_files:
        # Resize/Crop işlemi yapılarak 1080x1920 boyutuna tam oturtulur
        clip = ImageClip(img_path).with_duration(duration_per_image).resized(width=1080, height=1920).with_fps(24)
        clips.append(clip)
        
    # Görselleri arka arkaya birleştir
    video = concatenate_videoclips(clips, method="chain")
    
    # Sesi videoya ekle
    video = video.with_audio(audio)
    
    # Basit Altyazı Ekleme (Opsiyonel)
    if text_content:
        # Metni 4-5 kelimelik parçalara bölüyoruz
        words = text_content.split()
        chunk_size = 4
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        duration_per_chunk = total_duration / len(chunks)
        
        txt_clips = []
        for i, chunk in enumerate(chunks):
            start_time = i * duration_per_chunk
            # TextClip için ImageMagick kurulu olmalıdır!
            try:
                font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Bold.ttf')
                txt_clip = TextClip(text=chunk, font_size=70, color='white', font=font_path,
                                    stroke_color='black', stroke_width=3, size=(900, None), method='caption')
                txt_clip = txt_clip.with_position(('center', 'bottom')).with_start(start_time).with_duration(duration_per_chunk)
                
                # Hafif yukarı kaydırmak için margin
                txt_clip = txt_clip.margin(bottom=200, opacity=0)
                txt_clips.append(txt_clip)
            except Exception as e:
                print(f"Altyazı üretilirken hata oluştu (ImageMagick eksik olabilir): {e}")
                txt_clips = []
                break
                
        if txt_clips:
            video = CompositeVideoClip([video] + txt_clips)

    print(f"Video {output_path} adıyla dışa aktarılıyor... Lütfen bekleyin.")
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    
    print("Video montajı başarıyla tamamlandı!")

if __name__ == "__main__":
    create_video()
