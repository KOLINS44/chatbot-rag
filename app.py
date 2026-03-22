"""
app.py - главный файл приложения «Анти-Похмелье»
Запуск: streamlit run app.py
"""

import streamlit as st
from chatbot_logic import AntiHangoverBot, TOAST_CATEGORIES

st.set_page_config(page_title="Анти-Похмелье", page_icon="🍺", layout="centered")

st.markdown("""
<style>
    .main-header { text-align: center; padding: 10px 0 5px 0; }
    .severity-block { padding: 14px 18px; border-radius: 10px; margin: 10px 0; font-weight: 600; font-size: 1.05em; }
    .severity-light  { background: #d4edda; color: #155724; border-left: 5px solid #28a745; }
    .severity-medium { background: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }
    .severity-heavy  { background: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }
    .quick-btn-label { text-align: center; color: #888; font-size: 0.8em; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='main-header'><h2>🍺 Анти-Похмелье</h2>"
    "<p style='color:#888;font-size:0.9em;'>Чат-бот на основе NLP и RAG-системы</p></div>",
    unsafe_allow_html=True,
)

@st.cache_resource
def load_bot():
    return AntiHangoverBot()

if "bot" not in st.session_state:
    with st.spinner("⏳ Загрузка модели и базы знаний..."):
        st.session_state.bot = load_bot()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Привет! 👋 Я бот «Анти-Похмелье».\n\n"
            "Помогу облегчить похмелье, расскажу как подготовиться к застолью, "
            "подберу тост или поделюсь фактом.\n\n"
            "Нажми кнопку или напиши что тебя интересует! 👇"
        ),
    })

for key, default in [
    ("diagnosis_mode", False),
    ("diagnosis_step", 0),
    ("user_profile", {}),
    ("quick_action", None),
    ("toast_mode", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Кнопки ---
if not st.session_state.diagnosis_mode:

    # Меню тостов
    if st.session_state.toast_mode:
        st.markdown("<div class='quick-btn-label'>Выбери повод:</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        keys = list(TOAST_CATEGORIES.keys())
        for i, key in enumerate(keys):
            label, _ = TOAST_CATEGORIES[key]
            with cols[i % 3]:
                if st.button(label, use_container_width=True, key=f"toast_{key}"):
                    st.session_state.quick_action = f"__toast__{key}"
                    st.session_state.toast_mode = False

        st.markdown("<div class='quick-btn-label'></div>", unsafe_allow_html=True)
        if st.button("← Назад", use_container_width=False):
            st.session_state.toast_mode = False
            st.rerun()

    else:
        # Основные кнопки
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
                st.session_state.toast_mode = True
                st.rerun()
        with col4:
            if st.button("💡\nФакт", use_container_width=True):
                st.session_state.quick_action = "интересный факт про алкоголь"
        with col5:
            if st.button("🔄\nСброс", use_container_width=True):
                for key in ["messages", "diagnosis_mode", "diagnosis_step",
                            "user_profile", "quick_action", "toast_mode"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

# --- Обработка действий ---
if st.session_state.quick_action:
    action = st.session_state.quick_action
    st.session_state.quick_action = None

    is_toast_select = action.startswith("__toast__")
    toast_key = action.replace("__toast__", "") if is_toast_select else None

    display_text = TOAST_CATEGORIES[toast_key][0] if is_toast_select else action
    st.session_state.messages.append({"role": "user", "content": display_text})

    with st.chat_message("user"):
        st.markdown(display_text)

    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            if is_toast_select:
                result = st.session_state.bot.respond(
                    toast_key, False, 0, {}, toast_mode=True
                )
            else:
                result = st.session_state.bot.respond(
                    action,
                    st.session_state.diagnosis_mode,
                    st.session_state.diagnosis_step,
                    st.session_state.user_profile,
                )

        st.session_state.diagnosis_mode = result["diagnosis_mode"]
        st.session_state.diagnosis_step = result["diagnosis_step"]
        st.session_state.user_profile = result["user_profile"]

        if result.get("toast_menu"):
            st.session_state.toast_mode = True

        text = result["text"]
        if "ЛЁГКОЕ" in text:
            st.markdown("<div class='severity-block severity-light'>🟢 Степень похмелья: ЛЁГКОЕ</div>", unsafe_allow_html=True)
        elif "СРЕДНЕЕ" in text:
            st.markdown("<div class='severity-block severity-medium'>🟡 Степень похмелья: СРЕДНЕЕ</div>", unsafe_allow_html=True)
        elif "ТЯЖЁЛОЕ" in text:
            st.markdown("<div class='severity-block severity-heavy'>🔴 Степень похмелья: ТЯЖЁЛОЕ</div>", unsafe_allow_html=True)

        st.markdown(text)
        st.session_state.messages.append({"role": "assistant", "content": text})

    st.rerun()

# --- Поле ввода ---
placeholder = (
    f"Вопрос {st.session_state.diagnosis_step + 1} из 8..."
    if st.session_state.diagnosis_mode else "Напишите сообщение..."
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

        if result.get("toast_menu"):
            st.session_state.toast_mode = True

        text = result["text"]
        if "ЛЁГКОЕ" in text:
            st.markdown("<div class='severity-block severity-light'>🟢 Степень похмелья: ЛЁГКОЕ</div>", unsafe_allow_html=True)
        elif "СРЕДНЕЕ" in text:
            st.markdown("<div class='severity-block severity-medium'>🟡 Степень похмелья: СРЕДНЕЕ</div>", unsafe_allow_html=True)
        elif "ТЯЖЁЛОЕ" in text:
            st.markdown("<div class='severity-block severity-heavy'>🔴 Степень похмелья: ТЯЖЁЛОЕ</div>", unsafe_allow_html=True)

        st.markdown(text)
        st.session_state.messages.append({"role": "assistant", "content": text})

    st.rerun()
