import json
import os
import urllib.request
import urllib.parse

def generate_images(prompts, output_dir="images"):
    print("Ücretsiz Görsel Üretici (Pollinations AI) başlatılıyor...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for i, prompt in enumerate(prompts):
        print(f"Görsel {i+1} üretiliyor... (Bu işlem yaklaşık 10-15 saniye sürebilir)")
        
        # Prompt'u URL formatına uygun hale getir
        # style: cinematic, aspect ratio: 9:16 (1080x1920)
        enhanced_prompt = f"{prompt}, cinematic lighting, photorealistic, highly detailed, 8k resolution, vertical video format"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        import random
        seed = random.randint(1, 99999999)
        # Pollinations AI API'si ile en yüksek kalite ayarları (model=flux, enhance=true) ve rastgele seed
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&model=flux&enhance=true&seed={seed}"
        output_path = os.path.join(output_dir, f"image_{i+1}.jpg")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response, open(output_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Gorsel {i+1} basariyla kaydedildi: {output_path}")
        except Exception as e:
            print(f"Gorsel {i+1} uretilirken hata olustu: {e}")

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
