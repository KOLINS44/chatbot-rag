"""
chatbot_logic.py - логика чат-бота «Анти-Похмелье»
"""

import re
import random
from rag_system import RAGSystem

ALCOHOL_CONTENT = {
    "пиво":       {"abv": 0.05, "density": 0.8},
    "вино":       {"abv": 0.12, "density": 0.8},
    "шампанское": {"abv": 0.11, "density": 0.8},
    "водка":      {"abv": 0.40, "density": 0.8},
    "коньяк":     {"abv": 0.40, "density": 0.8},
    "виски":      {"abv": 0.40, "density": 0.8},
}

TOAST_CATEGORIES = {
    "birthday": ("🎂 День рождения", [
        "Пусть каждый следующий год будет лучше предыдущего, а поводов для радости - больше, чем для расстройств. За тебя! 🥂",
        "С годами не стареют - набираются опыта. Выпьем за то, чтобы опыт только прибавлялся, а остальное не менялось!",
        "Здоровья - крепкого, денег - достаточно, любви - взаимной, друзей - верных. Всё остальное приложится. С днём рождения!",
        "Говорят, с каждым годом человек становится мудрее. Значит, ты умнеешь прямо на глазах. Выпьем за твой рост!",
    ]),
    "wedding": ("💍 Свадьба", [
        "Два человека нашли друг друга среди миллиардов людей. Это не случайность - это судьба. За счастье молодых! 🥂",
        "Пусть первая ссора случится как можно позже, а последнее примирение - как можно раньше. За любовь и терпение!",
        "Семья - это не те, с кем тебе хорошо, а те, без кого тебе плохо. Пусть вы всегда будете нужны друг другу!",
        "Говорят, за каждым успешным мужчиной стоит умная женщина. Сегодня он сделал первый шаг к успеху. За невесту!",
    ]),
    "man": ("👨 Мужчине", [
        "За настоящего мужчину - того, кто держит слово и не бросает в трудную минуту. Таких мало - ты из этих. За тебя! 🥂",
        "Мужчина - это не профессия и не звание. Это характер. Выпьем за твой характер - крепкий, как хороший напиток!",
        "Силы - чтобы справляться, мудрости - чтобы не нервничать по пустякам, удачи - чтобы всё получалось. За тебя!",
        "Говорят, настоящий мужчина должен построить дом, посадить дерево и вырастить сына. За всё что ты уже сделал!",
    ]),
    "woman": ("👩 Женщине", [
        "За женщину, которая умеет быть сильной когда нужно, и нежной когда хочется. Это редкое и ценное сочетание! 🥂",
        "Говорят, женщина украшает любое общество. Сегодня мы в этом убеждаемся лично. За тебя - самую обаятельную!",
        "Пусть рядом всегда будут те, кто ценит тебя по достоинству. За тебя!",
        "За женщину - источник вдохновения, тепла и здравого смысла. Без вас нам было бы совсем плохо. За тебя!",
    ]),
    "newyear": ("🎄 Новый год", [
        "Новый год - это повод поверить что всё самое лучшее ещё впереди. С Новым годом! 🥂",
        "Пусть в новом году сбудется то, что не сбылось в прошлом, и добавится то, о чём ещё не мечтали!",
        "Говорят, как встретишь - так и проведёшь. Значит, проведём его в хорошей компании. С Новым годом!",
        "За то, чтобы новый год оказался лучше старого - хотя бы в мелочах. А мелочи и составляют жизнь!",
    ]),
    "funny": ("😄 Юмористический", [
        "Говорят, алкоголь убивает клетки мозга. Но выживают сильнейшие. Выпьем за наши сильнейшие клетки! 🥂",
        "За то, чтобы наши желания совпадали с нашими возможностями - или чтобы хватало наглости не замечать разницы!",
        "В жизни есть три радости - хорошая еда, хорошая компания и хороший напиток. Два из трёх уже есть!",
        "Жизнь сложная штука. Но с правильными людьми и напитками она значительно веселее. За нас!",
    ]),
}


