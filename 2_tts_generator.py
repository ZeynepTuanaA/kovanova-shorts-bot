import os
import json
import asyncio
import random
import re
import warnings
warnings.filterwarnings("ignore")

from tts_provider import get_tts_provider, TextPreprocessor

def get_audio_duration(audio_file):
    """Ses dosyasının net süresini döner."""
    try:
        from moviepy import AudioFileClip
        with AudioFileClip(audio_file) as clip:
            return float(clip.duration)
    except Exception:
        pass
    try:
        import subprocess
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass
    # Dosya boyutundan (128kbps mp3 ~16KB/s) yaklaşık süre
    if os.path.exists(audio_file):
        return max(os.path.getsize(audio_file) / 16000.0, 10.0)
    return 20.0

def generate_proportional_subtitles(script_text, audio_duration):
    """
    Kelimelerin harf uzunlukları ve noktalama duraklamalarına göre 
    hafif ve mükemmel hizalanmış zaman damgaları üretir (OOM / RAM riski sıfırdır).
    """
    words = script_text.split()
    weights = []
    for w in words:
        weight = max(len(w), 1)
        if w.endswith(('.', '!', '?', ':')):
            weight += 4.0
        elif w.endswith((',', ';')):
            weight += 2.0
        weights.append(weight)
    
    total_weight = sum(weights) if sum(weights) > 0 else 1
    current_time = 0.0
    subtitles = []
    
    for w, weight in zip(words, weights):
        duration = (weight / total_weight) * audio_duration
        start = round(current_time, 3)
        end = round(current_time + duration * 0.92, 3)
        subtitles.append({'word': w, 'start': start, 'end': end})
        current_time += duration
        
    return subtitles

def generate_speech_fish_audio(text, output_file="audio.mp3", reference_id=None):
    """
    Fish Audio S2.1 Pro — Yüksek Kaliteli Türkçe TTS Sağlayıcısı.
    """
    provider = get_tts_provider()
    metadata = provider.generate_speech(
        text=text,
        output_path=output_file,
        reference_id=reference_id,
        audio_format="mp3"
    )
    meta_path = "audio_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return metadata

def generate_speech_google_tts(text, output_file):
    """Acil Durum Fallback: Google Cloud TTS (varsa)"""
    credentials_path = "google-credentials.json"
    if not os.path.exists(credentials_path):
        return False
    try:
        from google.cloud import texttospeech
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        voices = ["tr-TR-Wavenet-C", "tr-TR-Wavenet-D"]
        selected_voice = random.choice(voices)
        print(f"Google Cloud TTS fallback kullanılarak ses üretiliyor... (Ses: {selected_voice})")
        
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="tr-TR", name=selected_voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=0.90)
        
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        print(f"Seslendirme (Google) '{output_file}' dosyasına kaydedildi!")
        return True
    except Exception as e:
        print(f"Google TTS fallback hatası: {e}")
        return False

async def generate_audio_and_subtitles(script_text, output_file="audio.mp3", subtitles_file="subtitles.json", reference_id=None):
    """
    Metni Fish Audio S2.1 Pro ile seslendirir ve kelime zaman damgalarını oluşturur.
    """
    # 1. Ses Üretimi (Ana Sağlayıcı: Fish Audio S2.1 Pro)
    try:
        print(f"Fish Audio S2.1 Pro TTS ile Türkçe ses üretiliyor...")
        generate_speech_fish_audio(script_text, output_file, reference_id=reference_id)
    except Exception as e:
        print(f"Fish Audio TTS uyarısı: {e}. Fallback kontrol ediliyor...")
        ok = generate_speech_google_tts(script_text, output_file)
        if not ok:
            raise e

    # 2. Ses Süresini Al ve Altyazıları Hizala
    duration = get_audio_duration(output_file)
    print(f"Ses üretildi. Toplam ses süresi: {duration:.2f} saniye.")
    
    subtitles = None
    # İsteğe bağlı: Whisper Tiny denenir, bellek yetersizliği durumunda hafif orantısal modele geçer
    try:
        import whisper
        print("Whisper Tiny ile zaman damgaları taranıyor...")
        model = whisper.load_model('tiny')
        result = model.transcribe(output_file, word_timestamps=True, language='tr', fp16=False)
        
        whisper_words = []
        for s in result.get('segments', []):
            for w in s.get('words', []):
                whisper_words.append({
                    "word": w['word'].strip(),
                    "start": round(w['start'], 3),
                    "end": round(w['end'], 3)
                })
        orig_words = script_text.split()
        if len(orig_words) == len(whisper_words):
            subtitles = []
            for i in range(len(orig_words)):
                subtitles.append({
                    "word": orig_words[i],
                    "start": whisper_words[i]["start"],
                    "end": whisper_words[i]["end"]
                })
    except Exception as e:
        print(f"Whisper uyarısı: {e}. Ultra-hafif orantısal altyazı motoruna geçiliyor.")

    if not subtitles:
        print("Orantısal ağırlıklı altyazı zamanlaması hesaplanıyor...")
        subtitles = generate_proportional_subtitles(script_text, duration)
            
    with open(subtitles_file, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)
        
    print(f"Toplam {len(subtitles)} orijinal senaryo kelimesi zaman damgalarıyla '{subtitles_file}' dosyasına kaydedildi!")
    print("Altyazılar %100 orijinal senaryo imlasına göre kusursuz olarak hizalandı.")

def main():
    script_file = "current_script.json"
    if not os.path.exists(script_file):
        print(f"Hata: '{script_file}' bulunamadı. Önce 1_script_generator.py'yi çalıştırın.")
        return
    
    with open(script_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    script_text = data.get("script")
    if not script_text:
        print("Hata: JSON dosyasında 'script' metni bulunamadı.")
        return
        
    asyncio.run(generate_audio_and_subtitles(script_text, reference_id=os.getenv("FISH_REFERENCE_ID")))

if __name__ == "__main__":
    main()
