import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY bulunamadı!")

client = genai.Client(api_key=api_key)

def generate_zodiac_script(zodiac_sign="Kova"):
    """
    Belirtilen burç hakkında 20-30 saniyelik (50-70 kelime) bir YouTube Shorts metni 
    ve arka plan videosu için 7 adet ASİL, KUSURSUZ YÜZLÜ, ŞIK VE KAPALI KIYAFETLİ astrolojik görsel promptu üretir.
    """
    import datetime
    import random
    bugun = datetime.datetime.now().strftime("%d %B %Y")
    
    prompt = f"""
    Sen 'Kovanova Studios' YouTube kanalı için içerik üreten saygın ve vizyoner bir astrologsun.
    Konsept: Gerçek Astroloji, Zodyak ve Kozmik Enerjiler.
    Tarih: {bugun}
    Burç: {zodiac_sign}.
    
    GÖREVLER:
    1. {zodiac_sign} burcu için bugünün astrolojik enerjilerini anlatan 50-70 kelimelik gizemli, akıcı ve motive edici bir Türkçe metin yaz.
    2. Metin KESİNLİKLE '{zodiac_sign} burcu, ...' veya '{zodiac_sign}, ...' ile başlamalıdır.
    3. Kapanış cümlesi SADECE şu olmalıdır: "Kader çarkı senin için dönsün."
    4. Metinde sahne notu ([müzik] vb.) olmasın.
    5. Metnin ana konusunu ve temalarını analiz et (Örneğin: Aşk, Para/Kariyer, Enerji/Dönüşüm, Spiritüel Şans).
    6. Video görselleri için Pexels API'de dikey arama yapmaya uygun TAM 7 ADET dinamik İngilizce arama sorgusu ('pexels_queries') oluştur.
       - Aşk teması için: "romantic celestial astrology", "pink galaxy stars", "love astrology aesthetic"
       - Para / Başarı için: "luxury celestial gold", "golden stars universe", "wealth aesthetic cosmic"
       - Enerji / Dönüşüm için: "cosmic transformation eclipse", "mystical aura light", "spiritual energy galaxy"
       - Burç teması için: "{zodiac_sign.lower()} zodiac celestial", "cosmic night stars aesthetic", "celestial mystery"
    7. AI görsel üretimi için 7 adet İngilizce 'video_prompts' oluştur:
       - Estetik: Dark fantasy, mystical, cinematic fantasy concept art, digital painting, highly detailed, dramatic lighting.
       - Karakter odaklı: {zodiac_sign} burcunun sembolik öğelerini üzerinde taşıyan asil, tamamen giyinik, büyüleyici fantezi karakteri (kadın/tanrıça/savaşçı).
       - NSFW/Açıklık/Müstehcenlik KESİNLİKLE YOKTUR.
       - Renkler: Derin lacivert, mor, altın, zümrüt veya burcun mistik tonları.
       - Dikey kompozisyon (vertical 9:16 portrait).
    
    Çıktını SADECE JSON formatında ver:
    {{
        "zodiac_sign": "{zodiac_sign}",
        "theme": "Aşk / Para / Enerji / Dönüşüm",
        "script": "Türkçe metin",
        "pexels_queries": [
            "İngilizce pexels arama sorgusu 1",
            "İngilizce pexels arama sorgusu 2",
            "İngilizce pexels arama sorgusu 3",
            "İngilizce pexels arama sorgusu 4",
            "İngilizce pexels arama sorgusu 5",
            "İngilizce pexels arama sorgusu 6",
            "İngilizce pexels arama sorgusu 7"
        ],
        "video_prompts": [
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 1, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 2, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 3, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 4, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 5, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 6, 9:16 vertical",
            "Dark fantasy {zodiac_sign} zodiac character, detailed prompt 7, 9:16 vertical"
        ]
    }}
    """
    
    import time
    candidate_models = ['gemini-3.5-flash', 'gemini-3.6-flash']
    response = None
    last_err = None
    
    for model_name in candidate_models:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                last_err = e
                print(f"Model '{model_name}' deneme {attempt} başarısız: {e}")
                time.sleep(2 * attempt)
        if response and response.text:
            break
            
    if not response or not response.text:
        print(f"Uyarı: Gemini modelleri geçici olarak meşgul ({last_err}). Şablon senaryo devreye sokuluyor...")
        return {
            "zodiac_sign": zodiac_sign,
            "theme": "Kozmik Dönüşüm ve Enerji",
            "script": f"{zodiac_sign} burcu, bugün kozmik enerjiler ruhunu sarıyor. Yıldızlar sezgilerinin sana rehberlik edeceğini müjdeliyor. İçindeki saklı gücü keşfetmek için harika bir gün. İnancını koru, yola devam et. Kader çarkı senin için dönsün.",
            "pexels_queries": [
                f"{zodiac_sign.lower()} zodiac celestial aesthetic",
                f"{zodiac_sign.lower()} galaxy stars cosmic",
                "celestial space nebulae gold glow",
                "mystical universe spiritual stars",
                "cosmic wheel destiny tarot",
                "glowing galaxy magic universe",
                "celestial zodiac royalty"
            ],
            "video_prompts": [
                f"Dark fantasy {zodiac_sign} zodiac spirit, detailed cinematic 8k, 9:16 vertical",
                f"Mystical {zodiac_sign} goddess standing in cosmos, ethereal lighting, 9:16 vertical",
                f"Celestial priestess channeling {zodiac_sign} energy, intricate stars, 9:16 vertical",
                f"Majestic royal figure embodying {zodiac_sign} constellation, 9:16 vertical",
                f"Cosmic warrior with glowing {zodiac_sign} aura in deep space, 9:16 vertical",
                f"Ethereal queen of destiny, golden galaxy background, 9:16 vertical",
                f"Sacred cosmic shrine of {zodiac_sign}, starry night sky, 9:16 vertical"
            ]
        }
    
    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(raw_text[start:end+1])
        except Exception:
            pass
            
    try:
        return json.loads(raw_text)
    except Exception as e:
        print(f"JSON regex fallback...")
        script_m = re.search(r'"script"\s*:\s*"([^"]+)"', raw_text)
        script = script_m.group(1) if script_m else ""
        prompts = re.findall(r'"([^"]{30,})"', raw_text)
        valid_prompts = [p for p in prompts if p != script and "video_prompts" not in p]
        default_queries = [
            f"{zodiac_sign.lower()} celestial astrology aesthetic",
            f"{zodiac_sign.lower()} zodiac cosmic night",
            "romantic celestial pink galaxy",
            "luxury celestial gold universe",
            "cosmic transformation eclipse mystical",
            "galaxy stars universe spiritual",
            "celestial astrology mystery night"
        ]
        if script and valid_prompts:
            return {"zodiac_sign": zodiac_sign, "theme": "Kozmik Astroloji", "script": script, "pexels_queries": default_queries, "video_prompts": valid_prompts[:7]}
        elif script:
            return {"zodiac_sign": zodiac_sign, "theme": "Kozmik Astroloji", "script": script, "pexels_queries": default_queries, "video_prompts": []}
        return None

if __name__ == "__main__":
    import datetime
    zodiac_signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
    day_index = datetime.datetime.now().toordinal() % 12
    selected_sign = zodiac_signs[day_index]
    
    print(f"Senaryo ve Asil Karakter Promptları Üretiliyor... (Burç: {selected_sign})")
    result = generate_zodiac_script(selected_sign)
    
    if result:
        with open("current_script.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print("Senaryo ve promptlar 'current_script.json' dosyasına kaydedildi!")
        print(f"SCRIPT:\n{result.get('script')}")
