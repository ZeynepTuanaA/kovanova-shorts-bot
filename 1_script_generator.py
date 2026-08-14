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
    import random
    bugun = datetime.datetime.now().strftime("%d %B %Y")
    
    concepts = [
        "Mistik Astroloji ve Yıldız Haritaları", "Kozmik Galaksi ve Nebula", "Tarot Kartı Estetiği", 
        "Altın Oran ve Kutsal Geometri", "Rüya Alemi ve Pastel Tonlar", "Sulu Boya Astrolojik Figürler", 
        "Zodyak Çarkı ve Kozmik Işıklar", "Eterik Aura ve Parlayan Takımyıldızlar", "Rönesans Astrolojisi",
        "Kristal Astroloji ve Şifa Enerjisi", "Güneş Tutulması ve Kozmik Kapı", "Masalsı Gökyüzü ve Burç Sembolleri"
    ]
    random_concept = random.choice(concepts)
    
    prompt = f"""
    Sen 'Kovanova Studios' adlı bir YouTube kanalı için içerik üreten profesyonel ve gerçeğe sadık bir astrologsun.
    Konseptimiz: Gerçek Astroloji ve Burçlar.
    Bugünün tarihi: {bugun}
    Bugünün burcu: {zodiac_sign}.
    Rastgele Odak Konsepti (bu videoyu diğerlerinden farklılaştırmak için): {random_concept}
    
    Görevlerin:
    1. LÜTFEN SALLAMA YAPMA. Bugünün ({bugun}) GERÇEK astrolojik olaylarını, gezegen geçişlerini (transitler, retro veya ay konumu vb.) dikkate alarak bu burç için özel bir yorum yap. Belirtilen 'Rastgele Odak Konsepti'ni hafifçe yoruma yedir.
    2. Okunacak metin KESİNLİKLE şu kelimelerle başlamalıdır: '{zodiac_sign} burcu, ...' veya doğrudan '{zodiac_sign}, ...'. Böylece videonun başında hangi burçtan bahsedildiği seyirciye anında iletilmiş olsun. Sonrasında 20-30 saniyede okunabilecek (yaklaşık 50-70 kelime) kısa, gizemli ve ilgi çekici bir metin yaz.
    3. Videonun başında (burç adını söyledikten hemen sonra) güçlü bir kanca (hook) olsun. Sonunda ise kapanış cümlesi olarak SADECE şu cümleyi kullan: "Kader çarkı senin için dönsün." (Abone ol vs. deme).
    4. Seslendirme robotu okuyacağı için metinde (gülümser), [müzik girer] gibi hiçbir sahne notu OLMASIN.
    5. KESİNLİKLE UNUTMA: Okunacak video metni (script) tamamen TÜRKÇE olmalıdır. Ancak video üretimi için olan 'video_prompts' kısmı İNGİLİZCE olmalıdır.
    6. Bu videonun arka planında dönecek, burcun elementine, bugünkü ruh haline ve 'Rastgele Odak Konsepti'ne uygun, yüksek kaliteli AI görsel üreticisi için TAM 7 ADET detaylı İngilizce 'video prompt' yaz. 
       - ÇOK ÖNEMLİ KURAL: Asla gerçek, vahşi veya korkunç hayvan fotoğrafları (örn. belgesel gibi gerçek bir aslan, korkunç bir yengeç vs.) İSTEME! Zodyak sembollerini mistik, astrolojik, renkli ve sanatsal bir şekilde temsil et. Yüz ve vücut anatomisinin kusursuz (perfect anatomy, well-proportioned) olması gerektiğini belirt ki deforme görseller oluşmasın. Korkutucu veya ürkütücü (creepy) hiçbir öğe kullanma. KESİNLİKLE çıplaklık veya müstehcen içerik OLMAMALI! Tüm figürler tamamen giyinik (fully clothed, elegant dress/attire) ve her yaşa uygun (SFW, no nudity) tasvir edilmelidir.
       - İLK (1.) prompt KESİNLİKLE doğrudan {zodiac_sign} burcunun astrolojik sembolünün veya mistik-insansı temsilinin çok estetik, simetrik ve sanatsal bir portresi olmalıdır. Ancak bu görseli 'Rastgele Odak Konsepti'yle harmanlayarak her videoda FARKLI ve EŞSİZ bir versiyonunu yarat! İlk görsel tamamen burcu tanıtmaya odaklı olsun!
       - Diğer 6 prompt da konuyla çok yakından bağlantılı ancak birbirinden kesinlikle farklı, çeşitli astrolojik sahneler (yakın çekimler, takımyıldızlar, büyüleyici burç figürleri, kozmik manzaralar, sembolik objeler, eterik auralar) içermelidir. Sadece manzara OLMAMALIDIR. Her görsel o burcu temsil eden estetik, renkli ve gizemli semboller veya büyüleyici insan figürleri (kadın/erkek) içerebilir.
       - Her 7 görselin kendine özgü bir sanat stili olmalı: portre, manzara+figür, yakın çekim obje, kozmik sahne, sembolik illüstrasyon, büyüleyici figür, soyut astrolojik kompozisyon gibi.
       - Her seferinde görseller BİRBİRİNDEN VE DAHA ÖNCEKİLERDEN TAMAMEN FARKLI ve ÇEŞİTLİ OLSUN!
    
    Çıktını SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama ekleme:
    {{
        "script": "Burada okunacak Türkçe metin olacak.",
        "video_prompts": [
            "İngilizce video prompt 1",
            "İngilizce video prompt 2",
            "İngilizce video prompt 3",
            "İngilizce video prompt 4",
            "İngilizce video prompt 5",
            "İngilizce video prompt 6",
            "İngilizce video prompt 7"
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
    import datetime
    
    zodiac_signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
    
    # Her gün aynı burcu seçmek için bugünün tarihine göre indeks belirliyoruz
    day_index = datetime.datetime.now().toordinal() % 12
    selected_sign = zodiac_signs[day_index]
    
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
