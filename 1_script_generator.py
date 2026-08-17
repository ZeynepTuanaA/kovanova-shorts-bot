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
    5. Video için TAM 7 ADET İngilizce 'video_prompts' yaz.
       - GÖRSEL KALİTE VE KARAKTER KURALLARI:
         * Karakterler ve insanlar İÇERSİN. Ancak yüz ve göz anatomisi KUSURSUZ, simetrik ve fotogerçekçi (perfect symmetrical face, photorealistic eyes, detailed facial features) olmalıdır. Asla deforme, kayık veya korkunç yüzler olmasın.
         * KIYAFETLER: Kesinlikle asil, şık, dökümlü ve KAPALI olmalıdır (fully clothed in royal celestial velvet robes, majestic high-fashion hooded cloaks, ornate gold embroidery, elegant modest attire). Asla dekolte, çıplaklık veya vücut hatlarını öne çıkaran müstehcen tasvirler OLMAMALIDIR.
         * TEMATİK UYUM: Her görsel doğrudan {zodiac_sign} burcunun astrolojik teması, Zodyak elementleri, altın Zodyak sembolleri, kadim haritalar ve kozmik galaksiyle iç içe olmalıdır.
         * 1. Görsel: {zodiac_sign} burcunu temsil eden asil, kusursuz yüzlü bir figürün görkemli portresi (altın taç, kraliyet cübbesi, parlayan Zodyak amblemi).
         * 2. Görsel: Gökyüzündeki Güneş ve gezegen hizalanmasına bakan asil pelerinli figür.
         * 3. Görsel: Altın astrolab ve yıldız haritası tutan zarif bir astrolog portresi.
         * 4. Görsel: {zodiac_sign} takımyıldızının ışıltısı altında duran görkemli cübbeli bilge.
         * 5. Görsel: Kozmik kristal portala odaklanan asil bir figür.
         * 6. Görsel: Nebula ve Zodyak çarkı önünde duran estetik figür.
         * 7. Görsel: Dönen altın Kader Çarkı ve kozmik ışıklar içindeki görkemli figür.
         * Her promptun sonuna ekle: "masterpiece, photorealistic digital art, perfect facial symmetry, detailed eyes, fully clothed in elegant royal attire, cinematic lighting, 8k resolution, vertical 9:16 aspect ratio".
    
    Çıktını SADECE JSON formatında ver:
    {{
        "script": "Türkçe metin",
        "video_prompts": [
            "İngilizce prompt 1",
            "İngilizce prompt 2",
            "İngilizce prompt 3",
            "İngilizce prompt 4",
            "İngilizce prompt 5",
            "İngilizce prompt 6",
            "İngilizce prompt 7"
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
        if script and valid_prompts:
            return {"script": script, "video_prompts": valid_prompts[:7]}
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
