import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict

from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

@dataclass
class AvitoItem:
    title: str
    price: str
    url: str
    description: str
    location: str
    date: str

class AvitoParser:
    def __init__(self, url: str, data_file: str = 'parsed_data.json'):
        self.url = url
        self.data_file = data_file
        self.driver = uc.Chrome(headless=True, version_main=114)
        self.seen_items = self.load_seen_items()

    def load_seen_items(self) -> dict[str, AvitoItem]:
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['url']: AvitoItem(**item) for item in data}
        return {}

    def save_seen_items(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            items = [asdict(item) for item in self.seen_items.values()]
            json.dump(items, f, ensure_ascii=False, indent=2)

    def parse_page(self) -> List[AvitoItem]:
        self.driver.get(self.url)
        time.sleep(5)  # Ожидание загрузки страницы
        
        items = []
        cards = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
        
        for card in cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, 'h3[itemprop="name"]')
                title = title_elem.text.strip()
                
                price_elem = card.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]')
                price = price_elem.get_attribute('content') + ' ₽'
                
                url_elem = card.find_element(By.CSS_SELECTOR, 'a[data-marker="item-title"]')
                url = 'https://www.avito.ru' + url_elem.get_attribute('href')
                
                description = card.find_element(By.CSS_SELECTOR, 'div[class*="item-description"]').text.strip()
                
                location = card.find_element(By.CSS_SELECTOR, 'div[data-marker="item-address"]').text.strip()
                
                date = card.find_element(By.CSS_SELECTOR, 'div[data-marker="item-date"]').text.strip()
                
                item = AvitoItem(
                    title=title,
                    price=price,
                    url=url,
                    description=description,
                    location=location,
                    date=date
                )
                items.append(item)
            except Exception as e:
                print(f"Ошибка парсинга карточки: {e}")
                continue
        
        return items

    def get_new_items(self) -> List[AvitoItem]:
        current_items = self.parse_page()
        new_items = []
        
        for item in current_items:
            if item.url not in self.seen_items:
                self.seen_items[item.url] = item
                new_items.append(item)
        
        if new_items:
            self.save_seen_items()
        
        return new_items

    def close(self):
        self.driver.quit()