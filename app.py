"""
app.py - главный файл приложения «Анти-Похмелье»
Запуск: streamlit run app.py
"""

import streamlit as st
from chatbot_logic import AntiHangoverBot

# ------------------------------------------------------------------
# Настройки страницы
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Анти-Похмелье",
    page_icon="🍺",
    layout="centered",
)

# ------------------------------------------------------------------
# CSS стили
# ------------------------------------------------------------------
st.markdown("""
<style>
    .main-header { text-align: center; padding: 10px 0 5px 0; }

    .severity-block {
        padding: 14px 18px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: 600;
        font-size: 1.05em;
    }
    .severity-light  { background: #d4edda; color: #155724; border-left: 5px solid #28a745; }
    .severity-medium { background: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }
    .severity-heavy  { background: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }

    .quick-btn-label {
        text-align: center;
        color: #888;
        font-size: 0.8em;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Заголовок
# ------------------------------------------------------------------
st.markdown(
    "<div class='main-header'>"
    "<h2>🍺 Анти-Похмелье</h2>"
    "<p style='color:#888;font-size:0.9em;'>Чат-бот на основе NLP и RAG-системы</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Инициализация
# ------------------------------------------------------------------
if "bot" not in st.session_state:
    with st.spinner("⏳ Загрузка модели и базы знаний..."):
        st.session_state.bot = AntiHangoverBot()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Привет! 👋 Я бот «Анти-Похмелье».\n\n"
            "Помогу облегчить похмелье, расскажу как подготовиться к застолью, "
            "подберу тост или поделюсь интересным фактом.\n\n"
            "Нажми кнопку или напиши что тебя интересует! 👇"
        ),
    })

for key, default in [
    ("diagnosis_mode", False),
    ("diagnosis_step", 0),
    ("user_profile", {}),
    ("quick_action", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------------------------------------------------------
# Прогресс-бар диагностики
# ------------------------------------------------------------------
if st.session_state.diagnosis_mode:
    total = 8
    current = st.session_state.diagnosis_step + 1
    st.markdown(
        f"<div style='background:#1e1e2e;border-radius:8px;padding:8px 14px;"
        f"font-size:0.82em;color:#a0a0b0;margin-bottom:6px;'>"
        f"🩺 Диагностика: вопрос {current} из {total}</div>",
        unsafe_allow_html=True,
    )
    st.progress(current / total)

# ------------------------------------------------------------------
# История сообщений
# ------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------------
# Быстрые кнопки (показываем только когда не идёт диагностика)
# ------------------------------------------------------------------
if not st.session_state.diagnosis_mode:
    st.markdown("<div class='quick-btn-label'>Быстрые действия:</div>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("😵\nМне плохо", use_container_width=True):
            st.session_state.quick_action = "мне плохо"
    with col2:
        if st.button("🥂\nЗастолье", use_container_width=True):
            st.session_state.quick_action = "как подготовиться к застолью"
    with col3:
        if st.button("📜\nТост", use_container_width=True):
            st.session_state.quick_action = "скажи тост"
    with col4:
        if st.button("💡\nФакт", use_container_width=True):
            st.session_state.quick_action = "интересный факт про алкоголь"
    with col5:
        if st.button("🔄\nСброс", use_container_width=True):
            for key in ["messages", "diagnosis_mode", "diagnosis_step", "user_profile", "quick_action"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ------------------------------------------------------------------
# Обработка быстрого действия от кнопки
# ------------------------------------------------------------------
if st.session_state.quick_action:
    action = st.session_state.quick_action
    st.session_state.quick_action = None

    st.session_state.messages.append({"role": "user", "content": action})

    with st.chat_message("user"):
        st.markdown(action)

    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            result = st.session_state.bot.respond(
                action,
                st.session_state.diagnosis_mode,
                st.session_state.diagnosis_step,
                st.session_state.user_profile,
            )

        st.session_state.diagnosis_mode = result["diagnosis_mode"]
        st.session_state.diagnosis_step = result["diagnosis_step"]
        st.session_state.user_profile = result["user_profile"]

        st.markdown(result["text"])
        st.session_state.messages.append({"role": "assistant", "content": result["text"]})

    st.rerun()

# ------------------------------------------------------------------
# Поле ввода
# ------------------------------------------------------------------
placeholder = (
    f"Вопрос {st.session_state.diagnosis_step + 1} из 8..."
    if st.session_state.diagnosis_mode
    else "Напишите сообщение..."
)

if prompt := st.chat_input(placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            result = st.session_state.bot.respond(
                prompt,
                st.session_state.diagnosis_mode,
                st.session_state.diagnosis_step,
                st.session_state.user_profile,
            )

        st.session_state.diagnosis_mode = result["diagnosis_mode"]
        st.session_state.diagnosis_step = result["diagnosis_step"]
        st.session_state.user_profile = result["user_profile"]

        # Визуальная шкала тяжести если это результат диагностики
        text = result["text"]
        if "ЛЁГКОЕ" in text:
            st.markdown(
                "<div class='severity-block severity-light'>"
                "🟢 Степень похмелья: ЛЁГКОЕ - справишься быстро!</div>",
                unsafe_allow_html=True,
            )
        elif "СРЕДНЕЕ" in text:
            st.markdown(
                "<div class='severity-block severity-medium'>"
                "🟡 Степень похмелья: СРЕДНЕЕ - нужны активные меры.</div>",
                unsafe_allow_html=True,
            )
        elif "ТЯЖЁЛОЕ" in text:
            st.markdown(
                "<div class='severity-block severity-heavy'>"
                "🔴 Степень похмелья: ТЯЖЁЛОЕ - полный покой и лечение!</div>",
                unsafe_allow_html=True,
            )

        st.markdown(text)
        st.session_state.messages.append({"role": "assistant", "content": text})

    st.rerun()
