import os
import json
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

def create_single_word_image(word, width=1080, height=1920, font_path='Roboto-Bold.ttf'):
    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try different sizes based on word length
    if len(word) > 10:
        font_size = 90
    elif len(word) > 6:
        font_size = 110
    else:
        font_size = 140
        
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
        
    # Get text size to center it
    text = word.upper()
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    # Position: X Center, Y center but slightly lower (Y=1000)
    x = (width - text_width) / 2
    y = 900
    
    # Stroke for good visibility over any background
    stroke_width = 8
    stroke_color = 'black'
    
    # Choose text color (yellow or white mostly, maybe green)
    fill_color = random.choice(["#FFFFFF", "#FFFFFF", "#FFEA00", "#FFEA00", "#00FF00"])
    
    # Draw text with stroke
    for dx in range(-stroke_width, stroke_width+1):
        for dy in range(-stroke_width, stroke_width+1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x+dx, y+dy), text, font=font, fill=stroke_color)
                
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color)
    
    return np.array(img)

def create_video():
    print("Video Montajlayıcı (MoviePy v2 + Dinamik Altyazı) başlatılıyor...")
    
    audio_path = "audio.mp3"
    images_dir = "images"
    subtitles_path = "subtitles.json"
    output_path = "final_short.mp4"
    
    if not os.path.exists(audio_path):
        print("Hata: audio.mp3 bulunamadı. Lütfen önce 2_tts_generator.py'yi çalıştırın.")
        return
        
    if not os.path.exists(images_dir) or not os.listdir(images_dir):
        print("Hata: images klasörü boş. Lütfen önce 3_visual_generator.py'yi çalıştırın.")
        return
        
    # Ses dosyasını yükle
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    
    # Görselleri bul
    # Hem JPG hem PNG görselleri tara (Gemini PNG çıktı verir)
    image_files = sorted(
        glob.glob(os.path.join(images_dir, "*.jpg")) + 
        glob.glob(os.path.join(images_dir, "*.png"))
    )
    
    if not image_files:
        print("Hata: Yeterli görsel (JPG/PNG) bulunamadı.")
        return
        
    # Her görselin ekranda kalma süresini hesapla
    duration_per_image = total_duration / len(image_files)
    
    clips = []
    for img_path in image_files:
        clip = ImageClip(img_path).with_duration(duration_per_image).resized(width=1080, height=1920).with_fps(24)
        clips.append(clip)
        
    # Görselleri arka arkaya birleştir
    video = concatenate_videoclips(clips, method="chain")
    video = video.with_audio(audio)
    
    # Dinamik Altyazı Ekleme
    txt_clips = []
    if os.path.exists(subtitles_path):
        with open(subtitles_path, "r", encoding="utf-8") as f:
            subtitles = json.load(f)
            
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Bold.ttf')
        
        for sub in subtitles:
            word = sub['word']
            start = sub['start']
            end = sub['end']
            
            # Punctuation'ları temizle (Türkçe karakterleri destekleyerek)
            valid_chars = set("abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ0123456789")
            word_clean = ''.join(c for c in word if c in valid_chars)
            if not word_clean:
                continue
                
            try:
                text_array = create_single_word_image(word, width=1080, height=1920, font_path=font_path)
                duration = end - start
                if duration <= 0:
                    continue
                # Create clip for this exact word duration
                txt_clip = ImageClip(text_array).with_position(('center', 'center')).with_start(start).with_duration(duration)
                txt_clips.append(txt_clip)
            except Exception as e:
                print(f"Altyazı ({word}) üretilirken hata oluştu: {e}")
                
    if txt_clips:
        print(f"Toplam {len(txt_clips)} adet dinamik kelime altyazısı eklendi.")
        video = CompositeVideoClip([video] + txt_clips)
    else:
        print("Uyarı: Dinamik altyazı bulunamadı veya oluşturulamadı, düz video render ediliyor.")

    print(f"Video {output_path} adıyla dışa aktarılıyor... Lütfen bekleyin.")
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    
    print("Video montajı başarıyla tamamlandı!")

if __name__ == "__main__":
    create_video()
