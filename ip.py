import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = "@dragoncaneloni67"  # Ваш канал

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_type TEXT,
            content TEXT,
            file_id TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Функция для сохранения поста в БД
def save_post(user_id, message_type, content, file_id=None):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO posts (user_id, message_type, content, file_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, message_type, content, file_id))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

# Функция для получения постов на модерации
def get_pending_posts():
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE status = "pending" ORDER BY timestamp')
    posts = cursor.fetchall()
    conn.close()
    return posts

# Функция для обновления статуса поста
def update_post_status(post_id, status):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE posts SET status = ? WHERE id = ?', (status, post_id))
    conn.commit()
    conn.close()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🤖 Добро пожаловать в бот-модератор для канала @dragoncaneloni67!

Вы можете предложить пост для публикации в канале. Просто отправьте:
• Текст
• Фото с подписью
• Видео с подписью
• Документ с подписью

После проверки модератором ваш пост будет опубликован в канале!
    """
    bot.send_message(message.chat.id, welcome_text)

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'):
        return
    
    post_id = save_post(message.from_user.id, 'text', message.text)
    
    # Уведомление пользователю
    bot.send_message(message.chat.id, "✅ Ваш текст отправлен на модерацию!")
    
    # Уведомление администратору
    notify_admin(post_id, message.from_user)

# Обработчик фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.caption is None:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, добавьте подпись к фото!")
        return
    
    file_id = message.photo[-1].file_id
    post_id = save_post(message.from_user.id, 'photo', message.caption, file_id)
    
    bot.send_message(message.chat.id, "✅ Ваше фото с подписью отправлено на модерацию!")
    notify_admin(post_id, message.from_user)

# Обработчик видео
@bot.message_handler(content_types=['video'])
def handle_video(message):
    if message.caption is None:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, добавьте подпись к видео!")
        return
    
    file_id = message.video.file_id
    post_id = save_post(message.from_user.id, 'video', message.caption, file_id)
    
    bot.send_message(message.chat.id, "✅ Ваше видео с подписью отправлено на модерацию!")
    notify_admin(post_id, message.from_user)

# Обработчик документов
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.caption is None:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, добавьте подпись к документу!")
        return
    
    file_id = message.document.file_id
    post_id = save_post(message.from_user.id, 'document', message.caption, file_id)
    
    bot.send_message(message.chat.id, "✅ Ваш документ с подписью отправлен на модерацию!")
    notify_admin(post_id, message.from_user)

# Уведомление администратора о новом посте
def notify_admin(post_id, user):
    posts = get_pending_posts()
    current_post = None
    
    for post in posts:
        if post[0] == post_id:
            current_post = post
            break
    
    if not current_post:
        return
    
    admin_chat_id = "YOUR_ADMIN_CHAT_ID"  # Замените на ваш chat_id
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{post_id}")
    )
    
    user_info = f"👤 Пользователь: @{user.username or 'нет username'}\nID: {user.id}\n"
    post_info = f"📝 Тип: {current_post[2]}\nВремя: {current_post[6]}\n\n"
    
    if current_post[2] == 'text':
        message_text = user_info + post_info + f"Текст:\n{current_post[3]}"
        bot.send_message(admin_chat_id, message_text, reply_markup=keyboard)
    
    elif current_post[2] == 'photo':
        message_text = user_info + post_info + f"Подпись:\n{current_post[3]}"
        bot.send_photo(admin_chat_id, current_post[4], caption=message_text, reply_markup=keyboard)
    
    elif current_post[2] == 'video':
        message_text = user_info + post_info + f"Подпись:\n{current_post[3]}"
        bot.send_video(admin_chat_id, current_post[4], caption=message_text, reply_markup=keyboard)
    
    elif current_post[2] == 'document':
        message_text = user_info + post_info + f"Подпись:\n{current_post[3]}"
        bot.send_document(admin_chat_id, current_post[4], caption=message_text, reply_markup=keyboard)

# Обработчик callback-запросов (кнопки одобрить/отклонить)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith('approve_'):
        post_id = int(call.data.split('_')[1])
        approve_post(post_id, call.message)
    
    elif call.data.startswith('reject_'):
        post_id = int(call.data.split('_')[1])
        reject_post(post_id, call.message)

# Функция одобрения поста
def approve_post(post_id, admin_message):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        bot.answer_callback_query(admin_message.id, "Пост не найден!")
        return
    
    # Публикация в канал
    try:
        if post[2] == 'text':
            bot.send_message(CHANNEL_USERNAME, post[3])
        
        elif post[2] == 'photo':
            bot.send_photo(CHANNEL_USERNAME, post[4], caption=post[3])
        
        elif post[2] == 'video':
            bot.send_video(CHANNEL_USERNAME, post[4], caption=post[3])
        
        elif post[2] == 'document':
            bot.send_document(CHANNEL_USERNAME, post[4], caption=post[3])
        
        # Обновление статуса
        update_post_status(post_id, 'approved')
        
        # Уведомление пользователю
        try:
            bot.send_message(post[1], "🎉 Ваш пост был одобрен и опубликован в канале!")
        except:
            pass
        
        # Обновление сообщения админа
        bot.edit_message_text(
            chat_id=admin_message.chat.id,
            message_id=admin_message.message_id,
            text=f"✅ Пост одобрен и опубликован!\n\n{admin_message.text}",
            reply_markup=None
        )
        
        bot.answer_callback_query(admin_message.id, "Пост опубликован!")
        
    except Exception as e:
        logger.error(f"Ошибка публикации: {e}")
        bot.answer_callback_query(admin_message.id, "Ошибка публикации!")

# Функция отклонения поста
def reject_post(post_id, admin_message):
    update_post_status(post_id, 'rejected')
    
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
    user_id = cursor.fetchone()[0]
    conn.close()
    
    # Уведомление пользователю
    try:
        bot.send_message(user_id, "❌ К сожалению, ваш пост был отклонен модератором.")
    except:
        pass
    
    # Обновление сообщения админа
    bot.edit_message_text(
        chat_id=admin_message.chat.id,
        message_id=admin_message.message_id,
        text=f"❌ Пост отклонен!\n\n{admin_message.text}",
        reply_markup=None
    )
    
    bot.answer_callback_query(admin_message.id, "Пост отклонен!")

# Команда для админа - просмотр очереди
@bot.message_handler(commands=['moderate'])
def show_moderation_queue(message):
    # Проверка, что это админ (замените на ваш chat_id)
    if message.from_user.id != YOUR_ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет прав для этой команды.")
        return
    
    posts = get_pending_posts()
    
    if not posts:
        bot.send_message(message.chat.id, "✅ Нет постов на модерации!")
        return
    
    bot.send_message(message.chat.id, f"📋 Постов на модерации: {len(posts)}")
    
    for post in posts:
        notify_admin(post[0], type('User', (), {'id': post[1], 'username': 'user'}))

if __name__ == "__main__":
    init_db()
    logger.info("Бот запущен!")
    bot.infinity_polling()
