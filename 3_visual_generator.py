"""
Kovanova Studios — Görsel Üretim Motoru (Puter AI + Pexels Fallback)
- Ana Görsel Sağlayıcı: Puter AI (gpt-image-1) Dark Fantasy Zodyak Karakterleri
- Yedek Görsel Sağlayıcı: Pexels API 7 Katmanlı Zodyak Storyboard & Cache
- Çıktı Formatı: 1080x1920 Piksel (9:16 Dikey Shorts Formatı)
"""
import os
import sys
import json
import glob
import time
import base64
import logging
from io import BytesIO
from typing import Optional, List, Dict, Any, Tuple
import requests
from PIL import Image
from dotenv import load_dotenv

from pexels_client import PexelsClient, build_attribution_text

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VisualGenerator")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "images")

NEGATIVE_PROMPT = (
    "nudity, nude, naked, lingerie, erotic, sexual, nsfw, explicit, gore, blood, "
    "mutilation, deformed anatomy, extra limbs, extra fingers, low quality, blurry, watermark, text, logo"
)


class PuterImageGenerator:
    """Puter.com AI Image Generation REST API İstemcisi."""

    DRIVERS_CALL_URL = "https://api.puter.com/drivers/call"

    def __init__(self):
        self.auth_token = os.getenv("PUTER_AUTH_TOKEN") or os.getenv("PUTER_API_KEY")

    def process_to_shorts_9_16(self, image_bytes: bytes, output_path: str) -> bool:
        """Görseli 9:16 (1080x1920) oranında ortalayarak yüksek kalitede kaydeder."""
        target_w, target_h = 1080, 1920
        target_ratio = target_w / target_h

        try:
            with Image.open(BytesIO(image_bytes)) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img_w, img_h = img.size
                current_ratio = img_w / img_h

                if current_ratio > target_ratio:
                    new_w = int(img_h * target_ratio)
                    left = (img_w - new_w) // 2
                    right = left + new_w
                    top = 0
                    bottom = img_h
                else:
                    new_h = int(img_w / target_ratio)
                    top = (img_h - new_h) // 2
                    bottom = top + new_h
                    left = 0
                    right = img_w

                cropped = img.crop((left, top, right, bottom))
                resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                resized.save(output_path, "PNG", quality=95)
                return True
        except Exception as e:
            logger.error(f"Görsel işleme hatası: {e}")
            return False

    def generate_single_image(self, prompt: str, model: str = "gpt-image-1") -> Optional[bytes]:
        """Tek bir görsel üretir ve raw bytes döner."""
        if not self.auth_token:
            logger.warning("PUTER_AUTH_TOKEN bulunamadı.")
            return None

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "interface": "puter-image-generation",
            "driver": "ai-image",
            "method": "generate",
            "args": {
                "prompt": prompt + ", vertical 9:16 composition, highly detailed fantasy concept art, digital painting, dark fantasy aesthetic, cinematic lighting, fully clothed, no nudity",
                "negative_prompt": NEGATIVE_PROMPT,
                "model": model
            }
        }

        try:
            response = requests.post(self.DRIVERS_CALL_URL, json=payload, headers=headers, timeout=90)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result") or data

                if isinstance(result, str):
                    if result.startswith("data:image/"):
                        b64_data = result.split(",", 1)[1]
                        return base64.b64decode(b64_data)
                    elif result.startswith("http"):
                        img_res = requests.get(result, timeout=30)
                        if img_res.status_code == 200:
                            return img_res.content
                elif isinstance(result, dict):
                    url = result.get("image_url") or result.get("url")
                    if url and url.startswith("http"):
                        img_res = requests.get(url, timeout=30)
                        if img_res.status_code == 200:
                            return img_res.content
                    b64_raw = result.get("data")
                    if b64_raw:
                        return base64.b64decode(b64_raw)
            else:
                logger.warning(f"Puter API Hatası (HTTP {response.status_code}): {response.text[:150]}")
                return None
        except Exception as e:
            logger.error(f"Puter API bağlantı hatası: {e}")
            return None


def generate_visuals(script_data_path="current_script.json", output_dir="images", target_count=7):
    """
    current_script.json içindeki promptları okur.
    Önce Puter AI (gpt-image-1) ile 7 adet dark fantasy görsel üretmeyi dener.
    Eğer herhangi biri başarısız olursa Pexels 7 Katmanlı Astroloji Storyboard motorunu devreye sokar.
    """
    if not os.path.exists(script_data_path):
        logger.error(f"Hata: '{script_data_path}' bulunamadı. Önce 1_script_generator.py'yi çalıştırın.")
        return False

    with open(script_data_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    zodiac_sign = script_data.get("zodiac_sign", "Balık")
    theme = script_data.get("theme", "Astroloji")
    prompts = script_data.get("video_prompts", [])

    logger.info(f"🔮 Görsel Üretimi Başlatılıyor (Burç: {zodiac_sign}, Tema: {theme})...")

    # Eski görselleri temizle
    os.makedirs(output_dir, exist_ok=True)
    for ext in ("*.jpg", "*.png"):
        for f in glob.glob(os.path.join(output_dir, ext)):
            try:
                os.remove(f)
            except OSError:
                pass

    puter_generator = PuterImageGenerator()
    generated_images = []
    
    # 1. Puter AI ile üretmeyi dene
    if puter_generator.auth_token:
        logger.info(f"✨ Puter AI (gpt-image-1) ile {target_count} görsel üretiliyor...")
        for i in range(target_count):
            prompt = prompts[i] if i < len(prompts) else f"Dark fantasy {zodiac_sign} zodiac celestial woman mystical character"
            out_path = os.path.join(output_dir, f"image_{i+1}.png")
            logger.info(f"  🎨 [{i+1}/{target_count}] Puter AI görseli üretiliyor: {prompt[:65]}...")
            
            img_bytes = puter_generator.generate_single_image(prompt, model="gpt-image-1")
            if img_bytes:
                success = puter_generator.process_to_shorts_9_16(img_bytes, out_path)
                if success:
                    generated_images.append(out_path)
                    logger.info(f"    ✅ [OK] image_{i+1}.png hazırlandı (1080x1920).")
            else:
                logger.warning(f"    ⚠️ Puter AI {i+1}. görsel için yanıt vermedi.")
            
            time.sleep(1)

    # 2. Eğer yeterli görsel üretilemediyse Pexels Fallback devreye girer
    if len(generated_images) < target_count:
        logger.warning(f"Puter AI ile {len(generated_images)}/{target_count} görsel üretildi. Eksikler Pexels ile tamamlanıyor...")
        
        zodiac_tr_to_en = {
            "Koç": "Aries", "Boğa": "Taurus", "İkizler": "Gemini", "Yengeç": "Cancer",
            "Aslan": "Leo", "Başak": "Virgo", "Terazi": "Libra", "Akrep": "Scorpio",
            "Yay": "Sagittarius", "Oğlak": "Capricorn", "Kova": "Aquarius", "Balık": "Pisces"
        }
        zodiac_en = zodiac_tr_to_en.get(zodiac_sign, "Pisces")

        client = PexelsClient()
        pexels_images, attributions = client.fetch_zodiac_storyboard_visuals(
            zodiac_name=zodiac_en,
            output_dir=output_dir
        )
        
        attr_text = build_attribution_text(attributions)
        script_data["attributions"] = attributions
        script_data["attribution_text"] = attr_text
        with open(script_data_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

    logger.info(f"🎉 Toplam {len(glob.glob(os.path.join(output_dir, '*.png')))} görsel başarıyla hazırlandı!")
    return True

def main():
    generate_visuals()

if __name__ == "__main__":
    main()
