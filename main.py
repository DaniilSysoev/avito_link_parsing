import time
import random
from avito_parsing import AvitoParser
from tg_alert import TelegramAlert
from dotenv import load_dotenv

load_dotenv()

# Ссылки для парсинга
SEARCH_URLS = [
    "https://www.avito.ru/sankt-peterburg/telefony/mobilnye_telefony/vivo/x200_pro_mini-ASgBAgICA0SywA34gZEVtMANzqk5sMENiPw3?context=H4sIAAAAAAAA_wFfAKD_YToyOntzOjg6ImZyb21QYWdlIjtzOjc6InN1Z2dlc3QiO3M6NToieF9zZ3QiO3M6NDA6IjkzYmIzZGE5OGI5NWViOGY2YjczOTlhZmVlNDc1YTg0YmE1NzUyYTEiO30IkA1gXwAAAA&f=ASgBAgECA0SywA34gZEVtMANzqk5sMENiPw3AUXGmgwVeyJmcm9tIjowLCJ0byI6NDYwMDB9&geoCoords=59.939095%2C30.315868&moreExpensive=0&presentationType=serp&s=104",
    "https://www.avito.ru/sankt-peterburg?cd=1&f=ASgCAgECAUXGmgwZeyJmcm9tIjoxOTAwMCwidG8iOjI2MDAwfQ&q=ray+ban+meta"
]

def main():
    alert = TelegramAlert()
    parsers = [AvitoParser(url) for url in SEARCH_URLS]
    
    try:
        while True:
            for parser in parsers:
                try:
                    new_items = parser.get_new_items()
                    for item in new_items:
                        print(f"Найдено новое объявление: {item.title}")
                        alert.send_alert(item)
                        #time.sleep(1)  # Пауза между отправками
                except Exception as e:
                    print(f"Ошибка при парсинге: {e}")
            
            # Случайная пауза от 1 до 10 минут
            sleep_time = random.randint(60, 600)
            print(f"Следующая проверка через {sleep_time//60} минут")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("Остановка парсера...")
    finally:
        for parser in parsers:
            parser.close()

if __name__ == "__main__":
    main()