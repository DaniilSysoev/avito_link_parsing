import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

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
        self.driver = self._init_driver()
        self.seen_items = self.load_seen_items()

    def _init_driver(self):
        options = uc.ChromeOptions()
        
        # Настройки для Linux сервера
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--headless=new')
        
        # Настройки для обхода защиты
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        
        # Указываем явный путь к Chrome
        options.binary_location = '/usr/bin/chromium-browser'
        
        driver = uc.Chrome(
            options=options,
            version_main=114,  # Укажите вашу версию Chrome
            driver_executable_path='/usr/bin/chromedriver'
        )
        return driver

    def load_seen_items(self) -> dict[str, AvitoItem]:
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['url']: AvitoItem(**item) for item in data}
        return {}

    def save_seen_items(self):
        """Сохраняет данные в файл, создавая резервную копию при ошибках"""
        try:
            # Создаем временный файл для безопасной записи
            temp_file = self.data_file + '.tmp'
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                items = [asdict(item) for item in self.seen_items.values()]
                json.dump(items, f, ensure_ascii=False, indent=2)
            
            # Заменяем старый файл новым
            os.replace(temp_file, self.data_file)
            print(f"Данные успешно сохранены в {self.data_file}")
            
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
            # Создаем резервную копию поврежденного файла
            if os.path.exists(self.data_file):
                backup_name = f"{self.data_file}.backup_{int(time.time())}"
                os.rename(self.data_file, backup_name)
                print(f"Создана резервная копия: {backup_name}")

    def parse_page(self) -> List[AvitoItem]:
        self.driver.get(self.url)
        time.sleep(5)
        
        items = []
        
        # Проверяем наличие сообщения "Ничего не найдено"
        try:
            no_results = self.driver.find_element(
                By.CSS_SELECTOR, 'h2.no-results-title-f6Tng'
            )
            if "Ничего не найдено" in no_results.text:
                print("Нет товаров в выбранной области поиска")
                return []
        except NoSuchElementException:
            pass
        
        # Проверяем наличие блока с объявлениями из других городов
        try:
            other_cities_block = self.driver.find_element(
                By.CSS_SELECTOR, 'div.items-extraTitle-en7fx h2.styles-module-root-KWbDd'
            )
            if "объявлений есть в других городах" in other_cities_block.text:
                print(f"Найдено сообщение: {other_cities_block.text.strip()}")
        except NoSuchElementException:
            pass
        
        # Парсим только объявления до блока с другими городами
        cards = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
        
        for card in cards:
            try:
                # Проверяем, не является ли карточка частью блока других городов
                try:
                    card.find_element(By.XPATH, './/ancestor::div[contains(@class, "items-extraContent-duy3l")]')
                    continue  # Пропускаем объявления из других городов
                except NoSuchElementException:
                    pass
                
                # Парсинг данных объявления
                title = "Без названия"
                price = "Цена не указана"
                url = "Ссылка недоступна"
                description = "Описание не указано"
                location = "Местоположение не указано"
                date = "Дата не указана"
                
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, '[itemprop="name"], h3, h2')
                    title = title_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                try:
                    price_elem = card.find_element(By.CSS_SELECTOR, '[itemprop="price"], [data-marker="item-price"]')
                    price_content = price_elem.get_attribute('content')
                    price = f"{price_content} ₽" if price_content else price_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, 'a[data-marker="item-title"]')
                    href = link_elem.get_attribute('href')
                    if href:
                        url = f"https://www.avito.ru{href}" if not href.startswith('http') else href
                except NoSuchElementException:
                    pass
                
                try:
                    description_elem = card.find_element(
                        By.CSS_SELECTOR, 'p.styles-module-root-PYlie, .iva-item-descriptionStep-Qp8li, [data-marker="item-description"]'
                    )
                    description = description_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                try:
                    location_elem = card.find_element(
                        By.CSS_SELECTOR, '[data-marker="item-address"], .iva-item-geo-OW9Hc, [class*="geo-"]'
                    )
                    location = location_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                try:
                    date_elem = card.find_element(
                        By.CSS_SELECTOR, '[data-marker="item-date"], .iva-item-dateInfoStep-AoWrh, [class*="date-"]'
                    )
                    date = date_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                items.append(AvitoItem(
                    title=title,
                    price=price,
                    url=url,
                    description=description,
                    location=location,
                    date=date
                ))
                
            except Exception as e:
                print(f"Ошибка парсинга карточки: {str(e)[:100]}...")
                continue
        
        print(f"Найдено {len(items)} объявлений в текущем городе")
        return items

    def get_new_items(self) -> List[AvitoItem]:
        current_items = self.parse_page()
        new_items = []
        
        for item in current_items:
            if item.url not in self.seen_items:
                self.seen_items[item.url] = item
                new_items.append(item)
        
        # Всегда сохраняем данные, даже если новых объявлений нет
        self.save_seen_items()
        
        return new_items

    def close(self):
        self.driver.quit()