import streamlit as st
import threading
import time
from scheduler.scheduler import TaskScheduler

st.title("Управление состоянием")

# Инициализация состояния
if "logs" not in st.session_state:
    st.session_state.logs = []

if "scheduler" not in st.session_state:
    st.session_state.scheduler = TaskScheduler(st.session_state.logs)

if "task_running" not in st.session_state:
    st.session_state.task_running = False

st.title("📆 Планировщик сбора данных CoinGecko")

# Автоматический планировщик
with st.form("config_form"):
    st.subheader("⚙️ Настройка автоматических интервалов")

    col1, col2, col3 = st.columns(3)
    with col1:
        interval_tokens = st.number_input("TokenStats обновление (сек)", value=30, min_value=10, max_value=300)
    with col2:
        interval_exchanges = st.number_input("ExchangesStats обновление (часы)", value=1, min_value=1, max_value=24)
    with col3:
        interval_details = st.number_input("Детальная информация (часы)", value=24, min_value=1, max_value=48)

    submitted = st.form_submit_button("🔁 Запустить/Перезапустить")

    if submitted:
        st.session_state.scheduler.stop()
        st.session_state.scheduler = TaskScheduler(st.session_state.logs)
        st.session_state.scheduler.start(interval_tokens, interval_exchanges, interval_details)
        st.success(f"Планировщик запущен! TokenStats: {interval_tokens}с, Exchanges: {interval_exchanges}ч, Details: {interval_details}ч")

col1, col2 = st.columns(2)
with col1:
    if st.button("⏹️ Остановить планировщик"):
        st.session_state.scheduler.stop()
        st.warning("Планировщик остановлен")
        
with col2:
    if st.button("🔄 Обновить логи"):
        st.rerun()

st.divider()

# Ручное управление задачами
st.subheader("🎯 Ручное выполнение задач")

def run_manual_task(task_func, task_name, logs_list):
    """Запуск ручной задачи в отдельном потоке"""
    def run_task():
        try:
            # Добавляем начальное сообщение
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logs_list.append(f"[{timestamp}] Запуск ручной задачи: {task_name}")
            
            # Выполняем задачу
            task_func(logs_list)
            
            # Добавляем сообщение об успешном завершении
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logs_list.append(f"[{timestamp}] Ручная задача завершена: {task_name}")
            
        except Exception as e:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logs_list.append(f"[{timestamp}] [ERROR] {task_name}: {str(e)}")
        finally:
            # Сбрасываем флаг выполнения задачи
            st.session_state.task_running = False
    
    if not st.session_state.task_running:
        st.session_state.task_running = True
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        st.success(f"Запущена задача: {task_name}")
        # Автоматически обновляем через 2 секунды
        time.sleep(2)
        st.rerun()
    else:
        st.warning("Подождите, пока завершится текущая задача...")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 TokenStats", disabled=st.session_state.task_running):
        from scheduler.tasks import manual_task_token_stats
        run_manual_task(manual_task_token_stats, "Обновление TokenStats", st.session_state.logs)

with col2:
    if st.button("🏢 ExchangesStats", disabled=st.session_state.task_running):
        from scheduler.tasks import manual_task_exchange_stats
        run_manual_task(manual_task_exchange_stats, "Обновление ExchangesStats", st.session_state.logs)

with col3:
    if st.button("🔍 Детали токенов", disabled=st.session_state.task_running):
        from scheduler.tasks import manual_task_token_details
        run_manual_task(manual_task_token_details, "Детальная информация токенов", st.session_state.logs)

with col4:
    if st.button("🏛️ Детали бирж", disabled=st.session_state.task_running):
        from scheduler.tasks import manual_task_exchange_details
        run_manual_task(manual_task_exchange_details, "Детальная информация бирж", st.session_state.logs)

# Показать статус выполнения
if st.session_state.task_running:
    st.info("⏳ Выполняется ручная задача...")

st.divider()

st.subheader("📈 Текущие настройки")
st.info("""
🚀 **TokenStats**: Мгновенное обновление каждые 30 секунд (500 токенов)
📊 **ExchangesStats**: Обновление каждый час (100 бирж)  
📋 **Детальная информация**: Обновление раз в 24 часа

💡 **Ручные задачи**: Кнопки выше позволяют запустить любую задачу немедленно
""")

st.divider()

st.subheader("📜 Логи задач")

col1, col2 = st.columns([4, 1])
with col1:
    st.text_area("Последние события", value="\n".join(st.session_state.logs[-30:]), height=400, key="logs_display")

with col2:
    st.write("**Управление:**")
    if st.button("🗑️ Очистить логи"):
        st.session_state.logs.clear()
        st.rerun()
    
    if st.button("💾 Экспорт логов"):
        logs_text = "\n".join(st.session_state.logs)
        st.download_button(
            label="📄 Скачать логи",
            data=logs_text,
            file_name=f"coingecko_logs_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

st.empty()
time.sleep(0.1) 