"""
Kovanova Studios — Yüksek Kaliteli Mistik Astroloji Görsel Üretici (FAL AI + Pollinations Fallback)
Asil, kusursuz yüz detaylarına ve şık kapalı kıyafetlere sahip büyüleyici karakterler üretir.
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

def get_fal_key():
    key = os.getenv("FAL_API_KEY")
    if key:
        return key
    env_path = r"c:\Users\HUAWEI\Desktop\Antigravity\_knowledge\credentials\master.env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("FAL_API_KEY="):
                    return line.strip().split("=", 1)[1].strip("\"'")
    return None

FAL_KEY = get_fal_key()
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

def generate_with_fal(prompt, output_path):
    """FAL AI (FLUX.1 Schnell) ile kusursuz yüz, simetrik gözler ve asil kıyafetli görsel üretir."""
    if not FAL_KEY:
        return False
    try:
        import fal_client
        
        enhanced_prompt = (
            f"{prompt}, masterpiece, photorealistic digital art, perfect symmetrical face, "
            "detailed expressive eyes, natural skin texture, fully clothed in elegant royal celestial attire, "
            "ornate golden embroidery, velvet robes, cinematic lighting, 8k resolution"
        )
        
        handler = fal_client.submit(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": enhanced_prompt,
                "image_size": "portrait_16_9",
                "num_inference_steps": 4,
                "enable_safety_checker": True
            }
        )
        result = handler.get()
        images = result.get("images", [])
        if images and "url" in images[0]:
            img_url = images[0]["url"]
            urllib.request.urlretrieve(img_url, output_path)
            return True
        return False
    except Exception as e:
        print(f"    FAL AI hatası: {e}")
        return False

def generate_with_pollinations(prompt, output_path):
    """Pollinations AI ile asil ve kaliteli karakter görseli üretir (Fallback)."""
    enhanced_prompt = (
        f"{prompt}, masterpiece, highly detailed face, perfect symmetrical eyes, "
        "fully clothed in royal celestial velvet robes, ornate gold patterns, 8k resolution, vertical 9:16 format"
    )
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}&model=flux"

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    try:
        headers = {'User-Agent': random.choice(user_agents), 'Accept': 'image/*'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"    Pollinations hatası: {e}")
        return False

def generate_images(prompts, output_dir="images"):
    print("Mistik Astroloji Karakter ve Sahne Görselleri Üretiliyor...")
    os.makedirs(output_dir, exist_ok=True)

    for ext in ("*.jpg", "*.png"):
        for f in glob.glob(os.path.join(output_dir, ext)):
            try:
                os.remove(f)
            except OSError:
                pass

    success_count = 0
    for i, prompt in enumerate(prompts):
        print(f"\n  Görsel {i+1}/{len(prompts)} üretiliyor...")
        output_path = os.path.join(output_dir, f"image_{i+1}.png")
        saved = False

        if FAL_KEY:
            ok = generate_with_fal(prompt, output_path)
            if ok:
                print(f"  [OK] Görsel {i+1} FAL AI ile üretildi: {output_path}")
                saved = True
                success_count += 1
                time.sleep(1)
                continue

        for attempt in range(3):
            ok = generate_with_pollinations(prompt, output_path)
            if ok:
                print(f"  [OK] Görsel {i+1} Pollinations ile üretildi: {output_path}")
                saved = True
                success_count += 1
                break
            else:
                print(f"  [!] Görsel {i+1} tekrar deneniyor ({attempt+1}/3)...")
                time.sleep(5)

        if not saved:
            print(f"  [HATA] Görsel {i+1} üretilemedi!")
        time.sleep(2)

    print(f"\nSonuç: {success_count}/{len(prompts)} görsel başarıyla üretildi.")

def main():
    try:
        with open("current_script.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            prompts = data.get("video_prompts", [])
            if not prompts:
                print("Hata: current_script.json içinde görsel komutları bulunamadı.")
                return
            generate_images(prompts)
    except FileNotFoundError:
        print("Hata: current_script.json bulunamadı.")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
