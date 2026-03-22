"""
chatbot_logic.py - логика чат-бота «Анти-Похмелье»
Режимы: базовый чат, диагностика похмелья, советы по застолью, тосты, факты
"""

import re
import random
from rag_system import RAGSystem


# Содержание чистого спирта (грамм) в стандартной порции
ALCOHOL_CONTENT = {
    "пиво":    {"density": 0.8, "abv": 0.05},   # 5% об.
    "вино":    {"density": 0.8, "abv": 0.12},   # 12% об.
    "водка":   {"density": 0.8, "abv": 0.40},   # 40% об.
    "коньяк":  {"density": 0.8, "abv": 0.40},
    "виски":   {"density": 0.8, "abv": 0.40},
    "шампанское": {"density": 0.8, "abv": 0.11},
}


def parse_amount_to_ml(text: str) -> tuple[float, str]:
    """
    Пытается извлечь объём в мл из произвольной строки.
    Возвращает (объём_мл, тип_напитка).
    """
    text_low = text.lower()

    # Определяем тип напитка
    drink_type = "водка"
    if any(w in text_low for w in ["пив", "beer"]):
        drink_type = "пиво"
    elif any(w in text_low for w in ["вин", "wine", "шампан"]):
        drink_type = "вино"
    elif any(w in text_low for w in ["коньяк", "cognac"]):
        drink_type = "коньяк"
    elif any(w in text_low for w in ["виски", "whisky", "whiskey"]):
        drink_type = "виски"

    # Ищем числа
    nums = re.findall(r"(\d+(?:[.,]\d+)?)\s*(литр|л\b|liter|ml|мл|г\b|грамм|бутылк|стакан|бокал|рюмк|банк)", text_low)
    if not nums:
        nums_raw = re.findall(r"\d+(?:[.,]\d+)?", text_low)
        if nums_raw:
            val = float(nums_raw[0].replace(",", "."))
            # Эвристика: если число > 10 - скорее всего мл/г, иначе - порции
            volume_ml = val if val > 10 else val * (500 if drink_type == "пиво" else 100)
            return volume_ml, drink_type
        return 300.0, drink_type

    total_ml = 0.0
    for val_str, unit in nums:
        val = float(val_str.replace(",", "."))
        unit = unit.strip()
        if unit in ("литр", "л", "liter"):
            total_ml += val * 1000
        elif unit in ("ml", "мл"):
            total_ml += val
        elif unit in ("г", "грамм"):
            total_ml += val  # граммы ≈ мл для водки
        elif "бутылк" in unit:
            total_ml += val * (500 if drink_type == "пиво" else 500)
        elif unit in ("стакан", "бокал"):
            total_ml += val * 200
        elif "рюмк" in unit:
            total_ml += val * 50
        elif "банк" in unit:
            total_ml += val * 500
        else:
            total_ml += val

    return max(total_ml, 50.0), drink_type


def calc_pure_alcohol_g(volume_ml: float, drink_type: str) -> float:
    """Вычисляет граммы чистого спирта."""
    info = ALCOHOL_CONTENT.get(drink_type, ALCOHOL_CONTENT["водка"])
    return volume_ml * info["abv"] * info["density"]


