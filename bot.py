import random
import time
import json
import os
import threading
from datetime import datetime
import telebot
from groq import Groq
import schedule

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = "8974825461:AAGQ9YZz1rSJUBRfXBrT-AbsyW7m7ySrCeQ"
CHANNEL_ID = "@AnimeSoulDark"

GROQ_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
# Добавили увеличенный таймаут (30 секунд) и повторные попытки для стабильности в облаке
groq_client = Groq(api_key=GROQ_API_KEY, timeout=30.0, max_retries=3)

STATE_FILE = "bot_state.json"
HISTORY_FILE = "bot_history.json"

CONTENT_PLAN_30_DAYS = [
    ("ТЫ ЭТО ПРОПУСТИЛ", "Скрытая сцена в Клинок рассекающий демонов, где Танджиро на секунду замечает будущее."),
    ("СЕКРЕТ", "Какие реальные исторические символы спрятаны в форме разведкорпуса в Атаке титанов."),
    ("ПЕРСОНАЖ", "Почему Саске Учиха поступил именно так в финале битвы с Наруто."),
    ("ЧТО ЕСЛИ?", "Что было бы, если Минато и Кушина выжили в день нападения Девятихвостого на Коноху?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Реальные японские городские легенды, на которых построена Магическая битва."),
    ("СЕКРЕТ", "Скрытый смысл изменения цвета глаз и формы зрачков у персонажей Наруто."),
    ("ПЕРСОНАЖ", "Психологический перелом Эрена Йегера: в какой именно момент он сломался?"),
    ("ЧТО ЕСЛИ?", "Что было бы, если Лайт Ягами не нашел Тетрадь Смерти в самый первый день?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Колоссальный труд аниматоров студии MAPPA: детали, которые никто не ценит."),
    ("СЕКРЕТ", "Тайные философские отсылки и библейские мотивы в аниме Евангелион."),
    ("ПЕРСОНАЖ", "Почему Ророноа Зоро из One Piece никогда не предал бы свою мечту."),
    ("ЧТО ЕСЛИ?", "Что если бы Итачи Учиха отказался уничтожать свой клан и пошел против старейшин?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Как создавался давящий и мрачный саундтрек для Тетради Смерти."),
    ("СЕКРЕТ", "Неочевидные связи и параллели между капитанами отрядов в Бличе."),
    ("ПЕРСОНАЖ", "Тяжелая ноша Годжо Сатору: почему абсолютная сила приносит только одиночество."),
    ("ЧТО ЕСЛИ?", "Что было бы, если Танджиро не успел спасти Незуко от превращения до конца?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Точные реальные географические места из фильма Твоё имя, куда ездят фанаты."),
    ("СЕКРЕТ", "Гениальные пасхалки от Studio Ghibli, спрятанные на задних планах."),
    ("ПЕРСОНАЖ", "Внутренний ад Кен Канеки из Токийского гуля: цена принятия своей второй половины."),
    ("ЧТО ЕСЛИ?", "Что если бы Манки Д. Луффи съел другой дьявольский плод вместо Гому-Гому?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Исторические прототипы реальных самураев в сериале Самурай Чамплу."),
    ("СЕКРЕТ", "Скрытый сатирический смысл концовок в аниме Ванпанчмен."),
    ("ПЕРСОНАЖ", "Истинные мотивы и скрытая глубина Кацуки Бакуго из Моей геройской академии."),
    ("ЧТО ЕСЛИ?", "Что если бы Незуко погибла вместе с семьей в самой первой серии?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Секреты уникальной цифровой рисовки и динамики боев в Клинке."),
    ("СЕКРЕТ", "Тонкие цитаты и отсылки к классическому американскому нуару в Ковбой Бибоп."),
    ("ПЕРСОНАЖ", "Почему Мадара Учиха — самый прописанный злодей сёнэна, а не просто безумец."),
    ("ЧТО ЕСЛИ?", "Что если бы L победил Лайта в Тетради Смерти в первые недели расследования?"),
    ("ТЫ ЭТО ПРОПУСТИЛ", "Скрытая механика и жесткие ограничения Нэн в мире Hunter x Hunter."),
    ("СЕКРЕТ", "Какое значение на самом деле имеет цвет волос персонажей в популярных сёнэнах.")
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current_day": 0, "total_published": 0}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def generate_and_publish_post(custom_topic=None):
    try:
        state = load_state()
        history = load_history()

        if custom_topic:
            rubric_name = "АВТОРСКИЙ РАЗБОР"
            anime_topic = custom_topic
        else:
            day_index = state["current_day"] % len(CONTENT_PLAN_30_DAYS)
            rubric_name, anime_topic = CONTENT_PLAN_30_DAYS[day_index]
            state["current_day"] += 1

        recent_posts = [h["topic"] for h in history[-3:]]
        context_str = f"Недавно в канале уже публиковалось: {', '.join(recent_posts)}." if recent_posts else ""

        system_prompt = f"""
        Ты — элитный копирайтер и эксперт по аниме. Напиши увлекательный, глубокий и понятный пост для Telegram-канала.
        {context_str}
        
        Рубрика: {rubric_name}
        Тема для разбора: {anime_topic}

        ЖЕСТКИЕ ПРАВИЛА:
        1. СТРОГО НА РУССКОМ ЯЗЫКЕ. Никаких английских слов, транслита или обрывков фраз.
        2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать символ звездочки (*).
        3. МИНИМУМ СМАЙЛИКОВ (не больше 1 на весь текст, или вообще без них).
        4. Пиши строго по теме, логично и интересно.
        5. Структура: мощный хук в первой строке, короткие абзацы, в конце — жирный вопрос для обсуждения в комментариях.
        6. Если есть сюжетные спойлеры, в самом начале напиши: СПОЙЛЕРЫ.
        """

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты профессиональный копирайтер."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        post_text = completion.choices[0].message.content.strip()
        final_post = f"--- {rubric_name} ---\n\n{post_text}"

        bot.send_message(CHANNEL_ID, final_post)

        state["total_published"] += 1
        save_state(state)

        history.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "rubric": rubric_name,
            "topic": anime_topic
        })
        save_history(history)

        print(f"[УСПЕХ] Опубликовано: {anime_topic}")
        return anime_topic

    except Exception as e:
        print(f"[ОШИБКА генерации/публикации]: {e}")
        try:
            bot.send_message(CHANNEL_ID, f"⚠️ Ошибка публикации поста: {e}")
        except:
            pass
        return None

