import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY bulunamadı! Lütfen .env dosyasına ekleyin.")

client = genai.Client(api_key=api_key)

def generate_zodiac_script(zodiac_sign="Koç"):
    """
    Belirtilen burç hakkında 20-30 saniyelik (50-70 kelime) bir YouTube Shorts metni 
    ve arka plan videosu (Veo 3) için görsel promptları üretir.
    """
    
    import datetime
    bugun = datetime.datetime.now().strftime("%d %B %Y")
    
    prompt = f"""
    Sen 'Kovanova Studios' adlı bir YouTube kanalı için içerik üreten profesyonel ve gerçeğe sadık bir astrologsun.
    Konseptimiz: Gerçek Astroloji ve Burçlar.
    Bugünün tarihi: {bugun}
    Bugünün burcu: {zodiac_sign}.
    
    Görevlerin:
    1. LÜTFEN SALLAMA YAPMA. Bugünün ({bugun}) GERÇEK astrolojik olaylarını, gezegen geçişlerini (transitler, retro veya ay konumu vb.) dikkate alarak bu burç için özel bir yorum yap. 
    2. Bu burç hakkında, 20-30 saniyede okunabilecek (yaklaşık 50-70 kelime) kısa, gizemli ve ilgi çekici bir metin yaz.
    3. Videonun başında güçlü bir kanca (hook) olsun. Sonunda ise kapanış cümlesi olarak SADECE şu cümleyi kullan: "Kader çarkı senin için dönsün." (Abone ol vs. deme).
    4. Seslendirme robotu okuyacağı için metinde (gülümser), [müzik girer] gibi hiçbir sahne notu OLMASIN.
    5. KESİNLİKLE UNUTMA: Okunacak video metni (script) tamamen TÜRKÇE olmalıdır. Ancak video üretimi için olan 'video_prompts' kısmı İNGİLİZCE olmalıdır.
    6. Bu videonun arka planında dönecek, burcun elementine ve bugünkü ruh haline uygun, yüksek kaliteli AI video üreticisi için TAM 5 ADET detaylı İngilizce 'video prompt' yaz. KESİNLİKLE DİKKAT ET: Bu görseller sadece manzara veya obje OLMAMALIDIR. Her görsel mutlaka o burcu temsil eden karizmatik, gizemli KADIN veya ERKEK figürleri (portre veya belden yukarı) içermelidir (Örneğin koç burcu için boynuzları olan ateşli bir savaşçı kadın, mistik kıyafetler vb). (Örnek prompt: "Cinematic 4k portrait of a beautiful mystical woman with golden ram horns, glowing fiery aura, dark fantasy aesthetic, intricate gold details")
    
    
    Çıktını SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama ekleme:
    {{
        "script": "Burada okunacak Türkçe metin olacak.",
        "video_prompts": [
            "İngilizce video prompt 1",
            "İngilizce video prompt 2"
        ]
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        if not raw_text.endswith("}"):
            raw_text += "}"
            
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"JSON parse hatası: {e}! API'den gelen yanıt:")
        print(response.text)
        return None

if __name__ == "__main__":
    import random
    zodiac_signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
    selected_sign = random.choice(zodiac_signs)
    
    print(f"Senaryo üretiliyor... (Seçilen Burç: {selected_sign})")
    result = generate_zodiac_script(selected_sign)
    
    if result:
        with open("current_script.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print("Senaryo ve promptlar 'current_script.json' dosyasına başarıyla kaydedildi!")
        print("-" * 30)
        print(f"SCRIPT:\n{result.get('script')}")
        print(f"\nPROMPTS:\n{result.get('video_prompts')}")
        print("-" * 30)