class AntiHangoverBot:
    """Чат-бот «Анти-Похмелье» с несколькими режимами работы."""

    def __init__(self):
        self.rag = RAGSystem("knowledge_base.txt")

        # --- Базовые ответы ---
        self.basic_responses = {
            "greeting": {
                "triggers": ["привет", "здравствуй", "здравствуйте", "хай",
                             "hello", "hi", "добрый день", "добрый вечер",
                             "доброе утро", "салют", "хэй"],
                "response": (
                    "Привет! 👋 Я бот «Анти-Похмелье».\n\n"
                    "Выбери что тебя интересует или просто напиши:"
                ),
            },
            "how_are_you": {
                "triggers": ["как дела", "как ты", "как сам", "что делаешь",
                             "как жизнь", "как настроение", "что нового"],
                "response": (
                    "Нормально, спасибо! Сижу жду когда кто-нибудь перепьёт 😄\n"
                    "А у тебя как дела? Если плохо - помогу!"
                ),
            },
            "who_are_you": {
                "triggers": ["кто ты", "что ты", "что умеешь", "что можешь",
                             "расскажи о себе", "помощь", "help"],
                "response": (
                    "Я - бот «Анти-Похмелье» 🍺\n\n"
                    "**Что умею:**\n"
                    "- 😵 Диагностировать похмелье и давать персональные рекомендации\n"
                    "- 🥂 Рассказать как правильно подготовиться к застолью\n"
                    "- 📜 Подобрать тост на любой случай\n"
                    "- 💡 Поделиться интересными фактами об алкоголе\n"
                    "- 💬 Просто поговорить\n\n"
                    "Нажми кнопку или напиши что тебя интересует!"
                ),
            },
            "thanks": {
                "triggers": ["спасибо", "благодарю", "спс", "thanks", "сенкс"],
                "response": "Пожалуйста! 🙏 Береги себя и не злоупотребляй.",
            },
            "bye": {
                "triggers": ["пока", "до свидания", "прощай", "bye", "до встречи"],
                "response": "Пока! 👋 Береги себя. Если что - я здесь.",
            },
        }

        # --- Триггеры режимов ---
        self.hangover_triggers = [
            "похмелье", "похмельный", "бодун", "перепил", "выпил вчера",
            "плохо", "голова болит", "тошнит", "тошнота", "рвота",
            "болею", "помоги", "плохо себя чувствую", "болит голова",
            "слабость", "что делать", "как вылечить",
        ]
        self.prep_triggers = [
            "подготовиться", "подготовка", "застолье", "собираюсь пить",
            "буду пить", "как пить", "правильно пить", "перед вечеринкой",
            "перед праздником", "как подготовить",
        ]
        self.toast_triggers = [
            "тост", "тосты", "за здоровье", "выпьем за", "поднять бокал",
            "что сказать", "слово скажи",
        ]
        self.fact_triggers = [
            "факт", "интересно", "расскажи", "не знал", "а знаешь",
            "про алкоголь", "знаешь ли", "миф",
        ]

        # --- Вопросы диагностики ---
        self.questions = [
            "Сколько тебе лет?",
            "Какой у тебя вес (в кг)?",
            (
                "Что пил вчера?\n\n"
                "1️⃣ Только пиво\n"
                "2️⃣ Только вино\n"
                "3️⃣ Только водка / крепкий алкоголь\n"
                "4️⃣ Только коньяк / виски / бурбон\n"
                "5️⃣ Всё подряд / ёрш"
            ),
            (
                "Примерно сколько выпил?\n\n"
                "Укажи объём и напиток, например:\n"
                "- «2 литра пива»\n"
                "- «300 мл водки»\n"
                "- «4 бокала вина»\n"
                "- «литр пива и 200 мл водки» (если смешивал)"
            ),
            "Сколько часов назад закончил пить?",
            "Сколько часов удалось поспать?",
            (
                "Что ел до или во время?\n\n"
                "1️⃣ Нормально поел - полноценный ужин\n"
                "2️⃣ Немного закусывал\n"
                "3️⃣ Почти ничего не ел"
            ),
            (
                "Какие симптомы беспокоят прямо сейчас?\n\n"
                "1️⃣ Только головная боль\n"
                "2️⃣ Только тошнота\n"
                "3️⃣ Слабость и разбитость\n"
                "4️⃣ Сильная жажда и сухость во рту\n"
                "5️⃣ Несколько симптомов сразу"
            ),
        ]
        self.profile_keys = [
            "age", "weight", "drink_type_ans", "amount",
            "hours_since", "sleep_hours", "food", "symptoms",
        ]

    # ------------------------------------------------------------------
    # Главный метод
    # ------------------------------------------------------------------
    def respond(self, user_input: str, diagnosis_mode: bool,
                diagnosis_step: int, user_profile: dict) -> dict:

        text_lower = user_input.lower().strip()

        if diagnosis_mode:
            return self._handle_diagnosis(user_input, diagnosis_step, user_profile)

        # Базовые ответы
        for data in self.basic_responses.values():
            for trigger in data["triggers"]:
                if trigger in text_lower:
                    return self._make_response(data["response"], False, 0, user_profile)

        # Режим диагностики похмелья
        for trigger in self.hangover_triggers:
            if trigger in text_lower:
                return self._make_response(
                    "Понял, сейчас разберёмся! 🩺 Отвечай честно - "
                    "чем точнее ответы, тем лучше рекомендации.\n\n"
                    f"**{self.questions[0]}**",
                    True, 0, {},
                )

        # Режим подготовки к застолью
        for trigger in self.prep_triggers:
            if trigger in text_lower:
                return self._prep_advice()

        # Тосты
        for trigger in self.toast_triggers:
            if trigger in text_lower:
                return self._get_toast(text_lower)

        # Факты
        for trigger in self.fact_triggers:
            if trigger in text_lower:
                return self._get_fact()

        # RAG - поиск по базе знаний
        rag_result = self.rag.query(user_input)
        if rag_result:
            return self._make_response(
                "Вот что нашёл по твоему вопросу:\n\n" + rag_result +
                "\n\n---\nЕсли плохо - напиши **«мне плохо»**.",
                False, 0, user_profile,
            )

        return self._make_response(
            "Не совсем понял 🤔 Попробуй переформулировать.\n\n"
            "Или нажми одну из кнопок внизу.",
            False, 0, user_profile,
        )

    # ------------------------------------------------------------------
    # Диагностика
    # ------------------------------------------------------------------
    def _handle_diagnosis(self, user_input: str, step: int, profile: dict) -> dict:
        key = self.profile_keys[step]
        profile[key] = user_input.strip()
        next_step = step + 1

        if next_step >= len(self.questions):
            return self._make_response(
                self._generate_recommendation(profile), False, 0, profile
            )

        return self._make_response(
            f"**{self.questions[next_step]}**", True, next_step, profile
        )

    # ------------------------------------------------------------------
    # Умный расчёт рекомендаций
    # ------------------------------------------------------------------
    def _generate_recommendation(self, profile: dict) -> str:
        age = self._extract_number(profile.get("age", "25"))
        weight = self._extract_number(profile.get("weight", "70"))
        sleep_h = self._extract_number(profile.get("sleep_hours", "6"))
        food_ans = str(profile.get("food", "1"))
        drink_type_ans = str(profile.get("drink_type_ans", "1"))
        amount_str = profile.get("amount", "500 мл пива")
        symptoms = str(profile.get("symptoms", "1"))

        # Определяем тип напитка по ответу на вопрос 3
        if "1" in drink_type_ans:
            main_drink = "пиво"
        elif "2" in drink_type_ans:
            main_drink = "вино"
        elif "4" in drink_type_ans:
            main_drink = "коньяк"
        else:
            main_drink = "водка"

        is_yorsh = "5" in drink_type_ans

        # Парсим объём и считаем спирт
        volume_ml, parsed_drink = parse_amount_to_ml(amount_str)
        if is_yorsh:
            # При ёрше берём parsed_drink или водку как базу
            pure_alcohol = calc_pure_alcohol_g(volume_ml, parsed_drink)
        else:
            pure_alcohol = calc_pure_alcohol_g(volume_ml, main_drink)

        # Г спирта на кг веса
        alcohol_per_kg = pure_alcohol / max(weight, 40)

        # Базовый уровень по формуле
        if alcohol_per_kg < 1.0:
            severity_level = 1  # лёгкое
        elif alcohol_per_kg < 2.0:
            severity_level = 2  # среднее
        else:
            severity_level = 3  # тяжёлое

        # Штрафы
        penalties = []
        if is_yorsh:
            severity_level = min(severity_level + 1, 3)
            penalties.append("смешивание напитков (ёрш)")
        if sleep_h < 4:
            severity_level = min(severity_level + 1, 3)
            penalties.append(f"мало сна ({int(sleep_h)} ч.)")
        elif sleep_h < 6:
            penalties.append(f"недостаточно сна ({int(sleep_h)} ч.)")
        if "3" in food_ans:
            severity_level = min(severity_level + 1, 3)
            penalties.append("пил почти на голодный желудок")
        if age > 40:
            severity_level = min(severity_level + 1, 3)
            penalties.append("возраст старше 40 лет")
        if "5" in symptoms:
            severity_level = min(severity_level + 1, 3)

        severity_map = {1: "лёгкое", 2: "среднее", 3: "тяжёлое"}
        severity = severity_map[severity_level]

        # Запрос к RAG
        rag_info = self.rag.query(
            f"похмелье {severity} лечение рекомендации симптомы восстановление", k=2
        )

        # Строим отчёт
        result = (
            f"## 🩺 Результат диагностики\n\n"
            f"**Степень похмелья: {severity.upper()}**\n\n"
            f"| Параметр | Значение |\n"
            f"|---|---|\n"
            f"| Возраст | {int(age)} лет |\n"
            f"| Вес | {int(weight)} кг |\n"
            f"| Выпито | {amount_str} |\n"
            f"| Чистый спирт | ~{int(pure_alcohol)} г |\n"
            f"| Нагрузка на кг веса | {alcohol_per_kg:.1f} г/кг |\n"
            f"| Часов прошло | {profile.get('hours_since', '—')} ч. |\n"
            f"| Сон | {int(sleep_h)} ч. |\n"
        )

        if penalties:
            result += f"\n**Факторы утяжеления:** {', '.join(penalties)}\n"

        result += "\n" + self._get_recommendations(severity)

        if rag_info:
            result += f"\n\n### 📖 Дополнительно из базы знаний\n\n{rag_info}"

        result += (
            "\n\n---\n"
            "⚠️ *Если симптомы не улучшаются через 3 часа или появились судороги, "
            "боль в груди - немедленно вызови скорую (103).*"
        )

        return result

    def _get_recommendations(self, severity: str) -> str:
        if severity == "лёгкое":
            return (
                "### 💊 Рекомендации\n\n"
                "**Сразу:**\n"
                "- Выпей 500-700 мл воды или Регидрона\n"
                "- Активированный уголь (1 таблетка на 10 кг веса)\n"
                "- Поешь: бульон, тост, банан\n\n"
                "**В течение дня:**\n"
                "- Пить воду маленькими глотками - 1.5-2 литра\n"
                "- Ибупрофен 400 мг от головной боли (после еды!)\n"
                "- Прогулка на свежем воздухе\n"
                "- Витамин C 500 мг\n\n"
                "⏱ **Прогноз:** лучше через 3-5 часов. 👍"
            )
        elif severity == "среднее":
            return (
                "### 💊 Рекомендации\n\n"
                "**Срочно:**\n"
                "- Регидрон - 1 пакет на 1 литр воды, пить медленно\n"
                "- Активированный уголь или Энтеросгель\n"
                "- Ибупрофен 400 мг (только после еды!)\n\n"
                "**Питание:**\n"
                "- Куриный бульон с сухариками\n"
                "- Банан - восстановит калий\n"
                "- 2-3 ст. ложки мёда - ускоряет вывод алкоголя\n\n"
                "**Режим:**\n"
                "- Постельный режим 3-4 часа\n"
                "- Никакого алкоголя «для опохмела»!\n\n"
                "⏱ **Прогноз:** улучшение через 6-8 часов. ⏳"
            )
        else:
            return (
                "### 💊 Рекомендации (тяжёлый случай)\n\n"
                "**Срочно:**\n"
                "- Регидрон - 1 литр медленно в течение часа\n"
                "- Энтеросгель - максимальная доза\n"
                "- Лечь, обеспечить свежий воздух\n\n"
                "**Важно:**\n"
                "- ❌ Парацетамол запрещён! Опасен для печени после алкоголя\n"
                "- Ибупрофен - только если нет проблем с желудком\n"
                "- Полный покой весь день\n"
                "- Пить воду постоянно маленькими глотками\n\n"
                "**Питание:**\n"
                "- Только лёгкое: бульон, тост, банан\n"
                "- Кефир или айран - обволакивает желудок\n\n"
                "⚠️ **При рвоте более 6 часов или потере сознания - скорая (103)!**\n\n"
                "⏱ **Прогноз:** улучшение через 12-24 часа. 😔"
            )

    # ------------------------------------------------------------------
    # Советы по застолью
    # ------------------------------------------------------------------
    def _prep_advice(self) -> dict:
        rag_info = self.rag.query("подготовка застолье как правильно пить советы", k=3)
        text = (
            "## 🥂 Как подготовиться к застолью\n\n"
            "Правильная подготовка снижает риск тяжёлого похмелья в 2-3 раза.\n\n"
        )
        if rag_info:
            text += rag_info
        text += (
            "\n\n---\n"
            "💡 *Если всё же перестарался - напиши **«мне плохо»**, "
            "проведём диагностику.*"
        )
        return self._make_response(text, False, 0, {})

    # ------------------------------------------------------------------
    # Тосты
    # ------------------------------------------------------------------
    def _get_toast(self, text_lower: str) -> dict:
        if any(w in text_lower for w in ["день рождения", "рождения", "birthday"]):
            query = "тост день рождения поздравление"
        elif any(w in text_lower for w in ["свадьб", "молодожён", "невест", "жених"]):
            query = "тост свадьба молодые"
        elif any(w in text_lower for w in ["друг", "дружб", "компани"]):
            query = "тост дружба друзья"
        elif any(w in text_lower for w in ["здоровь", "здоров"]):
            query = "тост здоровье долголетие"
        elif any(w in text_lower for w in ["встреч", "встретил", "вместе"]):
            query = "тост встреча вместе"
        elif any(w in text_lower for w in ["смешн", "юмор", "прикол"]):
            query = "тост юмористический смешной"
        elif any(w in text_lower for w in ["коротк", "быстр"]):
            query = "тост короткий универсальный"
        else:
            query = "тост универсальный"

        rag_info = self.rag.query(query, k=2)
        text = "## 📜 Тост\n\n"
        if rag_info:
            text += rag_info
        else:
            text += "Будем здоровы! 🥂"
        text += "\n\n---\n💡 *Уточни повод - подберу более подходящий тост!*"
        return self._make_response(text, False, 0, {})

    # ------------------------------------------------------------------
    # Факты
    # ------------------------------------------------------------------
    def _get_fact(self) -> dict:
        rag_info = self.rag.query(
            "интересный факт алкоголь миф правда", k=2
        )
        text = "## 💡 Интересный факт\n\n"
        if rag_info:
            text += rag_info
        else:
            text += "Алкоголь перерабатывается печенью со скоростью ~10 мл чистого спирта в час. Ускорить этот процесс невозможно!"
        text += "\n\n---\n*Напиши **«ещё факт»** - расскажу следующий!*"
        return self._make_response(text, False, 0, {})

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    @staticmethod
    def _make_response(text: str, diag_mode: bool, diag_step: int, profile: dict) -> dict:
        return {
            "text": text,
            "diagnosis_mode": diag_mode,
            "diagnosis_step": diag_step,
            "user_profile": profile,
        }

    @staticmethod
    def _extract_number(text: str) -> float:
        try:
            nums = re.findall(r"\d+(?:[.,]\d+)?", str(text))
            return float(nums[0].replace(",", ".")) if nums else 0.0
        except Exception:
            return 0.0
