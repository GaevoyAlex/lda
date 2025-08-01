import schedule
import threading
import time

class TaskScheduler:
    def __init__(self, log_list):
        self.thread = None
        self.stop_flag = False
        self.log_list = log_list
        self.initial_load_done = False

    def start(self, interval_tokens_seconds=30, interval_exchanges_hours=1, interval_details_hours=24):
        self.stop_flag = False
        schedule.clear()
        
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.append(f"[{timestamp}] Запуск планировщика...")
        
        if not self.initial_load_done:
            try:
                from scheduler.tasks import task_initial_load
                task_initial_load(self.log_list)
                self.initial_load_done = True
            except Exception as e:
                self.log_list.append(f"[{timestamp}] Ошибка начальной загрузки: {str(e)}")

        schedule.every(interval_tokens_seconds).seconds.do(self.task_wrapper, "tokens")
        schedule.every(interval_exchanges_hours).hours.do(self.task_wrapper, "exchanges") 
        schedule.every(interval_details_hours).hours.do(self.task_wrapper, "details")

        self.log_list.append(f"[{timestamp}] Планировщик настроен: Токены каждые {interval_tokens_seconds}с, Биржи каждые {interval_exchanges_hours}ч")

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop_flag:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.log_list.append(f"[{timestamp}] Ошибка в планировщике: {str(e)}")

    def stop(self):
        self.stop_flag = True
        schedule.clear()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.append(f"[{timestamp}] Планировщик остановлен")

    def task_wrapper(self, task_type):
        try:
            if task_type == "tokens":
                from scheduler.tasks import task_every_30_seconds
                task_every_30_seconds(self.log_list)
            elif task_type == "exchanges":
                from scheduler.tasks import task_every_1_hour
                task_every_1_hour(self.log_list)
            elif task_type == "details":
                from scheduler.tasks import task_every_24_hours
                task_every_24_hours(self.log_list)
        except Exception as e:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_list.append(f"[{timestamp}] Ошибка выполнения задачи {task_type}: {str(e)}")