def parse_amount_to_ml(text: str) -> tuple:
    text_low = text.lower()
    drink_type = "водка"
    if any(w in text_low for w in ["пив", "beer"]):
        drink_type = "пиво"
    elif "шампан" in text_low:
        drink_type = "шампанское"
    elif any(w in text_low for w in ["вин", "wine"]):
        drink_type = "вино"
    elif any(w in text_low for w in ["коньяк", "cognac"]):
        drink_type = "коньяк"
    elif any(w in text_low for w in ["виски", "whisky"]):
        drink_type = "виски"

    nums = re.findall(
        r"(\d+(?:[.,]\d+)?)\s*(литр[а-я]*|л\b|ml|мл|г\b|грамм[а-я]*|бутылк[а-я]*|стакан[а-я]*|бокал[а-я]*|рюмк[а-я]*|банк[а-я]*)",
        text_low,
    )

    if not nums:
        nums_raw = re.findall(r"\d+(?:[.,]\d+)?", text_low)
        if nums_raw:
            val = float(nums_raw[0].replace(",", "."))
            volume_ml = val if val > 10 else val * (500 if drink_type == "пиво" else 100)
            return volume_ml, drink_type
        return 300.0, drink_type

    total_ml = 0.0
    for val_str, unit in nums:
        val = float(val_str.replace(",", "."))
        if "литр" in unit or unit == "л":
            total_ml += val * 1000
        elif unit in ("ml", "мл"):
            total_ml += val
        elif unit in ("г",) or "грамм" in unit:
            total_ml += val
        elif "бутылк" in unit:
            total_ml += val * 500
        elif "стакан" in unit or "бокал" in unit:
            total_ml += val * 200
        elif "рюмк" in unit:
            total_ml += val * 50
        elif "банк" in unit:
            total_ml += val * 500
        else:
            total_ml += val

    return max(total_ml, 50.0), drink_type


def calc_pure_alcohol_g(volume_ml: float, drink_type: str) -> float:
    info = ALCOHOL_CONTENT.get(drink_type, ALCOHOL_CONTENT["водка"])
    return volume_ml * info["abv"] * info["density"]


