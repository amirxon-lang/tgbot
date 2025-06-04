import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import os
from keep_alive import keep_alive

keep_alive()

# Botni yaratish
bot = Bot(token=os.environ.get('token'))
dp = Dispatcher(bot)

# Asosiy menyu
menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
menu_buttons.add("❌⭕ X O", "✊✌️✋ TQQ")
menu_buttons.add("🔢 Son topish", "🔠 So'z topish")

# O'yinlar uchun ma'lumotlar
active_games = {
    "xo": {},
    "word": {},
    "guess": {},
    "tqq": {}
}

user_stats = {}
last_activity = {}

# Spam nazorati
async def check_spam(user_id: int):
    now = time.time()
    if user_id in last_activity and (now - last_activity[user_id]) < 2:
        return True
    last_activity[user_id] = now
    return False

# Statistikani yangilash
def update_stats(user_id: int, game_type: str, won: bool = True):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "total": {"played": 0, "won": 0},
            "xo": {"played": 0, "won": 0},
            "tqq": {"played": 0, "won": 0},
            "guess": {"played": 0, "won": 0},
            "word": {"played": 0, "won": 0}
        }
    
    user_stats[user_id]["total"]["played"] += 1
    user_stats[user_id][game_type]["played"] += 1
    
    if won:
        user_stats[user_id]["total"]["won"] += 1
        user_stats[user_id][game_type]["won"] += 1

# Start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if await check_spam(message.from_user.id):
        await message.reply("⏳ Iltimos, 2 soniya kutib turing!")
        return
    
    await message.reply(
        "🎮 O'yinlar botiga xush kelibsiz!\n\n"
        "Quyidagi o'yinlardan birini tanlang:",
        reply_markup=menu_buttons
    )

