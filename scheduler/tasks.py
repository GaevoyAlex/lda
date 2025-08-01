from datetime import datetime
from typing import List
from services.coingecko import CoingeckoAggregator


MAX_LOGS = 100


def log_task(name: str, log_list: List[str]):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_list.append(f"[{timestamp}] {name}")
    
    if len(log_list) > MAX_LOGS:
        del log_list[0]


def task_every_30_seconds(log_list: List[str]):
    log_task("Выполнена задача: Мгновенное обновление TokenStats (30 сек)", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        log_task("TokenStats успешно обновлены", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления TokenStats: {str(e)}", log_list)


def task_every_1_hour(log_list: List[str]):
    log_task("Выполнена задача: Обновление ExchangesStats (1 час)", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        log_task("ExchangesStats успешно обновлены", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления ExchangesStats: {str(e)}", log_list)


def task_every_24_hours(log_list: List[str]):
    log_task("Выполнена задача: Сбор детальной информации Tokens и Exchanges (24 часа)", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_tokens_detailed_info_daily(limit=500)
        aggregator.collect_exchanges_detailed_info_daily(limit=100)
        log_task("Детальная информация успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации: {str(e)}", log_list)


def task_initial_load(log_list: List[str]):
    log_task("Начальная загрузка данных", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        
        log_task("Загружаем TokenStats...", log_list)
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        
        log_task("Загружаем ExchangesStats...", log_list)
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        
        log_task("Начальная загрузка завершена", log_list)
    except Exception as e:
        log_task(f"Ошибка начальной загрузки: {str(e)}", log_list)


def manual_task_token_details(log_list: List[str]):
    log_task("Ручной запуск сбора детальной информации о токенах", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_tokens_detailed_info_daily(limit=500)
        log_task("Детальная информация о токенах успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации о токенах: {str(e)}", log_list)


def manual_task_exchange_details(log_list: List[str]):
    log_task("Ручной запуск сбора детальной информации о биржах", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.collect_exchanges_detailed_info_daily(limit=100)
        log_task("Детальная информация о биржах успешно собрана", log_list)
    except Exception as e:
        log_task(f"Ошибка сбора детальной информации о биржах: {str(e)}", log_list)


def manual_task_token_stats(log_list: List[str]):
    log_task("Ручной запуск обновления статистики токенов", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_tokens_stats_every_10_seconds(limit=500)
        log_task("Статистика токенов успешно обновлена", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления статистики токенов: {str(e)}", log_list)


def manual_task_exchange_stats(log_list: List[str]):
    log_task("Ручной запуск обновления статистики бирж", log_list)
    
    try:
        aggregator = CoingeckoAggregator(is_demo=False)
        aggregator.update_exchanges_stats_every_10_seconds(limit=100)
        log_task("Статистика бирж успешно обновлена", log_list)
    except Exception as e:
        log_task(f"Ошибка обновления статистики бирж: {str(e)}", log_list)