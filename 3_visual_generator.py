"""
Kovanova Studios — Gorsel Uretici (Gemini + Pollinations Fallback)
Gemini image generation modeli primary olarak kullanilir.
Kota doluysa Pollinations AI'a fallback yapar.
Her video icin 7 adet yuksek kaliteli gorsel uretir.
"""
import json
import os
import glob
import time
import random
import urllib.request
import urllib.parse
import urllib.error
from dotenv import load_dotenv

load_dotenv()

# Gemini SDK'yi yukle (opsiyonel — yuklu degilse sadece Pollinations kullanilir)
try:
    from google import genai
    from google.genai import types
    from PIL import Image
    from io import BytesIO
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

api_key = os.getenv("GEMINI_API_KEY")


def generate_with_gemini(prompt, output_path):
    """Gemini image generation ile gorsel uretir."""
    if not GEMINI_AVAILABLE or not api_key:
        return False

    try:
        client = genai.Client(api_key=api_key)
        enhanced_prompt = (
            f"{prompt} "
            "Mystical astrology aesthetic, beautiful illustration, perfect anatomy, "
            "well-proportioned figures, highly detailed, vibrant colors, "
            "8k resolution, vertical composition 9:16 aspect ratio, "
            "no text, no watermark, no scary or creepy elements."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                image = image.resize((1080, 1920), Image.LANCZOS)
                image.save(output_path, quality=95)
                return True

        return False
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print(f"    Gemini kota doldu, Pollinations'a geciliyor...")
        else:
            print(f"    Gemini hatasi: {e}")
        return False


def generate_with_pollinations(prompt, output_path):
    """Pollinations AI ile gorsel uretir (fallback)."""
    enhanced_prompt = f"{prompt}, mystical, beautiful illustration, perfect anatomy, highly detailed, 8k resolution, vertical video format"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    ]

    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}&model=flux"

    try:
        headers = {'User-Agent': random.choice(user_agents), 'Accept': 'image/*'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"    Pollinations hatasi: {e}")
        return False


def generate_images(prompts, output_dir="images"):
    """
    Gorselleri uretir. Oncelikle Gemini, kota doluysa Pollinations.
    """
    print("Gorsel uretici baslatiliyor (Gemini + Pollinations fallback)...")

    os.makedirs(output_dir, exist_ok=True)

    # Eski gorselleri temizle
    for ext in ("*.jpg", "*.png"):
        for f in glob.glob(os.path.join(output_dir, ext)):
            try:
                os.remove(f)
            except OSError:
                pass

    gemini_failed = False  # Gemini kota dolduysa butun sonrakilerde Pollinations kullan
    success_count = 0

    for i, prompt in enumerate(prompts):
        print(f"\n  Gorsel {i+1}/{len(prompts)} uretiliyor...")
        output_path = os.path.join(output_dir, f"image_{i+1}.png")

        saved = False

        # Gemini'yi dene (kota dolmadiysa)
        if not gemini_failed:
            for attempt in range(2):
                ok = generate_with_gemini(prompt, output_path)
                if ok:
                    print(f"  [OK] Gorsel {i+1} kaydedildi (Gemini): {output_path}")
                    saved = True
                    success_count += 1
                    break
                else:
                    gemini_failed = True  # Gemini basarisiz, artik Pollinations kullan
                    break
            if saved:
                time.sleep(5)  # Gemini rate limit
                continue

        # Pollinations fallback
        for attempt in range(3):
            ok = generate_with_pollinations(prompt, output_path)
            if ok:
                print(f"  [OK] Gorsel {i+1} kaydedildi (Pollinations): {output_path}")
                saved = True
                success_count += 1
                break
            else:
                print(f"  [!] Gorsel {i+1}: Pollinations basarisiz (Deneme {attempt+1}/3)")
                time.sleep(15)

        if not saved:
            print(f"  [HATA] Gorsel {i+1} uretilemedi!")

        time.sleep(8)  # Rate limit beklemesi

    print(f"\nSonuc: {success_count}/{len(prompts)} gorsel basariyla uretildi.")


def main():
    try:
        with open("current_script.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            prompts = data.get("video_prompts", [])

            if not prompts:
                print("Hata: current_script.json icinde gorsel komutlari bulunamadi.")
                return

            print(f"Toplam {len(prompts)} adet gorsel uretilecek.")
            generate_images(prompts)

    except FileNotFoundError:
        print("Hata: current_script.json dosyasi bulunamadi. Once 1_script_generator.py'yi calistirin.")
    except Exception as e:
        print(f"Beklenmeyen bir hata olustu: {e}")


if __name__ == "__main__":
    main()
