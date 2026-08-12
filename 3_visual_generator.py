import json
import os
import urllib.request
import urllib.parse
import urllib.error
import time
import random
def generate_images(prompts, output_dir="images"):
    print("Ücretsiz Görsel Üretici (Pollinations AI) başlatılıyor...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        import glob
        for f in glob.glob(os.path.join(output_dir, "*.jpg")):
            try:
                os.remove(f)
            except:
                pass
        
        
    for i, prompt in enumerate(prompts):
        print(f"Görsel {i+1} üretiliyor... (Bu işlem yaklaşık 10-15 saniye sürebilir)")
        
        # Prompt'u URL formatına uygun hale getir
        # style: cinematic, aspect ratio: 9:16 (1080x1920)
        enhanced_prompt = f"{prompt}, cinematic lighting, photorealistic, highly detailed, 8k resolution, vertical video format"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        max_retries = 5
        for attempt in range(max_retries):
            seed = random.randint(1, 99999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}"
            output_path = os.path.join(output_dir, f"image_{i+1}.jpg")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response, open(output_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Gorsel {i+1} basariyla kaydedildi: {output_path}")
                time.sleep(5) # Bekleme süresi ekle
                break # Başarılı olursa döngüden çık
            except urllib.error.HTTPError as e:
                print(f"Gorsel {i+1} uretilirken HTTP hatası (Deneme {attempt+1}/{max_retries}): {e}")
                time.sleep(10)
            except Exception as e:
                print(f"Gorsel {i+1} uretilirken hata (Deneme {attempt+1}/{max_retries}): {e}")
                time.sleep(10)

def main():
    try:
        with open("current_script.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            prompts = data.get("video_prompts", [])
            
            if not prompts:
                print("Hata: current_script.json içinde görsel komutları bulunamadı.")
                return
                
            print(f"Toplam {len(prompts)} adet görsel üretilecek.")
            generate_images(prompts)
            
    except FileNotFoundError:
        print("Hata: prompts.json dosyası bulunamadı. Önce 1_script_generator.py'yi çalıştırın.")
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    main()
