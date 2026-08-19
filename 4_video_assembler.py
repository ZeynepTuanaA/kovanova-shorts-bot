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

def create_compact_phrase_image(words_list, active_index, font_path='Roboto-Bold.ttf'):
    """
    Sadece altyazı kutusunun kapladığı küçük alanı (ör. 700x120 px) çizer.
    Bellek kullanımını 30 kat düşürerek sunucunun OOM (RAM aşımı) olmasını engeller.
    """
    font_size = 64
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
        
    formatted_words = [tr_upper(w.strip()) for w in words_list]
    
    # Boyut ölçümü
    temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    space_w = temp_draw.textbbox((0, 0), " ", font=font)[2]
    
    word_boxes = []
    total_w = 0
    max_h = 0
    for w in formatted_words:
        bbox = temp_draw.textbbox((0, 0), w, font=font)
        w_w = bbox[2] - bbox[0]
        w_h = bbox[3] - bbox[1]
        word_boxes.append((w, w_w, w_h))
        total_w += w_w + space_w
        if w_h > max_h:
            max_h = w_h
    total_w -= space_w
    
    pad_x = 32
    pad_y = 18
    badge_w = total_w + pad_x * 2
    badge_h = max_h + pad_y * 2 + 10
    
    img = Image.new('RGBA', (badge_w, badge_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Yarı saydam şık koyu kapsül
    draw.rounded_rectangle(
        [0, 0, badge_w, badge_h],
        radius=20,
        fill=(10, 10, 15, 210),
        outline=(255, 215, 0, 140),
        width=3
    )
    
    curr_x = pad_x
    curr_y = pad_y
    stroke_width = 4
    
    for idx, (word_text, w_w, w_h) in enumerate(word_boxes):
        is_active = (idx == active_index)
        text_color = "#FFE600" if is_active else "#FFFFFF"
        stroke_color = "#000000"
        
        # Kontur
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((curr_x + dx, curr_y + dy), word_text, font=font, fill=stroke_color)
                    
        # Ana metin
        draw.text((curr_x, curr_y), word_text, font=font, fill=text_color)
        curr_x += w_w + space_w
        
    return np.array(img)

def group_subtitles_into_phrases(subtitles, max_words_per_phrase=3):
    """
    Altyazı kelimelerini 2-3 kelimelik akıcı öbeklere böler.
    """
    phrases = []
    current_phrase = []
    
    for sub in subtitles:
        word = sub.get('word', '').strip()
        if not word:
            continue
        current_phrase.append(sub)
        
        is_sentence_end = word.endswith(('.', '!', '?', ';', ':'))
        if len(current_phrase) >= max_words_per_phrase or is_sentence_end:
            phrases.append(current_phrase)
            current_phrase = []
            
    if current_phrase:
        phrases.append(current_phrase)
        
    return phrases

def create_video():
    print("Profesyonel Video Montajlayıcı (Düşük Bellek Modu + HD Render) başlatılıyor...")
    
    audio_path = "audio.mp3"
    images_dir = "images"
    subtitles_path = "subtitles.json"
    output_path = "final_short.mp4"
    
    if not os.path.exists(audio_path):
        print("Hata: audio.mp3 bulunamadı.")
        return
        
    if not os.path.exists(images_dir) or not os.listdir(images_dir):
        print("Hata: images klasörü boş.")
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
        
    duration_per_image = total_duration / len(image_files)
    print(f"{len(image_files)} görsel kullanılıyor (Görsel başına {duration_per_image:.2f} saniye)")
    
    clips = []
    for img_path in image_files:
        clip = ImageClip(img_path).with_duration(duration_per_image).resized(width=1080, height=1920).with_fps(24)
        clips.append(clip)
        
    # Görselleri arka arkaya birleştir
    video = concatenate_videoclips(clips, method="chain")
    video = video.with_audio(audio)
    
    # Dinamik Karaoke Altyazı Ekleme (Kompakt Badge Modu)
    txt_clips = []
    if os.path.exists(subtitles_path):
        with open(subtitles_path, "r", encoding="utf-8") as f:
            subtitles = json.load(f)
            
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Bold.ttf')
        phrases = group_subtitles_into_phrases(subtitles, max_words_per_phrase=3)
        print(f"Altyazılar {len(phrases)} adet akıcı öbeğe ayrıldı.")
        
        # Shorts güvenli bölge konumu (Y = 1350)
        for phrase in phrases:
            words_in_phrase = [item['word'] for item in phrase]
            
            for active_idx, item in enumerate(phrase):
                w_start = item['start']
                w_end = item['end']
                duration = w_end - w_start
                if duration <= 0:
                    continue
                    
                try:
                    img_array = create_compact_phrase_image(
                        words_list=words_in_phrase,
                        active_index=active_idx,
                        font_path=font_path
                    )
                    txt_clip = (
                        ImageClip(img_array)
                        .with_position(('center', 1350))
                        .with_start(w_start)
                        .with_duration(duration)
                    )
                    txt_clips.append(txt_clip)
                except Exception as e:
                    print(f"Altyazı karesi üretilirken hata: {e}")
                    
    if txt_clips:
        print(f"Toplam {len(txt_clips)} adet kompakt altyazı karesi videoya eklendi.")
        video = CompositeVideoClip([video] + txt_clips)
    else:
        print("Uyarı: Altyazı oluşturulamadı, düz video render ediliyor.")

    print(f"Video {output_path} adıyla render ediliyor...")
    video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        bitrate="4500k",
        threads=2
    )
    
    print("\n[OK] Video montajı başarıyla tamamlandı!")

if __name__ == "__main__":
    create_video()
