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
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        
        for attempt in range(max_retries):
            seed = random.randint(1, 99999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}"
            output_path = os.path.join(output_dir, f"image_{i+1}.jpg")
            try:
                headers = {'User-Agent': random.choice(user_agents), 'Accept': 'image/jpeg'}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=45) as response, open(output_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Gorsel {i+1} basariyla kaydedildi: {output_path}")
                time.sleep(10) # Bekleme süresini uzattık
                break # Başarılı olursa döngüden çık
            except urllib.error.HTTPError as e:
                print(f"Gorsel {i+1} uretilirken HTTP hatası (Deneme {attempt+1}/{max_retries}): {e}")
                time.sleep(15)
            except Exception as e:
                print(f"Gorsel {i+1} uretilirken hata (Deneme {attempt+1}/{max_retries}): {e}")
                time.sleep(15)

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
