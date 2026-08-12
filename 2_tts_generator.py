import os
import json
import asyncio
import random
import whisper
import whisper.audio
import imageio_ffmpeg
from google.cloud import texttospeech
import warnings
warnings.filterwarnings("ignore")

# Monkeypatch whisper's subprocess call to use imageio_ffmpeg's binary
original_run = whisper.audio.run
def monkeypatch_run(cmd, *args, **kwargs):
    if cmd[0] == 'ffmpeg':
        cmd[0] = imageio_ffmpeg.get_ffmpeg_exe()
    return original_run(cmd, *args, **kwargs)
whisper.audio.run = monkeypatch_run

async def generate_audio_and_subtitles(text, output_file="audio.mp3", subtitles_file="subtitles.json"):
    """
    Verilen metni Google Cloud TTS (Wavenet) ile sese dönüştürür.
    Ardından Local Whisper AI (small model) kullanarak kelime bazlı zaman damgalarını çıkarır.
    """
    # 1. Ses Üretimi (Google Cloud TTS)
    credentials_path = "google-credentials.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    
    # Kullanıcının seçtiği Wavenet sesleri
    voices = ["tr-TR-Wavenet-C", "tr-TR-Wavenet-D"]
    selected_voice = random.choice(voices)
    print(f"Google Cloud TTS kullanılarak ses üretiliyor... (Ses: {selected_voice})")
    
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="tr-TR", name=selected_voice)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    
    print(f"Seslendirme '{output_file}' dosyasına başarıyla kaydedildi!")

    # 2. Whisper ile Kelime Zaman Damgalarını Alma
    print("Local Whisper AI (base model) yükleniyor ve ses analiz ediliyor... (Hızlı ve Kaliteli İşlem İçin)")
    
    model = whisper.load_model('base')
    
    # Türkçe astroloji terimleri ve yaygın kelimeleri içeren zengin initial_prompt
    # Bu, Whisper'ın Türkçe kelime tanıma doğruluğunu önemli ölçüde artırır
    turkish_context = (
        "Bu video bir Türkçe YouTube short astroloji videosudur. "
        "Kelimeler doğru Türkçe yazımla yazılmalıdır. "
        "Burç, görkemli, kozmik, ışık, şovu, gölgelerin, kucakla, Zodyak çarkı, "
        "kader, gezegen, geçiş, transit, retro, Ay, Güneş, yıldız, takımyıldız, "
        "nebula, galaksi, evren, enerji, aura, ruh, tutulma, uyanış, dönüşüm, "
        "Koç, Boğa, İkizler, Yengeç, Aslan, Başak, Terazi, Akrep, Yay, Oğlak, Kova, Balık, "
        "gizemli, büyüleyici, gökyüzünde, sahneleniyor, birleşiyor, kalbinde, gerçekleşen, "
        "devasa, saklı, gücünü, liderliğini, ortaya, çıkaracak, süzülen, ilahi, dönsün."
    )
    
    print("Zaman damgaları çıkarılıyor...")
    result = model.transcribe(output_file, word_timestamps=True, language='tr', fp16=False, initial_prompt=turkish_context)
        
    # Whisper'ın Türkçe'de sıkça yaptığı yanlış yazımları düzelten sözlük
    turkish_corrections = {
        "gölkemli": "görkemli",
        "görgelerin": "gölgelerin",
        "kucaklı": "kucakla",
        "çobu": "şovu",
        "cosmik": "kozmik",
        "kosmik": "kozmik",
        "zodiac": "Zodyak",
        "Zodiac": "Zodyak",
        "zodiak": "Zodyak",
        "astroloji": "astroloji",
        "gezeğen": "gezegen",
        "tutulması": "tutulması",
        "kendini": "kendin",
        "takım yıldız": "takımyıldız",
        "gökyüzunde": "gökyüzünde",
        "sahneleniyo": "sahneleniyor",
        "birleşiyo": "birleşiyor",
    }
    
    def correct_turkish(word):
        """Whisper'ın Türkçe hatalarını düzeltir."""
        cleaned = word.strip()
        lower = cleaned.lower()
        for wrong, right in turkish_corrections.items():
            if lower == wrong.lower():
                # Orijinal kelimeden boşluk prefix'ini koru
                prefix = word[:len(word) - len(word.lstrip())]
                return prefix + right
        return word
    
    subtitles = []
    for s in result.get('segments', []):
        for w in s.get('words', []):
            corrected_word = correct_turkish(w['word'])
            subtitles.append({
                "word": corrected_word,
                "start": w['start'],
                "end": w['end']
            })
            
    with open(subtitles_file, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)
        
    print(f"Toplam {len(subtitles)} kelimenin zaman damgası '{subtitles_file}' dosyasına başarıyla kaydedildi!")
    print("(Türkçe düzeltme katmanı uygulandı)")

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
        
    asyncio.run(generate_audio_and_subtitles(script_text))

if __name__ == "__main__":
    main()
