"""
Kovanova Studios — Gelişmiş Pexels Burç ve Zodyak Kürasyon Motoru
Her burç için 7 tematik astrolojik katman oluşturur:
1. Burcun Sembolik Canlısı / Motifi (Pisces için: İki Balık / Yin Yang Koi)
2. Astrolog / Mistik Karakter (Tarot & Astroloji haritası bakan bilge/kadın)
3. Altın Zodyak Çarkı / Astronomik Saat (Zodiac Clock Wheel)
4. Burcun Mistik Karakter Portresi (Burç elementini taşıyan fantezi figürü)
5. Doğum Haritası / Astroloji Haritası (Natal Astrology Chart & Crystals)
6. Mistik Tarot Kartı / Kader Çarkı (Tarot Card The Star / Wheel of Fortune)
7. Burcun Elementi ve Kozmik Işıltı (Deep Blue Water / Cosmic Glow)
"""
import os
import json
import time
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PexelsClient")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "pexels")
CACHE_INDEX_FILE = os.path.join(CACHE_DIR, "index.json")


# 12 BURÇ İÇİN 7 KATMANLI DOĞRUDAN ASTROLOJİ & ZODYAK SORGULARI
ZODIAC_STORYBOARD_QUERIES: Dict[str, List[Dict[str, str]]] = {
    "Pisces": [
        {"slot": "1_symbol", "query": "two koi fish swimming circle pond", "fallback": "two fish swimming together"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical blue water woman fantasy portrait", "fallback": "fantasy character blue makeup underwater"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "tarot card the star mystical setup", "fallback": "mystical tarot card reading setup"},
        {"slot": "7_element_ocean", "query": "deep blue ocean water glowing underwater", "fallback": "marine fish swimming blue aquatic"}
    ],
    "Aries": [
        {"slot": "1_symbol", "query": "ram with big horns majestic", "fallback": "powerful ram horns"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical warrior woman red fire armor portrait", "fallback": "dark fantasy woman horns flames"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "tarot card reading mystical candles", "fallback": "person holding the sun tarot card"},
        {"slot": "7_element_fire", "query": "dramatic red flames fire energy dark", "fallback": "fire flame glowing sparks night"}
    ],
    "Taurus": [
        {"slot": "1_symbol", "query": "majestic bull horns nature", "fallback": "strong bull gold aesthetic"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical forest woman green velvet dress portrait", "fallback": "ethereal earth goddess flowers nature"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "tarot card reading mystical candles", "fallback": "the empress tarot card nature"},
        {"slot": "7_element_earth", "query": "emerald green luxury botanical gold nature", "fallback": "lush forest sunlight green plants"}
    ],
    "Gemini": [
        {"slot": "1_symbol", "query": "ethereal twin sisters reflection mirror fantasy", "fallback": "two women portrait reflection"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical woman duality shadow light fantasy portrait", "fallback": "two woman with neon face paints"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "tarot card reading mystical candles", "fallback": "mystical tarot card setup"},
        {"slot": "7_element_air", "query": "dreamy wind clouds pastel ethereal sky", "fallback": "silver light rays aesthetic"}
    ],
    "Cancer": [
        {"slot": "1_symbol", "query": "mystical moon water ocean reflection", "fallback": "full moon ocean waves night"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical moon goddess silver pearls water portrait", "fallback": "ethereal woman moonlight water night"},
        {"slot": "5_astrology_chart", "query": "astrology moon phases calendar crystals", "fallback": "astrology chart cards notebook"},
        {"slot": "6_tarot_destiny", "query": "tarot card the moon mystical setup", "fallback": "tarot card reading candles"},
        {"slot": "7_element_water", "query": "serene ocean water waves silver moonlight", "fallback": "pearls seashells water aesthetic"}
    ],
    "Leo": [
        {"slot": "1_symbol", "query": "majestic male lion golden mane close up", "fallback": "powerful lion gold sunlight"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "regal queen gold crown dramatic lighting portrait", "fallback": "majestic golden goddess fantasy portrait"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "person holding the sun tarot card close up", "fallback": "the sun tarot card golden"},
        {"slot": "7_element_sun", "query": "golden sunlight rays luxury gold texture", "fallback": "glowing gold light dramatic"}
    ],
    "Virgo": [
        {"slot": "1_symbol", "query": "wheat field golden harvest botanical", "fallback": "delicate flowers botanical aesthetic"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "elegant celestial woman flowers botanical portrait", "fallback": "ethereal goddess nature flowers"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "the hermit tarot card mystical setup", "fallback": "tarot card reading crystals"},
        {"slot": "7_element_earth", "query": "mystical green botanical leaves aesthetic", "fallback": "soft nature flowers aesthetic"}
    ],
    "Libra": [
        {"slot": "1_symbol", "query": "stones on old fashioned scale balance", "fallback": "brass justice scales balance"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "elegant celestial woman romantic pink gown portrait", "fallback": "mystical beauty goddess fantasy"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "justice tarot card mystical candles", "fallback": "the lovers tarot card setup"},
        {"slot": "7_element_romance", "query": "soft pink rose aesthetic gold sparkles", "fallback": "pastel romantic clouds aesthetic"}
    ],
    "Scorpio": [
        {"slot": "1_symbol", "query": "black scorpion macro dark aesthetic", "fallback": "scorpion mystical shadow"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "dark gothic fantasy woman crimson veil portrait", "fallback": "mysterious dark witch woman"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "death tarot card transformation mystical", "fallback": "tarot card reading dark candles"},
        {"slot": "7_element_eclipse", "query": "solar eclipse dark red crimson sky", "fallback": "dark water reflection night moody"}
    ],
    "Sagittarius": [
        {"slot": "1_symbol", "query": "archer holding bow arrow golden sunlight", "fallback": "traditional bow arrows mystical"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "mystical warrior woman bow arrows fantasy portrait", "fallback": "cosmic adventure woman purple fire"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "temperance tarot card reading setup", "fallback": "wheel of fortune tarot card"},
        {"slot": "7_element_fire", "query": "cosmic purple flame sparks universe", "fallback": "bonfire sparks night stars"}
    ],
    "Capricorn": [
        {"slot": "1_symbol", "query": "majestic mountain goat rocky peak", "fallback": "mountain peak night moody"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "dark luxury woman horns mountain fantasy portrait", "fallback": "powerful dark queen stone castle"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "the devil tarot card mystical setup", "fallback": "tarot card reading crystals"},
        {"slot": "7_element_earth", "query": "dark stone fortress mountain rocks moody", "fallback": "black marble gold texture"}
    ],
    "Aquarius": [
        {"slot": "1_symbol", "query": "water pouring from clay urn vase water bearer", "fallback": "water flowing in clear stream"},
        {"slot": "2_astrologist", "query": "woman astrologist reading tarot cards table", "fallback": "person marking astrology chart"},
        {"slot": "3_zodiac_wheel", "query": "Torre dell Orologio zodiac clock gold", "fallback": "zodiac clock tower marks"},
        {"slot": "4_zodiac_character", "query": "futuristic ethereal woman glowing water neon portrait", "fallback": "celestial woman electric blue lights"},
        {"slot": "5_astrology_chart", "query": "astrology chart cards notebook crystals", "fallback": "astrology moon phases calendar"},
        {"slot": "6_tarot_destiny", "query": "the star tarot card glowing celestial", "fallback": "the star card display open book"},
        {"slot": "7_element_electric", "query": "electric blue water splash neon lighting", "fallback": "cyan glowing neon lights abstract"}
    ]
}


class PexelsCache:
    """Pexels görsel sonuçlarını ve indirilen dosyaları yerel diskte saklar."""

    def __init__(self, cache_dir: str = CACHE_DIR, index_file: str = CACHE_INDEX_FILE):
        self.cache_dir = cache_dir
        self.index_file = index_file
        os.makedirs(self.cache_dir, exist_ok=True)
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Cache index okunamadı: {e}. Yeni index oluşturuluyor.")
        return {}

    def _save_index(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Cache index kaydedilemedi: {e}")

    def add(self, photo_data: Dict[str, Any], local_path: str, search_query: str, slot: str = ""):
        photo_id = str(photo_data.get("id"))
        self.index[photo_id] = {
            "photo_id": photo_id,
            "pexels_url": photo_data.get("url", ""),
            "photographer": photo_data.get("photographer", "Pexels Creator"),
            "photographer_url": photo_data.get("photographer_url", ""),
            "download_url": photo_data.get("src", {}).get("large2x") or photo_data.get("src", {}).get("original"),
            "search_query": search_query,
            "slot": slot,
            "local_path": local_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_index()


class ImageProcessor:
    """Görselleri 1080x1920 (9:16) formatına kayıpsız ve merkezli kırpar/boyutlandırır."""

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT  # 9/16 = 0.5625

    @classmethod
    def process_to_shorts_format(cls, input_path: str, output_path: str) -> bool:
        """Pexels ham görselini 9:16 oranına göre ortalayarak tam 1080x1920 piksel olarak kaydeder."""
        try:
            with Image.open(input_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img_w, img_h = img.size
                current_ratio = img_w / img_h

                if current_ratio > cls.TARGET_RATIO:
                    new_w = int(img_h * cls.TARGET_RATIO)
                    left = (img_w - new_w) // 2
                    right = left + new_w
                    top = 0
                    bottom = img_h
                else:
                    new_h = int(img_w / cls.TARGET_RATIO)
                    top = (img_h - new_h) // 2
                    bottom = top + new_h
                    left = 0
                    right = img_w

                cropped = img.crop((left, top, right, bottom))
                resized = cropped.resize((cls.TARGET_WIDTH, cls.TARGET_HEIGHT), Image.Resampling.LANCZOS)
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                resized.save(output_path, "PNG", quality=95)
                return True
        except Exception as e:
            logger.error(f"Görsel işleme hatası ({input_path}): {e}")
            return False


class PexelsClient:
    """Pexels API üzerinden doğrudan burç/astroloji temalı görsel kürasyon istemcisi."""

    API_SEARCH_URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.cache = PexelsCache()
        self.processor = ImageProcessor()

    def search_photos(self, query: str, per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """Pexels API üzerinden orientation=portrait parametresiyle görsel çeker."""
        if not self.api_key:
            logger.warning("[UYARI] PEXELS_API_KEY tanımlanmamış!")
            return []

        headers = {
            "Authorization": self.api_key,
            "User-Agent": "KovanovaShortsBot/2.0"
        }

        params = {
            "query": query,
            "orientation": "portrait",
            "per_page": per_page,
            "page": page
        }

        try:
            response = requests.get(self.API_SEARCH_URL, headers=headers, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                return data.get("photos", [])
            else:
                logger.warning(f"Pexels API hatası (HTTP {response.status_code}): {response.text}")
                return []
        except Exception as e:
            logger.error(f"Pexels API bağlantı hatası: {e}")
            return []

    def download_and_prepare_image(
        self,
        photo_data: Dict[str, Any],
        output_path: str,
        search_query: str,
        slot_name: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Görseli indirir, cache'e kaydeder, 1080x1920 dikey kırpma yapar ve attribution döner."""
        photo_id = str(photo_data.get("id"))
        src = photo_data.get("src", {})
        download_url = src.get("large2x") or src.get("portrait") or src.get("original") or src.get("large")
        
        if not download_url:
            return None

        cache_raw_path = os.path.join(self.cache.cache_dir, f"raw_{photo_id}.jpg")

        if not os.path.exists(cache_raw_path):
            try:
                res = requests.get(download_url, timeout=30)
                if res.status_code == 200:
                    with open(cache_raw_path, "wb") as f:
                        f.write(res.content)
                    self.cache.add(photo_data, cache_raw_path, search_query, slot=slot_name)
                else:
                    return None
            except Exception as e:
                logger.warning(f"Görsel indirme başarısız ({download_url}): {e}")
                return None

        success = self.processor.process_to_shorts_format(cache_raw_path, output_path)
        if success:
            return {
                "photo_id": photo_id,
                "title": photo_data.get("alt", "Zodiac Visual"),
                "pexels_url": photo_data.get("url", ""),
                "photographer": photo_data.get("photographer", "Pexels Creator"),
                "photographer_url": photo_data.get("photographer_url", ""),
                "search_query": search_query,
                "slot": slot_name,
                "output_path": output_path
            }
        return None

    def fetch_zodiac_storyboard_visuals(
        self,
        zodiac_name: str = "Pisces",
        output_dir: str = "images"
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Belirtilen burç için 7 tematik astrolojik katmandan (Sembol, Astrolog, Zodyak Çarkı, 
        Mistik Karakter, Doğum Haritası, Tarot, Element) en uygun 7 dikey görseli bulup hazırlar.
        """
        os.makedirs(output_dir, exist_ok=True)
        zodiac_key = zodiac_name.capitalize()
        storyboard_slots = ZODIAC_STORYBOARD_QUERIES.get(zodiac_key, ZODIAC_STORYBOARD_QUERIES["Pisces"])

        logger.info(f"🔮 {zodiac_key} Burcu İçin 7 Katmanlı Astroloji & Zodyak Storyboard Araması Başlatılıyor...")

        prepared_images: List[str] = []
        attributions: List[Dict[str, Any]] = []
        used_photo_ids = set()

        for idx, slot_info in enumerate(storyboard_slots, start=1):
            slot_name = slot_info["slot"]
            primary_query = slot_info["query"]
            fallback_query = slot_info.get("fallback", "")

            out_file = os.path.join(output_dir, f"image_{idx}.png")
            saved_attr = None

            # 1. Ana sorguyu dene
            logger.info(f"  [{idx}/7] Katman '{slot_name}' aranıyor: '{primary_query}'...")
            photos = self.search_photos(primary_query, per_page=10)

            for p in photos:
                p_id = str(p.get("id"))
                if p_id not in used_photo_ids:
                    saved_attr = self.download_and_prepare_image(p, out_file, primary_query, slot_name=slot_name)
                    if saved_attr:
                        used_photo_ids.add(p_id)
                        prepared_images.append(out_file)
                        attributions.append(saved_attr)
                        logger.info(f"    ✅ [OK] Katman #{idx} ({slot_name}) Pexels'ten hazırlandı: '{saved_attr['title']}' ({saved_attr['photographer']})")
                        break

            # 2. Eğer bulunamadıysa yedek sorguyu dene
            if not saved_attr and fallback_query:
                logger.info(f"    🔄 Yedek sorgu deneniyor: '{fallback_query}'...")
                fb_photos = self.search_photos(fallback_query, per_page=8)
                for p in fb_photos:
                    p_id = str(p.get("id"))
                    if p_id not in used_photo_ids:
                        saved_attr = self.download_and_prepare_image(p, out_file, fallback_query, slot_name=slot_name)
                        if saved_attr:
                            used_photo_ids.add(p_id)
                            prepared_images.append(out_file)
                            attributions.append(saved_attr)
                            logger.info(f"    ✅ [OK Yedek] Katman #{idx} hazırlandı: '{saved_attr['title']}' ({saved_attr['photographer']})")
                            break

            time.sleep(0.3)  # Rate limit koruması

        logger.info(f"Toplam {len(prepared_images)}/7 katmanlı astroloji görseli başarıyla hazırlandı.")
        return prepared_images, attributions


def build_attribution_text(attributions: List[Dict[str, Any]]) -> str:
    """Video açıklamasına eklenebilecek standart ve şık Pexels attribution metni üretir."""
    if not attributions:
        return ""

    lines = ["\n\n---", "📸 Görseller / Photos provided by Pexels:"]
    seen_photographers = set()
    for attr in attributions:
        photographer = attr.get("photographer")
        if photographer and photographer not in seen_photographers:
            seen_photographers.add(photographer)
            p_url = attr.get("pexels_url")
            if p_url:
                lines.append(f"• {photographer} ({p_url})")
            else:
                lines.append(f"• {photographer}")
    return "\n".join(lines)
