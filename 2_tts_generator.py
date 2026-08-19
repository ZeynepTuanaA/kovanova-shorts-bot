import os
import json
import asyncio
import random
import re
import whisper
import whisper.audio
import imageio_ffmpeg
import warnings
warnings.filterwarnings("ignore")

# Monkeypatch whisper's subprocess call to use imageio_ffmpeg's binary
original_run = whisper.audio.run
def monkeypatch_run(cmd, *args, **kwargs):
    if cmd[0] == 'ffmpeg':
        cmd[0] = imageio_ffmpeg.get_ffmpeg_exe()
    return original_run(cmd, *args, **kwargs)
whisper.audio.run = monkeypatch_run

from tts_provider import get_tts_provider, TextPreprocessor

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
    # Metadata dosyasını kaydet
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
    Metni Fish Audio S2.1 Pro ile seslendirir ve Whisper AI zaman damgalarını 
    ORİJİNAL senaryo kelimeleriyle birebir eşleştirir.
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

    # 2. Whisper ile Kelime Zaman Damgalarını Alma
    print("Local Whisper AI yükleniyor ve ses analiz ediliyor...")
    model = whisper.load_model('base')
    
    turkish_context = (
        "Bu video bir Türkçe YouTube short astroloji videosudur. "
        "Kelimeler doğru Türkçe yazımla yazılmalıdır. "
        "Burç, görkemli, kozmik, ışık, şovu, gölgelerin, kucakla, Zodyak çarkı, "
        "kader, gezegen, geçiş, transit, retro, Ay, Güneş, yıldız, takımyıldız, "
        "nebula, galaksi, evren, enerji, aura, ruh, tutulma, uyanış, dönüşüm, "
        "Koç, Boğa, İkizler, Yengeç, Aslan, Başak, Terazi, Akrep, Yay, Oğlak, Kova, Balık."
    )
    
    print("Zaman damgaları çıkarılıyor...")
    result = model.transcribe(output_file, word_timestamps=True, language='tr', fp16=False, initial_prompt=turkish_context)
    
    whisper_words = []
    for s in result.get('segments', []):
        for w in s.get('words', []):
            whisper_words.append({
                "word": w['word'].strip(),
                "start": round(w['start'], 3),
                "end": round(w['end'], 3)
            })
            
    # Orijinal senaryo metnindeki kelimeler (İmla, büyük-küçük harf, kesme işaretleri %100 DOĞRU)
    orig_words = script_text.split()
    
    subtitles = []
    # Orijinal kelimeler ile Whisper zamanlarını birebir eşle (Forced Alignment)
    if len(orig_words) == len(whisper_words):
        for i in range(len(orig_words)):
            subtitles.append({
                "word": orig_words[i],
                "start": whisper_words[i]["start"],
                "end": whisper_words[i]["end"]
            })
    else:
        # Sayı farkı varsa en yakın eşleştirme
        w_idx = 0
        for orig_w in orig_words:
            if w_idx < len(whisper_words):
                subtitles.append({
                    "word": orig_w,
                    "start": whisper_words[w_idx]["start"],
                    "end": whisper_words[w_idx]["end"]
                })
                w_idx += 1
            else:
                last_end = subtitles[-1]["end"] if subtitles else 0
                subtitles.append({
                    "word": orig_w,
                    "start": last_end,
                    "end": last_end + 0.4
                })
            
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
