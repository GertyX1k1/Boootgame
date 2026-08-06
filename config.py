import os

# Токен бота — получить у @BotFather в Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")

# ID админов через запятую в переменной окружения ADMIN_IDS, например "123456789,987654321"
# Узнать свой ID можно у бота @userinfobot
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x]

DB_PATH = os.getenv("DB_PATH", "game.db")

# Опционально: ссылки на картинки для оформления сообщений (можно оставить пустыми)
IMG_WELCOME = os.getenv("IMG_WELCOME", "")
IMG_BATTLE = os.getenv("IMG_BATTLE", "")
IMG_VICTORY = os.getenv("IMG_VICTORY", "")
IMG_DEFEAT = os.getenv("IMG_DEFEAT", "")
IMG_LEVELUP = os.getenv("IMG_LEVELUP", "")
