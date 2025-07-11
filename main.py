import time
import random
import logging
from avito_parsing import AvitoParser
from tg_alert import TelegramAlert
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log', encoding='utf-8'),
        logging.StreamHandler()  # Если нужно дублировать логи в консоль
    ]
)
logger = logging.getLogger(__name__)

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
        bot_working_alert_ts = time.time()
        while True:
            for parser in parsers:
                try:
                    logger.info(f"Начинаем парсинг URL: {parser.url}")
                    
                    # Парсим страницу
                    items = parser.parse_page()
                    
                    # Обработка пустого результата
                    if not items:
                        logger.warning("Объявления не найдены или не соответствуют фильтру города")
                        if time.time() - bot_working_alert_ts > 60*60*12:
                            bot_working_alert_ts = time.time()
                            alert.send_no_results_alert(parser.url)
                        #alert.send_no_results_alert(parser.url)
                        continue
                        
                    logger.info(f"Найдено {len(items)} объявлений (после фильтрации)")
                    
                    # Фильтруем новые объявления
                    new_items = [item for item in items if item.url not in parser.seen_items]
                    
                    if not new_items:
                        logger.info("Новых объявлений не обнаружено")
                        continue
                        
                    logger.info(f"Найдено {len(new_items)} новых объявлений")
                    
                    # Отправляем уведомления
                    for i, item in enumerate(new_items, 1):
                        try:
                            logger.info(f"Отправляем: {item.title[:50]}... (Цена: {item.price})")
                            alert.send_alert(item)
                        except Exception as e:
                            logger.error(f"Ошибка отправки объявления: {str(e)[:100]}...")
                
                except Exception as e:
                    logger.error(f"Критическая ошибка при обработке URL {parser.url}: {str(e)[:200]}...")
                    continue
            
            # Случайная пауза между проверками
            sleep_time = random.randint(60, 600)
            mins = sleep_time // 60
            logger.info(f"Следующая проверка через {mins} минут ({sleep_time} секунд)")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Парсер остановлен по запросу пользователя")
    except Exception as e:
        logger.critical(f"Неожиданная ошибка в основном цикле: {e}")
    finally:
        logger.info("Завершаем работу...")
        for parser in parsers:
            try:
                parser.close()
                logger.info(f"Закрыт парсер для {parser.url}")
            except Exception as e:
                logger.error(f"Ошибка при закрытии парсера: {e}")
        logger.info("Работа завершена")

if __name__ == "__main__":
    main()