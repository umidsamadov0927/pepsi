#!/usr/bin/env python3
import cv2
import numpy as np
import pyautogui
import time
import os
import logging
import argparse
import requests
from datetime import datetime

# Logging konfiguratsiyasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ScreenRecorder:
    def __init__(self, token, chat_id, duration=10, fps=15,
                 quality=95, area=None, audio=False):
        """
        Ekran yozib olish va Telegram'ga yuborish uchun sinf

        Args:
            token (str): Telegram bot tokeni
            chat_id (str): Telegram chat ID raqami
            duration (int): Yozib olish davomiyligi (sekundlarda)
            fps (int): Kadrlar chastotasi
            quality (int): Video sifati (0-100)
            area (tuple): Yozib olish maydoni (x, y, width, height) yoki None
            audio (bool): Audio yozib olish (hozircha ishlamaydi)
        """
        self.token = token
        self.chat_id = chat_id
        self.duration = duration
        self.fps = fps
        self.quality = quality
        self.area = area
        self.audio = audio

        # Video parametrlari
        self.video_params = {
            'preset': 'slow',
            'crf': str(28 - (quality * 0.28))  # CRF 0-28 oralig'ida
        }

        # Timestamp bilan video nomi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_name = f"screen_record_{timestamp}.mp4"

        # Agar area ko'rsatilmagan bo'lsa, butun ekranni olish
        if self.area is None:
            self.screen_width, self.screen_height = pyautogui.size()
            self.area = (0, 0, self.screen_width, self.screen_height)
        else:
            self.screen_width = self.area[2]
            self.screen_height = self.area[3]

        # Papka mavjudligini tekshirish
        os.makedirs("recordings", exist_ok=True)
        self.video_path = os.path.join("recordings", self.video_name)

    def record_screen(self):
        """Ekranni yozib olish"""
        try:
            # H.264 codec ishlatamiz
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(
                self.video_path,
                fourcc,
                self.fps,
                (self.screen_width, self.screen_height)
            )

            logger.info(f"📹 Ekran yozuvi boshlandi ({self.duration} sekund, {self.fps} FPS)")
            frames_total = self.duration * self.fps
            frames_recorded = 0

            start_time = time.time()
            next_frame_time = start_time

            while frames_recorded < frames_total:
                current_time = time.time()

                # Aniq FPS ni ta'minlash
                if current_time >= next_frame_time:
                    # Screenshot olish
                    img = pyautogui.screenshot(region=self.area)
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                    # Kadrni yozish
                    out.write(frame)
                    frames_recorded += 1
                    next_frame_time += 1.0 / self.fps

                    # Progress ko'rsatish
                    if frames_recorded % 50 == 0:
                        progress = min(100, int((frames_recorded / frames_total) * 100))
                        logger.info(f"⏱️ Yozilmoqda: {progress}% ({frames_recorded}/{frames_total} kadrlar)")

                time.sleep(0.001)

            out.release()
            actual_duration = time.time() - start_time
            file_size_mb = os.path.getsize(self.video_path) / (1024 * 1024)

            logger.info(f"✅ Video yozildi! Davomiyligi: {actual_duration:.2f} sekund, Hajmi: {file_size_mb:.2f} MB")
            return True
        except Exception as e:
            logger.error(f"❌ Xato yuz berdi: {str(e)}")
            return False

    def send_to_telegram(self):
        """Videoni Telegram'ga yuborish"""
        try:
            # Video davomiyligini tekshirish
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            cap.release()

            logger.info(f"📊 Video tahlili: {duration:.2f}s, {fps:.2f} FPS, {frame_count} kadrlar")

            if duration < self.duration * 0.8:  # 80% dan kam bo'lsa
                logger.warning(f"⚠️ Video davomiyligi kutilganidan qisqa: {duration:.2f}s (kutilgan {self.duration}s)")

            logger.info(f"📤 Telegram'ga yuborilmoqda...")

            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.token}/sendVideo"

            # Caption tayyorlash
            caption = (f"📹 Ekran yozuvi\n"
                       f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f"⏱️ Davomiyligi: {duration:.2f} sekund\n"
                       f"🖥 O'lcham: {self.screen_width}x{self.screen_height}")

            # Faylni yuklash uchun so'rov parametrlari
            params = {
                'chat_id': self.chat_id,
                'caption': caption,
                'supports_streaming': True
            }

            # Video faylini ochish
            with open(self.video_path, 'rb') as video_file:
                # Multipart/form-data so'rov yuborish
                files = {'video': video_file}
                response = requests.post(url, params=params, files=files)

            # So'rov natijasini tekshirish
            if response.status_code == 200 and response.json().get('ok'):
                logger.info("✅ Video muvaffaqiyatli yuborildi!")
                return True
            else:
                logger.error(f"❌ Telegram API xatosi: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Telegram'ga yuborishda xato: {str(e)}")
            return False

    def cleanup(self, keep_local=False):
        """Video faylini o'chirish"""
        if not keep_local and os.path.exists(self.video_path):
            os.remove(self.video_path)
            logger.info(f"🗑 Mahalliy video fayli o'chirildi: {self.video_path}")
        elif keep_local:
            logger.info(f"💾 Mahalliy video saqlandi: {self.video_path}")


def main():
    # CLI argumentlarini tahlil qilish
    parser = argparse.ArgumentParser(description="Ekranni yozib olish va Telegram'ga yuborish")
    parser.add_argument("--token", default="7942625455:AAEBbd3l8CNbtxS_gw608thJcoNoEcHLMU4", help="Telegram bot tokeni")
    parser.add_argument("--chat-id", default="6340507558", help="Telegram chat ID raqami")
    parser.add_argument("--duration", type=int, default=10, help="Yozib olish davomiyligi (sekundlada)")
    parser.add_argument("--fps", type=int, default=15, help="Kadrlar chastotasi")
    parser.add_argument("--quality", type=int, default=95, help="Video sifati (0-100)")
    parser.add_argument("--keep", action="store_true", help="Mahalliy videoni saqlab qolish")
    parser.add_argument("--area", nargs=4, type=int, help="Yozib olish maydoni (x y width height)")

    args = parser.parse_args()

    # Area argumentini formatlash
    area = None
    if args.area:
        area = tuple(args.area)

    # Screen recorder yaratish
    recorder = ScreenRecorder(
        token=args.token,
        chat_id=args.chat_id,
        duration=args.duration,
        fps=args.fps,
        quality=args.quality,
        area=area
    )

    # Ekranni yozib olish
    success = recorder.record_screen()

    if success:
        # Telegram'ga yuborish
        recorder.send_to_telegram()

    # Tozalash (mahalliy faylni o'chirish yoki saqlash)
    recorder.cleanup(keep_local=args.keep)


if __name__ == "__main__":
    print("=" * 50)
    print("📹 EKRAN YOZIB OLISH VA TELEGRAM'GA YUBORISH")
    print("=" * 50)

    # Asosiy funksiyani ishga tushirish
    main()
