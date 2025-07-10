import requests
import os
from dotenv import load_dotenv
from avito_parsing import AvitoItem

load_dotenv()

class TelegramAlert:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f'https://api.telegram.org/bot{self.token}/sendMessage'
    
    def send_alert(self, item: AvitoItem):
        message = (
            f"🏷 *{item.title}*\n"
            f"💵 *Цена:* {item.price}\n"
            f"📍 *Местоположение:* {item.location}\n"
            f"📅 *Дата:* {item.date}\n"
            f"\n{item.description[:200]}...\n"
            f"[Ссылка на объявление]({item.url})"
        )
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        response = requests.post(self.base_url, data=payload)
        return response.json()