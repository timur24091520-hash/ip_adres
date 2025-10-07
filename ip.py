import telebot
import requests
from threading import Thread
import time

# Замените 'YOUR_TELEGRAM_BOT_TOKEN' на токен вашего бота от @BotFather
API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

bot = telebot.TeleBot(API_TOKEN)

def get_public_ip():
    """Получает публичный IP адрес"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        if response.status_code == 200:
            return response.json()['ip']
        else:
            return "Не удалось получить IP"
    except Exception as e:
        return f"Ошибка при получении IP: {str(e)}"

def get_detailed_ip_info():
    """Получает подробную информацию об IP"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = """
🤖 Привет! Я бот для проверки IP адреса.

Доступные команды:
/ip - Показать мой публичный IP адрес
/ipinfo - Подробная информация об IP
/help - Показать эту справку

Просто отправь мне команду и я покажу информацию о IP адресе сервера, на котором я запущен.
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['ip'])
def send_ip(message):
    """Обработчик команды /ip - показывает публичный IP"""
    bot.send_chat_action(message.chat.id, 'typing')
    
    ip_address = get_public_ip()
    
    response_text = f"🌐 Ваш публичный IP адрес:\n`{ip_address}`"
    bot.reply_to(message, response_text, parse_mode='Markdown')

@bot.message_handler(commands=['ipinfo'])
def send_ip_info(message):
    """Обработчик команды /ipinfo - показывает подробную информацию об IP"""
    bot.send_chat_action(message.chat.id, 'typing')
    
    ip_info = get_detailed_ip_info()
    
    if ip_info:
        response_text = f"""
📊 Подробная информация об IP:

🏠 IP адрес: `{ip_info.get('ip', 'N/A')}`
🌍 Страна: {ip_info.get('country_name', 'N/A')} ({ip_info.get('country_code', 'N/A')})
🏙️ Город: {ip_info.get('city', 'N/A')}
📮 Регион: {ip_info.get('region', 'N/A')}
📝 Провайдер: {ip_info.get('org', 'N/A')}
🗺️ Часовой пояс: {ip_info.get('timezone', 'N/A')}
💻 ASN: {ip_info.get('asn', 'N/A')}
        """
    else:
        response_text = "❌ Не удалось получить подробную информацию об IP"
    
    bot.reply_to(message, response_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Обработчик любых других сообщений"""
    help_text = """
Не понимаю команду 😊

Используйте:
/ip - узнать IP адрес
/ipinfo - подробная информация
/help - справка
    """
    bot.reply_to(message, help_text)

def start_bot_polling():
    """Запускает polling бота с обработкой ошибок"""
    while True:
        try:
            print("🤖 Бот запущен...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    print("🚀 Запуск Telegram бота для проверки IP...")
    print("📝 Убедитесь, что вы заменили 'YOUR_TELEGRAM_BOT_TOKEN' на реальный токен бота")
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=start_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    try:
        # Бесконечный цикл для поддержания работы программы
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Остановка бота...")
