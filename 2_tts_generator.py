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

async def generate_speech_edge_tts(text, output_file, voice="tr-TR-AhmetNeural", rate="-12%", pitch="+0Hz"):
    """
    Microsoft Edge TTS — Doğal, sakin ve etkileyici Türkçe anlatıcı sesi.
    - rate: '-12%' ile hızlı ve robotik ton engellenir, tane tane akıcı konuşur.
    """
    import edge_tts
    
    # Metni akıcı okuma için hafifçe normalize et
    # Çoklu boşlukları temizle
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    print(f"Edge TTS (Doğal Türkçe Nöral Ses: {voice}, Hız: {rate}) kullanılarak ses üretiliyor...")
    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )
    await communicate.save(output_file)
    print(f"Seslendirme '{output_file}' dosyasına başarıyla kaydedildi!")

def generate_speech_google_tts(text, output_file):
    """
    Fallback: Google Cloud TTS
    """
    from google.cloud import texttospeech
    credentials_path = "google-credentials.json"
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

async def generate_audio_and_subtitles(text, output_file="audio.mp3", subtitles_file="subtitles.json", voice="tr-TR-AhmetNeural"):
    """
    Metni sese dönüştürür ve Whisper AI ile kelime bazlı zaman damgalarını çıkarır.
    """
    # 1. Ses Üretimi (Öncelikli Edge-TTS ücretsiz, doğal ve yavaşlatılmış tempo)
    try:
        await generate_speech_edge_tts(text, output_file, voice=voice, rate="-10%", pitch="+0Hz")
    except Exception as e:
        print(f"Edge TTS uyarısı: {e}. Google Cloud TTS deneniyor...")
        if os.path.exists("google-credentials.json"):
            generate_speech_google_tts(text, output_file)
        else:
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
        "Koç, Boğa, İkizler, Yengeç, Aslan, Başak, Terazi, Akrep, Yay, Oğlak, Kova, Balık, "
        "gizemli, büyüleyici, gökyüzünde, sahneleniyor, birleşiyor, kalbinde, gerçekleşen, "
        "devasa, saklı, gücünü, liderliğini, ortaya, çıkaracak, süzülen, ilahi, dönsün."
    )
    
    print("Zaman damgaları çıkarılıyor...")
    result = model.transcribe(output_file, word_timestamps=True, language='tr', fp16=False, initial_prompt=turkish_context)
        
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
        "tualdeki": "tuvaldeki",
        "hava": "Kova",
    }
    
    def correct_turkish(word):
        cleaned = word.strip()
        lower = cleaned.lower()
        for wrong, right in turkish_corrections.items():
            if lower == wrong.lower():
                prefix = word[:len(word) - len(word.lstrip())]
                return prefix + right
        return word
    
    subtitles = []
    for s in result.get('segments', []):
        for w in s.get('words', []):
            corrected_word = correct_turkish(w['word'])
            subtitles.append({
                "word": corrected_word,
                "start": round(w['start'], 3),
                "end": round(w['end'], 3)
            })
            
    with open(subtitles_file, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)
        
    print(f"Toplam {len(subtitles)} kelimenin zaman damgası '{subtitles_file}' dosyasına başarıyla kaydedildi!")

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
        
    # Astroloji için karizmatik derin ses AhmetNeural
    asyncio.run(generate_audio_and_subtitles(script_text, voice="tr-TR-AhmetNeural"))

if __name__ == "__main__":
    main()