@bot.message_handler(commands=['post'])
def cmd_post(message):
    user_input = message.text.replace('/post', '').strip()
    bot.reply_to(message, "AI Editor (Groq): Генерирую пост...")
    topic = user_input if user_input else None
    published_topic = generate_and_publish_post(custom_topic=topic)
    
    if published_topic:
        bot.send_message(message.chat.id, f"Пост успешно опубликован в канале!\n\nТема: {published_topic}")
    else:
        bot.send_message(message.chat.id, "Ошибка генерации. Проверьте логи хостинга.")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    state = load_state()
    current_day = state["current_day"] + 1
    total = state["total_published"]
    next_rubric, next_topic = CONTENT_PLAN_30_DAYS[state["current_day"] % len(CONTENT_PLAN_30_DAYS)]
    
    status_text = (
        f"🤖 **Статус Cloud Agent:**\n\n"
        f"📅 День по плану: **День {current_day} из 30**\n"
        f"📊 Опубликовано: **{total}**\n\n"
        f"🔜 **Следующая тема:**\n"
        f"[{next_rubric}] {next_topic}"
    )
    bot.reply_to(message, status_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def cmd_reset(message):
    if os.path.exists(STATE_FILE): os.remove(STATE_FILE)
    if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
    bot.reply_to(message, "🔄 Прогресс сброшен. План на 30 дней начат заново с Дня 1.")

def run_scheduler():
    schedule.every().day.at("12:00").do(generate_and_publish_post)
    schedule.every().day.at("18:00").do(generate_and_publish_post)
    schedule.every().day.at("21:00").do(generate_and_publish_post)

    while True:
        schedule.run_pending()
        time.sleep(60)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

print("Cloud Anime Factory (Text Only Edition) запущен!")
bot.infinity_polling()
