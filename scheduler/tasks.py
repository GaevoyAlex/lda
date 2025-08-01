from datetime import datetime
from services.coingecko import CoingeckoAggregator

def log_task(name, log_list):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_list.append(f"[{timestamp}] Выполнена задача: {name}")
    
    if len(log_list) > 100:
        del log_list[0]

def task_every_30_seconds(log_list):
    log_task("Мгновенное обновление TokenStats (30 сек)", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        # Исправлено: используем правильный метод
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        log_task("TokenStats успешно обновлены", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления TokenStats: {str(e)}", log_list)

def task_every_1_hour(log_list):
    log_task("Обновление ExchangesStats (1 час)", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        # Исправлено: используем правильный метод
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        log_task("ExchangesStats успешно обновлены", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления ExchangesStats: {str(e)}", log_list)

def task_every_24_hours(log_list):
    log_task("Сбор детальной информации Tokens и Exchanges (24 часа)", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_tokens_detailed_info_daily(limit=500)
        aggregator.collect_exchanges_detailed_info_daily(limit=100)
        log_task("Детальная информация успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации: {str(e)}", log_list)

def task_initial_load(log_list):
    log_task("Начальная загрузка данных", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        log_task("Загружаем TokenStats...", log_list)
        # Исправлено: используем правильные методы
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        log_task("Загружаем ExchangesStats...", log_list)
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        log_task("Начальная загрузка завершена", log_list)
    except Exception as e:
        log_task(f"Ошибка начальной загрузки: {str(e)}", log_list)

# Добавляем недостающую функцию
def manual_task_token_details(log_list):
    """Ручная задача для сбора детальной информации о токенах"""
    log_task("Ручной запуск сбора детальной информации о токенах", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_tokens_detailed_info_daily(limit=500)
        log_task("Детальная информация о токенах успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации о токенах: {str(e)}", log_list)

# Также добавим функции для ручного запуска других задач
def manual_task_exchange_details(log_list):
    """Ручная задача для сбора детальной информации о биржах"""
    log_task("Ручной запуск сбора детальной информации о биржах", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_exchanges_detailed_info_daily(limit=100)
        log_task("Детальная информация о биржах успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации о биржах: {str(e)}", log_list)

def manual_task_token_stats(log_list):
    """Ручная задача для обновления статистики токенов"""
    log_task("Ручной запуск обновления статистики токенов", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        log_task("Статистика токенов успешно обновлена", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления статистики токенов: {str(e)}", log_list)

def manual_task_exchange_stats(log_list):
    """Ручная задача для обновления статистики бирж"""
    log_task("Ручной запуск обновления статистики бирж", log_list)
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        log_task("Статистика бирж успешно обновлена", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления статистики бирж: {str(e)}", log_list)