# X O o'yini
@dp.message_handler(lambda m: m.text == "❌⭕ X O")
async def start_xo(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    chat_id = message.chat.id
    active_games["xo"][chat_id] = ["⬜"] * 9
    await show_xo_board(chat_id)

async def show_xo_board(chat_id):
    board = active_games["xo"][chat_id]
    markup = InlineKeyboardMarkup(row_width=3)
    
    for i in range(9):
        markup.insert(InlineKeyboardButton(board[i], callback_data=f"xo_{i}"))
    
    await bot.send_message(chat_id, "X O o'yini:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('xo_'))
async def process_xo_move(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    move = int(callback.data.split('_')[1])
    
    if chat_id not in active_games["xo"] or active_games["xo"][chat_id][move] != "⬜":
        return
    
    # Foydalanuvchi harakati
    active_games["xo"][chat_id][move] = "❌"
    await show_xo_board(chat_id)
    
    # G'olibni tekshirish
    result = check_winner(active_games["xo"][chat_id], "❌")
    if result == "win":
        update_stats(callback.from_user.id, "xo", True)
        await callback.message.answer("🎉 Siz yutdingiz!")
        del active_games["xo"][chat_id]
        return
    elif result == "draw":
        await callback.message.answer("🤝 Durrang!")
        del active_games["xo"][chat_id]
        return
    
    # Bot harakati
    empty = [i for i, cell in enumerate(active_games["xo"][chat_id]) if cell == "⬜"]
    if empty:
        bot_move = random.choice(empty)
        active_games["xo"][chat_id][bot_move] = "⭕"
        await show_xo_board(chat_id)
        
        result = check_winner(active_games["xo"][chat_id], "⭕")
        if result == "win":
            await callback.message.answer("🤖 Bot yutdi!")
            del active_games["xo"][chat_id]
        elif result == "draw":
            await callback.message.answer("🤝 Durrang!")
            del active_games["xo"][chat_id]

def check_winner(board, player):
    win_patterns = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Gorizontal
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Vertikal
        [0, 4, 8], [2, 4, 6]               # Diagonal
    ]
    
    for pattern in win_patterns:
        if all(board[i] == player for i in pattern):
            return "win"
    
    if "⬜" not in board:
        return "draw"
    
    return False

# Tosh-qaychi-qog'oz o'yini
@dp.message_handler(lambda m: m.text == "✊✌️✋ TQQ")
async def start_tqq(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("✊", callback_data="tqq_rock"),
        InlineKeyboardButton("✌️", callback_data="tqq_scissors"),
        InlineKeyboardButton("✋", callback_data="tqq_paper")
    )
    await message.reply("Tanlang:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('tqq_'))
async def process_tqq(callback: types.CallbackQuery):
    choices = {
        "tqq_rock": "✊",
        "tqq_scissors": "✌️",
        "tqq_paper": "✋"
    }
    user_choice = choices[callback.data]
    bot_choice = random.choice(list(choices.values()))
    
    if user_choice == bot_choice:
        result = "🤝 Durrang!"
        won = None
    elif (user_choice == "✊" and bot_choice == "✌️") or \
         (user_choice == "✌️" and bot_choice == "✋") or \
         (user_choice == "✋" and bot_choice == "✊"):
        result = "🎉 Siz yutdingiz!"
        won = True
    else:
        result = "🤖 Bot yutdi!"
        won = False
    
    if won is not None:
        update_stats(callback.from_user.id, "tqq", won)
    
    await callback.message.edit_text(
        f"Siz: {user_choice}\nBot: {bot_choice}\n\n{result}"
    )

# Son topish o'yini
@dp.message_handler(lambda m: m.text == "🔢 Son topish")
async def start_guess_number(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("1-10", callback_data="guess_10"),
        InlineKeyboardButton("1-50", callback_data="guess_50"),
        InlineKeyboardButton("1-100", callback_data="guess_100")
    )
    await message.reply("Diapazonni tanlang:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('guess_'))
async def set_guess_range(callback: types.CallbackQuery):
    max_num = int(callback.data.split('_')[1])
    secret = random.randint(1, max_num)
    active_games["guess"][callback.message.chat.id] = {
        "secret": secret,
        "max": max_num,
        "attempts": 0
    }
    await callback.message.edit_text(f"1 dan {max_num} gacha son o'yladim. Topishga harakat qiling!")

@dp.message_handler(lambda m: m.text.isdigit())
async def check_guess(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_games["guess"]:
        return
    
    game = active_games["guess"][chat_id]
    guess = int(message.text)
    game["attempts"] += 1
    
    if guess < game["secret"]:
        await message.reply("⬆ Kattaroq!")
    elif guess > game["secret"]:
        await message.reply("⬇ Kichikroq!")
    else:
        update_stats(message.from_user.id, "guess", True)
        await message.reply(
            f"🎉 To'g'ri! {game['secret']} sonini {game['attempts']} urinishda topdingiz!"
        )
        del active_games["guess"][chat_id]

# So'z topish o'yini
# So'z topish o'yini uchun so'zlar ro'yxati
words = ["smartfon", "blog", "video", "robot", "montaj", "tizim", "funksiya"]

# O'yin holatlarini saqlash uchun dictionary
word_games = {}

@dp.message_handler(lambda message: message.text == "🔠 So'z topish")
async def start_word_game(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    chat_id = message.chat.id
    hidden_word = random.choice(words)
    masked_word = ["_"] * len(hidden_word)
    letters = list(hidden_word)
    random.shuffle(letters)

    word_games[chat_id] = {
        "word": hidden_word,
        "masked": masked_word,
        "next_index": 0,
        "remaining_letters": letters
    }

    await show_word_board(chat_id)

async def show_word_board(chat_id):
    game = word_games[chat_id]
    word_display = " ".join(game["masked"])

    buttons = InlineKeyboardMarkup(row_width=5)
    for letter in game["remaining_letters"]:
        buttons.insert(InlineKeyboardButton(text=letter, callback_data=f"word_{letter}"))

    await bot.send_message(chat_id, f"So'z: {word_display}\nHarflarni tanlang:", reply_markup=buttons)

@dp.callback_query_handler(lambda call: call.data.startswith("word_"))
async def process_word_guess(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    game = word_games.get(chat_id)
    if not game:
        return

    letter = call.data.split("_")[1]
    next_index = game["next_index"]

    if game["word"][next_index] == letter:
        game["masked"][next_index] = letter
        game["next_index"] += 1
        game["remaining_letters"].remove(letter)

        if "_" not in game["masked"]:
            update_stats(call.from_user.id, "word", True)
            await bot.send_message(chat_id, f"🎉 Siz so'zni topdingiz! So'z: {game['word']}")
            del word_games[chat_id]
            return

    await show_word_board(chat_id)

# Statistikani ko'rish
@dp.message_handler(commands=['stats'])
async def show_stats(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    if message.from_user.id not in user_stats:
        await message.reply("Siz hali hech qanday o'yin o'ynamagansiz!")
        return
    
    stats = user_stats[message.from_user.id]
    text = (
        "📊 Sizning statistikangiz:\n\n"
        f"🎮 Jami o'yinlar: {stats['total']['played']}\n"
        f"🏆 G'alabalar: {stats['total']['won']}\n\n"
        f"❌⭕ X O: {stats['xo']['won']}/{stats['xo']['played']}\n"
        f"✊✌️✋ TQQ: {stats['tqq']['won']}/{stats['tqq']['played']}\n"
        f"🔢 Son topish: {stats['guess']['won']}/{stats['guess']['played']}\n"
        f"🔠 So'z topish: {stats['word']['won']}/{stats['word']['played']}"
    )
    await message.reply(text)

# Top foydalanuvchilar
@dp.message_handler(commands=['top'])
async def show_top_players(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    if not user_stats:
        await message.reply("Hali hech qanday statistika to'plalmagan!")
        return
    
    top_players = sorted(
        user_stats.items(),
        key=lambda x: x[1]['total']['won'],
        reverse=True
    )[:10]
    
    text = "🏆 Eng ko'p g'alaba qozonganlar:\n\n"
    for i, (user_id, stats) in enumerate(top_players, 1):
        try:
            user = await bot.get_chat(user_id)
            name = user.username or user.first_name
        except:
            name = f"Foydalanuvchi {user_id}"
        
        text += f"{i}. {name} - {stats['total']['won']} g'alaba\n"
    
    await message.reply(text)

# Barcha buyruqlar ro'yxati
@dp.message_handler(commands=['help'])
async def show_help(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    help_text = (
        "🛠 Buyruqlar ro'yxati:\n\n"
        "/start - Botni ishga tushirish\n"
        "/stats - Shaxsiy statistikani ko'rish\n"
        "/top - Eng yaxshi o'yinchilar\n"
        "/help - Yordam\n\n"
        "Yoki quyidagi menyudan o'yin tanlang!"
    )
    await message.reply(help_text, reply_markup=menu_buttons)

# Noma'lum xabarlarga javob
@dp.message_handler()
async def handle_unknown(message: types.Message):
    if await check_spam(message.from_user.id):
        return
    
    await message.reply(
        "Iltimos, menyudan o'yin tanlang yoki /help buyrug'ini yuboring!",
        reply_markup=menu_buttons
    )

# Botni ishga tushurish
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
