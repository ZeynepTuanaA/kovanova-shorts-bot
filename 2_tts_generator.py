import os
import json
from google.cloud import texttospeech

def generate_audio(text, output_file="audio.mp3"):
    """
    Verilen metni Google Cloud TTS ile sese dönüştürür.
    """
    credentials_path = "google-credentials.json"
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Hata: {credentials_path} dosyası bulunamadı!")
        
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    print("Google Cloud TTS bağlantısı kuruluyor...")
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    import random
    selected_voice = random.choice(["tr-TR-Wavenet-C", "tr-TR-Wavenet-D"])
    
    # Ses parametreleri (Dönüşümlü olarak C ve D kadın sesleri)
    voice = texttospeech.VoiceSelectionParams(
        language_code="tr-TR",
        name=selected_voice,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    print("Ses üretiliyor...")
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f"Seslendirme başarıyla '{output_file}' dosyasına kaydedildi!")

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
        
    generate_audio(script_text, output_file="audio.mp3")

if __name__ == "__main__":
    main()
