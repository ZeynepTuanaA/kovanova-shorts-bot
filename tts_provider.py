"""
Kovanova Studios — Modüler TTS Sağlayıcı Mimarisi
Ana Sağlayıcı: Fish Audio (s2.1-pro-free / Reference Voice / Clone)

Yapılandırma Kuralları:
- FISH_MODEL: TTS model adı (Varsayılan: s2.1-pro-free).
- FISH_REFERENCE_ID: Fish Audio'daki ses/klon model kimliği.
- TTS_MODE:
    * 'fish_voice': Hazır Fish Audio sesi. FISH_REFERENCE_ID opsiyoneldir.
    * 'fish_clone': Klonlanmış özel referans ses. FISH_REFERENCE_ID ZORUNLUDUR.
"""
import os
import re
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TTSProvider")


class TextPreprocessor:
    """
    Türkçe metinleri TTS için optimize eden ve temizleyen yardımcı sınıf.
    - Türkçe karakterleri (ç, ğ, ı, İ, ö, ş, ü) KESİNLİKLE KORUR.
    - Emojileri, markdown işaretlerini, HTML etiketlerini, URL ve hashtag'leri temizler.
    - Astroloji ve burç isimlerinin doğru telaffuzu için fonetik düzeltmeler yapar.
    """

    # Astroloji telaffuz sözlüğü (İngilizce/yabancı terimlerin Türkçe karşılıkları)
    PRONUNCIATION_MAP = {
        r'\bAries\b': 'Koç',
        r'\bTaurus\b': 'Boğa',
        r'\bGemini\b': 'İkizler',
        r'\bCancer\b': 'Yengeç',
        r'\bLeo\b': 'Aslan',
        r'\bVirgo\b': 'Başak',
        r'\bLibra\b': 'Terazi',
        r'\bScorpio\b': 'Akrep',
        r'\bSagittarius\b': 'Yay',
        r'\bCapricorn\b': 'Oğlak',
        r'\bAquarius\b': 'Kova',
        r'\bPisces\b': 'Balık',
        r'\bretrograde\b': 'retro',
        r'\beclipse\b': 'tutulma',
        r'\bconstellation\b': 'takımyıldız',
    }

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""

        # 1. HTML ve Markdown etiketlerini kaldır
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[*_~`#>]', '', text)

        # 2. URL ve linkleri temizle
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # 3. Hashtag ve etiketleri temizle
        text = re.sub(r'#\w+', '', text)

        # 4. Yabancı astroloji terimlerini Türkçeleştir
        for pattern, replacement in cls.PRONUNCIATION_MAP.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 5. Emojileri ve özel sembolleri temizle (Türkçe karakterleri ve temel noktalamayı koruyarak)
        allowed_pattern = r'[^a-zA-Z0-9\sçÇğĞıİöÖşŞüÜ\.\,\!\?\:\;\-\'\"]'
        text = re.sub(allowed_pattern, ' ', text)

        # 6. Tekrarlayan noktalama ve fazla boşlukları düzenle
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([\.?!])\1+', r'\1', text)

        return text.strip()


class TTSProvider(ABC):
    """Tüm TTS sağlayıcıları için ortak soyut (abstract) arayüz."""

    @abstractmethod
    def generate_speech(
        self,
        text: str,
        output_path: str = "audio.mp3",
        reference_id: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Metni sese dönüştürür ve dosyaya kaydeder.
        Dönen değer: Metadata sözlüğü (provider, model, reference_id, text, created_at vb.)
        """
        pass


class FishAudioTTS(TTSProvider):
    """
    Fish Audio S2.1 Pro TTS Sağlayıcısı
    API Endpoint: https://api.fish.audio/v1/tts
    """
    API_URL = "https://api.fish.audio/v1/tts"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        reference_id: Optional[str] = None,
        tts_mode: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("FISH_API_KEY")
        self.model = model or os.getenv("FISH_MODEL", "s2.1-pro-free")
        self.reference_id = reference_id or os.getenv("FISH_REFERENCE_ID")
        self.tts_mode = (tts_mode or os.getenv("TTS_MODE", "fish_voice")).lower().strip()

    def _resolve_reference_id(self, override_ref_id: Optional[str] = None) -> Optional[str]:
        """
        Kullanılacak reference ID'yi belirler ve mod doğrulaması yapar.
        - fish_clone modunda reference_id zorunludur.
        - fish_voice modunda reference_id opsiyoneldir.
        """
        ref_id = override_ref_id or self.reference_id
        if self.tts_mode == "fish_clone":
            if not ref_id:
                raise ValueError(
                    "[HATA] TTS_MODE 'fish_clone' olarak ayarlandı fakat FISH_REFERENCE_ID belirtilmedi! "
                    "Lütfen .env dosyasında FISH_REFERENCE_ID=<klon_id> tanımlayın veya TTS_MODE=fish_voice yapın."
                )
            return ref_id
        # fish_voice modu (opsiyonel reference ID desteği)
        return ref_id if ref_id else None

    def generate_speech(
        self,
        text: str,
        output_path: str = "audio.mp3",
        reference_id: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Fish Audio API ile Türkçe metni seslendirir ve MP3 olarak kaydeder.
        Exponential backoff ve 3 denemeli retry mekanizması içerir.
        """
        if not self.api_key:
            raise ValueError("[HATA] FISH_API_KEY bulunamadı! Lütfen .env dosyasında FISH_API_KEY tanımlayın.")

        # Metni temizle ve optimize et
        cleaned_text = TextPreprocessor.clean(text)
        if not cleaned_text:
            raise ValueError("[HATA] Seslendirilecek metin boş veya geçersiz!")

        active_ref_id = self._resolve_reference_id(reference_id)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "model": self.model
        }

        payload: Dict[str, Any] = {
            "text": cleaned_text,
            "format": audio_format,
            "mp3_bitrate": 128,
            "latency": "normal",
            "normalize": True
        }

        # Eğer reference_id varsa payload'a ekle
        if active_ref_id:
            payload["reference_id"] = active_ref_id

        logger.info(
            f"Fish Audio TTS çağrısı başlatılıyor | Model Header: {self.model} | "
            f"Mod: {self.tts_mode} | Reference ID: {active_ref_id or 'Yok (Varsayılan Ses)'}"
        )

        # Retry döngüsü (3 deneme)
        max_retries = 3
        backoff_delays = [2.5, 5.5, 10.0]

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                # Kalıcı yetkilendirme / kredi hatalarında hemen dur
                if response.status_code in (401, 402, 403):
                    error_msg = f"Fish Audio API Hatası ({response.status_code}): {response.text}"
                    logger.error(error_msg)
                    raise PermissionError(error_msg)

                if response.status_code == 200:
                    output_dir = os.path.dirname(os.path.abspath(output_path))
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(response.content)

                    logger.info(f"Ses başarıyla üretildi ve kaydedildi: '{output_path}' ({len(response.content)} bayt)")

                    metadata = {
                        "provider": "fish_audio",
                        "model": self.model,
                        "reference_id": active_ref_id or "default",
                        "mode": self.tts_mode,
                        "language": "tr",
                        "text": cleaned_text,
                        "format": audio_format,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    return metadata

                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"Fish Audio deneme {attempt}/{max_retries} başarısız: {error_msg}")
                    last_error = RuntimeError(error_msg)

            except PermissionError:
                raise
            except Exception as e:
                logger.warning(f"Fish Audio deneme {attempt}/{max_retries} bağlantı hatası: {e}")
                last_error = e

            if attempt < max_retries:
                delay = backoff_delays[attempt - 1]
                logger.info(f"{delay} saniye bekleniyor...")
                time.sleep(delay)

        raise RuntimeError(f"Fish Audio TTS {max_retries} denemede de başarısız oldu! Son hata: {last_error}")


def get_tts_provider() -> TTSProvider:
    """
    Fabrika fonksiyonu: Aktif TTS sağlayıcısını döner.
    Şu an ana sağlayıcı: FishAudioTTS
    """
    return FishAudioTTS()
