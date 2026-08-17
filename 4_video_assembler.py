import os
import json
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

def tr_upper(text):
    """Türkçe karakterleri (i->İ, ı->I vb.) doğru şekilde BÜYÜK HARFE çevirir."""
    mapping = {
        'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ğ': 'Ğ', 'ö': 'Ö', 'ş': 'Ş', 'ü': 'Ü'
    }
    chars = []
    for c in text:
        chars.append(mapping.get(c, c.upper()))
    return ''.join(chars)

def create_phrase_image(words_list, active_index, width=1080, height=1920, font_path='Roboto-Bold.ttf'):
    """
    2-4 kelimelik şık bir grup altyazı oluşturur.
    Aktif kelime parlak Altın Sarısı (#FFD700), diğer kelimeler Beyaz (#FFFFFF).
    Arka planda yarı saydam şık koyu kapsül ve kalın kontur bulunur.
    """
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_size = 72
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
        
    # Kelimeleri formatla
    formatted_words = [tr_upper(w.strip()) for w in words_list]
    
    # Her kelimenin genişliğini hesapla
    word_boxes = []
    space_w = draw.textbbox((0, 0), " ", font=font)[2]
    
    total_text_width = 0
    for w in formatted_words:
        bbox = draw.textbbox((0, 0), w, font=font)
        w_width = bbox[2] - bbox[0]
        w_height = bbox[3] - bbox[1]
        word_boxes.append((w, w_width, w_height))
        total_text_width += w_width + space_w
    total_text_width -= space_w
    
    # Y konumu: Shorts güvenli alt bölgesi (Y = 1350)
    target_y = 1350
    start_x = (width - total_text_width) / 2
    
    # Kapsül / Arka plan kutusu
    padding_x = 35
    padding_y = 20
    box_left = start_x - padding_x
    box_top = target_y - padding_y
    box_right = start_x + total_text_width + padding_x
    box_bottom = target_y + word_boxes[0][2] + padding_y + 15
    
    # Yarı saydam şık koyu arka plan
    draw.rounded_rectangle(
        [box_left, box_top, box_right, box_bottom],
        radius=25,
        fill=(10, 10, 15, 200),
        outline=(255, 215, 0, 120),
        width=3
    )
    
    # Kelimeleri çiz
    curr_x = start_x
    stroke_width = 5
    
    for idx, (word_text, w_w, w_h) in enumerate(word_boxes):
        is_active = (idx == active_index)
        
        # Renk: Aktif kelime parlak sarı, diğerleri saf beyaz
        text_color = "#FFE600" if is_active else "#FFFFFF"
        stroke_color = "#000000"
        
        # Kontur
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((curr_x + dx, target_y + dy), word_text, font=font, fill=stroke_color)
                    
        # Ana metin
        draw.text((curr_x, target_y), word_text, font=font, fill=text_color)
        
        curr_x += w_w + space_w
        
    return np.array(img)

def group_subtitles_into_phrases(subtitles, max_words_per_phrase=3):
    """
    Whisper altyazı kelimelerini 2-3 kelimelik mantıklı ve ritmik öbeklere böler.
    """
    phrases = []
    current_phrase = []
    
    for sub in subtitles:
        word = sub.get('word', '').strip()
        if not word:
            continue
        current_phrase.append(sub)
        
        # Cümle sonu işareti varsa veya maksimum kelime sayısına ulaştıysa yeni öbek başlat
        is_sentence_end = word.endswith(('.', '!', '?', ';', ':'))
        if len(current_phrase) >= max_words_per_phrase or is_sentence_end:
            phrases.append(current_phrase)
            current_phrase = []
            
    if current_phrase:
        phrases.append(current_phrase)
        
    return phrases

def create_video():
    print("Profesyonel Video Montajlayıcı (Karaoke Dinamik Altyazı + HD Görseller) başlatılıyor...")
    
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
    print(f"Toplam ses süresi: {total_duration:.2f} saniye")
    
    # Görselleri bul
    image_files = sorted(
        glob.glob(os.path.join(images_dir, "*.jpg")) + 
        glob.glob(os.path.join(images_dir, "*.png"))
    )
    
    if not image_files:
        print("Hata: Yeterli görsel (JPG/PNG) bulunamadı.")
        return
        
    # Her görselin ekranda kalma süresini hesapla
    duration_per_image = total_duration / len(image_files)
    print(f"{len(image_files)} görsel kullanılıyor (Görsel başına {duration_per_image:.2f} saniye)")
    
    clips = []
    for img_path in image_files:
        clip = ImageClip(img_path).with_duration(duration_per_image).resized(width=1080, height=1920).with_fps(24)
        clips.append(clip)
        
    # Görselleri arka arkaya birleştir
    video = concatenate_videoclips(clips, method="chain")
    video = video.with_audio(audio)
    
    # Dinamik Karaoke Altyazı Ekleme
    txt_clips = []
    if os.path.exists(subtitles_path):
        with open(subtitles_path, "r", encoding="utf-8") as f:
            subtitles = json.load(f)
            
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Bold.ttf')
        
        phrases = group_subtitles_into_phrases(subtitles, max_words_per_phrase=3)
        print(f"Altyazılar {len(phrases)} adet akıcı öbeğe ayrıldı.")
        
        for phrase in phrases:
            words_in_phrase = [item['word'] for item in phrase]
            
            for active_idx, item in enumerate(phrase):
                w_start = item['start']
                w_end = item['end']
                duration = w_end - w_start
                if duration <= 0:
                    continue
                    
                try:
                    img_array = create_phrase_image(
                        words_list=words_in_phrase,
                        active_index=active_idx,
                        width=1080,
                        height=1920,
                        font_path=font_path
                    )
                    txt_clip = ImageClip(img_array).with_position(('center', 'top')).with_start(w_start).with_duration(duration)
                    txt_clips.append(txt_clip)
                except Exception as e:
                    print(f"Altyazı karesi üretilirken hata: {e}")
                    
    if txt_clips:
        print(f"Toplam {len(txt_clips)} adet karaoke altyazı karesi videoya eklendi.")
        video = CompositeVideoClip([video] + txt_clips)
    else:
        print("Uyarı: Altyazı oluşturulamadı, düz video render ediliyor.")

    print(f"Video {output_path} adıyla yüksek kalitede render ediliyor...")
    video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        bitrate="6000k",
        threads=4
    )
    
    print("\n[OK] Video montaji basariyla tamamlandi!")

if __name__ == "__main__":
    create_video()
