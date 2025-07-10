import time
import random
from avito_parsing import AvitoParser
from tg_alert import TelegramAlert
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Ссылки для парсинга
SEARCH_URLS = [
    "https://www.avito.ru/sankt-peterburg/telefony/mobilnye_telefony/vivo/x200_pro_mini-ASgBAgICA0SywA34gZEVtMANzqk5sMENiPw3?context=H4sIAAAAAAAA_wFfAKD_YToyOntzOjg6ImZyb21QYWdlIjtzOjc6InN1Z2dlc3QiO3M6NToieF9zZ3QiO3M6NDA6IjkzYmIzZGE5OGI5NWViOGY2YjczOTlhZmVlNDc1YTg0YmE1NzUyYTEiO30IkA1gXwAAAA&f=ASgBAgECA0SywA34gZEVtMANzqk5sMENiPw3AUXGmgwVeyJmcm9tIjowLCJ0byI6NDYwMDB9&geoCoords=59.939095%2C30.315868&moreExpensive=0&presentationType=serp&s=104",
    "https://www.avito.ru/sankt-peterburg?cd=1&f=ASgCAgECAUXGmgwZeyJmcm9tIjoxOTAwMCwidG8iOjI2MDAwfQ&q=ray+ban+meta"
]

def main():
    if not os.path.exists('parsed_data.json'):
        with open('parsed_data.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

    alert = TelegramAlert()
    parsers = [AvitoParser(url) for url in SEARCH_URLS]
    try:
        while True:
            for parser in parsers:
                try:
                    print(f"\nНачинаем парсинг URL: {parser.url}")
                    
                    # Парсим страницу
                    items = parser.parse_page()
                    
                    # Обработка пустого результата
                    if not items:
                        print("⚠️ Объявления не найдены или не соответствуют фильтру города")
                        alert.send_no_results_alert(parser.url)
                        continue
                        
                    print(f"🔍 Найдено {len(items)} объявлений (после фильтрации)")
                    
                    # Фильтруем новые объявления
                    new_items = [item for item in items if item.url not in parser.seen_items]
                    
                    if not new_items:
                        print("ℹ️ Новых объявлений не обнаружено")
                        continue
                        
                    print(f"✨ Найдено {len(new_items)} новых объявлений")
                    
                    # Отправляем уведомления
                    for i, item in enumerate(new_items, 1):
                        try:
                            print(f"  {i}. Отправляем: {item.title[:50]}... (Цена: {item.price})")
                            alert.send_alert(item)
                        except Exception as e:
                            print(f"    ⚠️ Ошибка отправки объявления: {str(e)[:100]}...")
                
                except Exception as e:
                    print(f"🔥 Критическая ошибка при обработке URL {parser.url}: {str(e)[:200]}...")
                    continue
            
            # Случайная пауза между проверками
            sleep_time = random.randint(60, 600)
            mins = sleep_time // 60
            print(f"\n⏳ Следующая проверка через {mins} минут ({sleep_time} секунд)")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\n🛑 Парсер остановлен по запросу пользователя")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка в основном цикле: {e}")
    finally:
        print("\n🧹 Завершаем работу...")
        for parser in parsers:
            try:
                parser.close()
                print(f"Закрыт парсер для {parser.url}")
            except Exception as e:
                print(f"Ошибка при закрытии парсера: {e}")
        print("Работа завершена")

if __name__ == "__main__":
    main()