class AntiHangoverBot:

    def __init__(self):
        self.rag = RAGSystem("knowledge_base.txt")

        self.basic_responses = {
            "greeting": {
                "triggers": ["привет", "здравствуй", "здравствуйте", "хай",
                             "hello", "hi", "добрый день", "добрый вечер",
                             "доброе утро", "салют"],
                "response": (
                    "Привет! 👋 Я бот «Анти-Похмелье».\n\n"
                    "Помогу облегчить похмелье, подготовиться к застолью, "
                    "подберу тост или расскажу интересный факт.\n\n"
                    "Нажми кнопку или напиши что тебя интересует! 👇"
                ),
            },
            "how_are_you": {
                "triggers": ["как дела", "как ты", "как сам", "что делаешь", "как жизнь"],
                "response": "Нормально, спасибо! Сижу жду когда кто-нибудь перепьёт 😄 А у тебя как?",
            },
            "who_are_you": {
                "triggers": ["кто ты", "что ты", "что умеешь", "что можешь",
                             "расскажи о себе", "помощь", "help"],
                "response": (
                    "Я - бот «Анти-Похмелье» 🍺\n\n"
                    "**Что умею:**\n"
                    "- 😵 Диагностировать похмелье и давать персональные рекомендации\n"
                    "- 🥂 Рассказать как подготовиться к застолью\n"
                    "- 📜 Подобрать тост на любой случай\n"
                    "- 💡 Поделиться интересным фактом об алкоголе\n\n"
                    "Нажми кнопку или напиши что тебя интересует!"
                ),
            },
            "thanks": {
                "triggers": ["спасибо", "благодарю", "спс", "thanks", "сенкс"],
                "response": "Пожалуйста! 🙏 Береги себя.",
            },
            "bye": {
                "triggers": ["пока", "до свидания", "прощай", "bye", "до встречи"],
                "response": "Пока! 👋 Береги себя. Если что - я здесь.",
            },
        }

        self.hangover_triggers = [
            "похмелье", "похмельный", "бодун", "перепил", "выпил вчера",
            "плохо", "голова болит", "тошнит", "тошнота", "рвота",
            "болею", "помоги", "плохо себя чувствую", "болит голова",
            "слабость", "что делать", "как вылечить",
        ]
        self.prep_triggers = [
            "подготовиться", "подготовка", "застолье", "собираюсь пить",
            "буду пить", "как пить", "правильно пить", "перед вечеринкой",
        ]
        self.fact_triggers = [
            "факт", "интересно", "расскажи", "не знал", "про алкоголь", "миф",
        ]

        self.questions = [
            "Сколько тебе лет?",
            "Какой у тебя вес (в кг)?",
            (
                "Что пил вчера?\n\n"
                "1️⃣ Только пиво\n"
                "2️⃣ Только вино\n"
                "3️⃣ Только водка / крепкий алкоголь\n"
                "4️⃣ Только коньяк / виски\n"
                "5️⃣ Всё подряд / ёрш"
            ),
            (
                "Примерно сколько выпил?\n\n"
                "Укажи объём и напиток, например:\n"
                "- «2 литра пива»\n"
                "- «300 мл водки»\n"
                "- «4 бокала вина»"
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

    def respond(self, user_input: str, diagnosis_mode: bool,
                diagnosis_step: int, user_profile: dict,
                toast_mode: bool = False) -> dict:

        text_lower = user_input.lower().strip()

        if diagnosis_mode:
            return self._handle_diagnosis(user_input, diagnosis_step, user_profile)

        if toast_mode:
            return self._get_toast_by_key(user_input)

        for data in self.basic_responses.values():
            for trigger in data["triggers"]:
                if trigger in text_lower:
                    return self._make_response(data["response"], False, 0, user_profile)

        for trigger in self.hangover_triggers:
            if trigger in text_lower:
                return self._make_response(
                    "Понял, сейчас разберёмся! 🩺 Отвечай честно.\n\n"
                    f"**{self.questions[0]}**",
                    True, 0, {},
                )

        for trigger in self.prep_triggers:
            if trigger in text_lower:
                return self._prep_advice()

        if any(t in text_lower for t in ["тост", "тосты", "выпьем", "бокал", "скажи тост"]):
            return self._show_toast_menu()

        for trigger in self.fact_triggers:
            if trigger in text_lower:
                return self._get_fact()

        rag_result = self.rag.query(user_input)
        if rag_result:
            return self._make_response(
                "Вот что нашёл по твоему вопросу:\n\n" + rag_result +
                "\n\n---\nЕсли плохо - напиши **«мне плохо»**.",
                False, 0, user_profile,
            )

        return self._make_response(
            "Не совсем понял 🤔 Попробуй переформулировать.\n\nИли нажми одну из кнопок внизу.",
            False, 0, user_profile,
        )

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

    def _show_toast_menu(self) -> dict:
        return {
            "text": "## 📜 Выбери повод для тоста\n\nНажми на кнопку с нужной категорией 👇",
            "diagnosis_mode": False,
            "diagnosis_step": 0,
            "user_profile": {},
            "toast_menu": True,
        }

    def _get_toast_by_key(self, key: str) -> dict:
        if key not in TOAST_CATEGORIES:
            return self._make_response(
                "Не нашёл такую категорию. Нажми кнопку «📜 Тост».",
                False, 0, {}
            )
        label, toasts = TOAST_CATEGORIES[key]
        toast = random.choice(toasts)
        text = f"## {label}\n\n{toast}\n\n---\n*Нажми «📜 Тост» ещё раз - подберу другой!*"
        return self._make_response(text, False, 0, {})

    def _prep_advice(self) -> dict:
        rag_info = self.rag.query("подготовка застолье как правильно пить советы", k=3)
        text = "## 🥂 Как подготовиться к застолью\n\n"
        text += rag_info if rag_info else "Поешь перед тем как пить, пей воду между порциями, не мешай напитки."
        text += "\n\n---\n💡 *Если всё же перестарался - напиши **«мне плохо»**.*"
        return self._make_response(text, False, 0, {})

    def _get_fact(self) -> dict:
        rag_info = self.rag.query("интересный факт алкоголь миф правда", k=2)
        text = "## 💡 Интересный факт\n\n"
        text += rag_info if rag_info else "Алкоголь перерабатывается со скоростью ~10 мл чистого спирта в час. Ускорить невозможно!"
        text += "\n\n---\n*Напиши **«ещё факт»** - расскажу следующий!*"
        return self._make_response(text, False, 0, {})

    def _generate_recommendation(self, profile: dict) -> str:
        age = self._extract_number(profile.get("age", "25"))
        weight = self._extract_number(profile.get("weight", "70"))
        sleep_h = self._extract_number(profile.get("sleep_hours", "6"))
        food_ans = str(profile.get("food", "1"))
        drink_type_ans = str(profile.get("drink_type_ans", "1"))
        amount_str = profile.get("amount", "500 мл пива")
        symptoms = str(profile.get("symptoms", "1"))

        if "1" in drink_type_ans:
            main_drink = "пиво"
        elif "2" in drink_type_ans:
            main_drink = "вино"
        elif "4" in drink_type_ans:
            main_drink = "коньяк"
        else:
            main_drink = "водка"

        is_yorsh = "5" in drink_type_ans
        volume_ml, parsed_drink = parse_amount_to_ml(amount_str)
        drink_for_calc = parsed_drink if is_yorsh else main_drink
        pure_alcohol = calc_pure_alcohol_g(volume_ml, drink_for_calc)
        alcohol_per_kg = pure_alcohol / max(weight, 40)

        if alcohol_per_kg < 1.0:
            severity_level = 1
        elif alcohol_per_kg < 2.0:
            severity_level = 2
        else:
            severity_level = 3

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
            penalties.append("пил на голодный желудок")
        if age > 40:
            severity_level = min(severity_level + 1, 3)
            penalties.append("возраст старше 40 лет")
        if "5" in symptoms:
            severity_level = min(severity_level + 1, 3)

        severity_map = {1: "лёгкое", 2: "среднее", 3: "тяжёлое"}
        severity = severity_map[severity_level]

        rag_info = self.rag.query(
            f"похмелье {severity} лечение рекомендации восстановление", k=2
        )

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
            result += f"\n\n### 📖 Дополнительно\n\n{rag_info}"

        result += "\n\n---\n⚠️ *При судорогах, боли в груди или потере сознания - скорая (103).*"

        return result

    def _get_recommendations(self, severity: str) -> str:
        if severity == "лёгкое":
            return (
                "### 💊 Рекомендации\n\n"
                "- Выпей 500-700 мл воды или Регидрона\n"
                "- Активированный уголь (1 таблетка на 10 кг веса)\n"
                "- Поешь: бульон, тост, банан\n"
                "- Ибупрофен 400 мг от головной боли (после еды!)\n"
                "- Прогулка на свежем воздухе\n\n"
                "⏱ **Прогноз:** лучше через 3-5 часов. 👍"
            )
        elif severity == "среднее":
            return (
                "### 💊 Рекомендации\n\n"
                "- Регидрон - 1 пакет на 1 литр воды, пить медленно\n"
                "- Активированный уголь или Энтеросгель\n"
                "- Ибупрофен 400 мг (только после еды!)\n"
                "- Куриный бульон, банан, 2-3 ст. ложки мёда\n"
                "- Постельный режим 3-4 часа\n\n"
                "⏱ **Прогноз:** улучшение через 6-8 часов. ⏳"
            )
        else:
            return (
                "### 💊 Рекомендации (тяжёлый случай)\n\n"
                "- Регидрон - 1 литр медленно в течение часа\n"
                "- Энтеросгель - максимальная доза\n"
                "- ❌ Парацетамол запрещён! Опасен для печени после алкоголя\n"
                "- Полный покой весь день\n"
                "- Пить воду постоянно маленькими глотками\n"
                "- Кефир или айран - обволакивает желудок\n\n"
                "⚠️ **При рвоте более 6 часов - скорая (103)!**\n\n"
                "⏱ **Прогноз:** улучшение через 12-24 часа. 😔"
            )

    @staticmethod
    def _make_response(text, diag_mode, diag_step, profile):
        return {
            "text": text,
            "diagnosis_mode": diag_mode,
            "diagnosis_step": diag_step,
            "user_profile": profile,
            "toast_menu": False,
        }

    @staticmethod
    def _extract_number(text: str) -> float:
        try:
            nums = re.findall(r"\d+(?:[.,]\d+)?", str(text))
            return float(nums[0].replace(",", ".")) if nums else 0.0
        except Exception:
            return 0.0
