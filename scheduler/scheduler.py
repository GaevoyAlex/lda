import schedule
import threading
import time
from typing import List


class TaskScheduler:
    def __init__(self, log_list: List[str]):
        self.thread = None
        self.stop_flag = False
        self.log_list = log_list
        self.initial_load_done = False

    def start(self, interval_tokens_seconds: int = 30, 
              interval_exchanges_hours: int = 1, 
              interval_details_hours: int = 24):
        self._reset_scheduler()
        self._log_startup(interval_tokens_seconds, interval_exchanges_hours, interval_details_hours)
        
        if not self.initial_load_done:
            self._run_initial_load()
        
        self._schedule_tasks(interval_tokens_seconds, interval_exchanges_hours, interval_details_hours)
        self._start_thread()

    def _reset_scheduler(self):
        self.stop_flag = False
        schedule.clear()

    def _log_startup(self, tokens_interval: int, exchanges_interval: int, details_interval: int):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.append(f"[{timestamp}] Запуск планировщика...")
        self.log_list.append(
            f"[{timestamp}] Планировщик настроен: "
            f"Токены каждые {tokens_interval}с, Биржи каждые {exchanges_interval}ч"
        )

    def _run_initial_load(self):
        try:
            from scheduler.tasks import task_initial_load
            task_initial_load(self.log_list)
            self.initial_load_done = True
        except Exception as e:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_list.append(f"[{timestamp}] Ошибка начальной загрузки: {str(e)}")

    def _schedule_tasks(self, tokens_interval: int, exchanges_interval: int, details_interval: int):
        schedule.every(tokens_interval).seconds.do(self.task_wrapper, "tokens")
        schedule.every(exchanges_interval).hours.do(self.task_wrapper, "exchanges") 
        schedule.every(details_interval).hours.do(self.task_wrapper, "details")

    def _start_thread(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop_flag:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self._log_error(f"Ошибка в планировщике: {str(e)}")

    def stop(self):
        self.stop_flag = True
        schedule.clear()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.append(f"[{timestamp}] Планировщик остановлен")

    def task_wrapper(self, task_type: str):
        try:
            task_map = {
                "tokens": self._run_tokens_task,
                "exchanges": self._run_exchanges_task,
                "details": self._run_details_task
            }
            
            task_func = task_map.get(task_type)
            if task_func:
                task_func()
        except Exception as e:
            self._log_error(f"Ошибка выполнения задачи {task_type}: {str(e)}")

    def _run_tokens_task(self):
        from scheduler.tasks import task_every_30_seconds
        task_every_30_seconds(self.log_list)

    def _run_exchanges_task(self):
        from scheduler.tasks import task_every_1_hour
        task_every_1_hour(self.log_list)

    def _run_details_task(self):
        from scheduler.tasks import task_every_24_hours
        task_every_24_hours(self.log_list)

    def _log_error(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.append(f"[{timestamp}] {message}")