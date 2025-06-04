import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import os
from keep_alive import keep_alive
keep_alive()

# Tokenni environment variablesdan olamiz

bot = Bot(token=os.environ.get('token'))
dp = Dispatcher(bot)

# O'yinlar menyusi tugmalari
menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
menu_buttons.add("❌⭕ X O", "✊✌️✋ TQQ")
menu_buttons.add("🔢 Son topish", "🔠 So'z topish")

# Foydalanuvchilar uchun strukturani saqlash
active_users = set()
user_last_message = {}  # Spam nazorati uchun
user_stats = {}  # Foydalanuvchi statistikasi

# Admin ID
ADMIN_ID = 5984770229

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Spam nazorati funktsiyasi
async def is_spam(user_id: int) -> bool:
    now = time.time()
    last_time = user_last_message.get(user_id, 0)
    if now - last_time < 2:  # 3 sekunddan kam bo'lsa spam hisoblanadi
        return await message.reply("iltimos spam qilmang 2 sekund kuting")
    user_last_message[user_id] = now
    return False

# Statistikani yangilash
def update_stats(user_id: int, game: str, win: bool = True):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "total_games": 0,
            "wins": 0,
            "games": {
                "xo": {"played": 0, "wins": 0},
                "tqq": {"played": 0, "wins": 0},
                "guess_number": {"played": 0, "wins": 0},
                "guess_word": {"played": 0, "wins": 0}
            }
        }
    
    user_stats[user_id]["total_games"] += 1
    user_stats[user_id]["games"][game]["played"] += 1
    
    if win:
        user_stats[user_id]["wins"] += 1
        user_stats[user_id]["games"][game]["wins"] += 1

# **START KOMANDASI**
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if await is_spam(message.from_user.id):
        return
    
    user_id = message.from_user.id
    active_users.add(user_id)
    
    start_text = ("🎮 *Mini o'yinlar botiga xush kelibsiz!*\n\n"
                "📌 Quyidagi o'yinlardan birini tanlang:\n\n"
                "✅ *❌⭕ X O* — Klassik X O o'yini\n"
                "✅ *✊✌️✋ TQQ* — Tosh-Qaychi-Qog'oz\n"
                "✅ *🔢 Son topish* — Berilgan diapazonda son topish\n"
                "✅ *🔠 So'z topish* — Harflarni ketma-ket tanlab so'z topish\n\n"
                "ℹ️ Har bir o'yinda g'alaba qozonishga harakat qiling! 🎯")
    await message.reply(start_text, parse_mode="Markdown", reply_markup=menu_buttons)

@dp.message_handler(lambda message: not (message.text in ["❌⭕ X O", "✊✌️✋ TQQ", "🔢 Son topish", "🔠 So'z topish"] or message.text.isdigit()))
async def block_unwanted_messages(message: types.Message):
    await message.reply("faqat knopkalar ishlating")

# **X O o'yini**
games = {}

@dp.message_handler(lambda message: message.text == "❌⭕ X O")
async def xo_game(message: types.Message):
    if await is_spam(message.from_user.id):
        return
    
    chat_id = message.chat.id
    games[chat_id] = ["⬜"] * 9
    await show_xo_board(chat_id)

async def show_xo_board(chat_id):
    board = games[chat_id]
    board_text = "\n".join([" | ".join(board[i:i+3]) for i in range(0, 9, 3)])
    
    buttons = InlineKeyboardMarkup(row_width=3)
    for i in range(9):
        buttons.insert(InlineKeyboardButton(text=board[i], callback_data=f"move_{i}"))

    await bot.send_message(chat_id, board_text, reply_markup=buttons)

@dp.callback_query_handler(lambda call: call.data.startswith("move_"))
async def xo_move(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    move = int(call.data.split("_")[1])

    if chat_id not in games:
        return

    if games[chat_id][move] == "⬜":
        games[chat_id][move] = "❌"
        await show_xo_board(chat_id)

        # G'olibni tekshirish
        result = check_winner(games[chat_id], "❌")
        if result == True:
            update_stats(call.from_user.id, "xo")
            await bot.send_message(chat_id, "🎉 Siz yutdingiz! +1 ochko")
            del games[chat_id]
            return
        elif result == "draw":
            await bot.send_message(chat_id, "🤝 Durrang! Hech kim yutmadi.")
            del games[chat_id]
            return

        # Bot harakat qiladi
        bot_move = best_move(games[chat_id])
        games[chat_id][bot_move] = "⭕"
        await show_xo_board(chat_id)

        # Bot yutganini tekshirish
        result = check_winner(games[chat_id], "⭕")
        if result == True:
            await bot.send_message(chat_id, "🤖 Bot yutdi!")
            del games[chat_id]
        elif result == "draw":
            await bot.send_message(chat_id, "🤝 Durrang! Hech kim yutmadi.")
            del games[chat_id]

def best_move(board):
    empty = [i for i in range(9) if board[i] == "⬜"]
    for mark in ["⭕", "❌"]:
        for i in empty:
            board[i] = mark
            if check_winner(board, mark):
                board[i] = "⬜"
                return i
            board[i] = "⬜"
    return random.choice(empty)

def check_winner(board, player):
    win_positions = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    if any(board[a] == board[b] == board[c] == player for a, b, c in win_positions):
        return True
    # Agar barcha kataklar to'ldirilgan bo'lsa, durrang
    if "_" not in board and "⬜" not in board:
        return "draw"
    return False

# **So'z topish o'yini**
words = ["smartfon", "blog", "video", "robot", "montaj", "tizim", "funksiya"]

word_games = {}

@dp.message_handler(lambda message: message.text == "🔠 So'z topish")
async def soz_topish_start(message: types.Message):
    if await is_spam(message.from_user.id):
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

    await show_guess_board(chat_id)

async def show_guess_board(chat_id):
    game = word_games[chat_id]
    word_display = " ".join(game["masked"])

    buttons = InlineKeyboardMarkup(row_width=5)
    for letter in game["remaining_letters"]:
        buttons.insert(InlineKeyboardButton(text=letter, callback_data=f"guess_{letter}"))

    await bot.send_message(chat_id, f"So'z: {word_display}\nHarflarni tanlang:", reply_markup=buttons)

@dp.callback_query_handler(lambda call: call.data.startswith("guess_"))
async def process_guess(call: types.CallbackQuery):
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
            update_stats(call.from_user.id, "guess_word")
            await bot.send_message(chat_id, f"🎉 Siz so'zni topdingiz! So'z: {game['word']} +1 ochko")
            del word_games[chat_id]
            return

    await show_guess_board(chat_id)

# **Son topish o'yini**
guess_games = {}

@dp.message_handler(lambda message: message.text == "🔢 Son topish")
async def choose_range(message: types.Message):
    if await is_spam(message.from_user.id):
        return
    
    buttons = InlineKeyboardMarkup(row_width=3)
    buttons.add(
        InlineKeyboardButton("1-10", callback_data="range_10"),
        InlineKeyboardButton("1-100", callback_data="range_100"),
        InlineKeyboardButton("1-1000", callback_data="range_1000")
    )
    await message.reply("Diapazonni tanlang:", reply_markup=buttons)

@dp.callback_query_handler(lambda call: call.data.startswith("range_"))
async def start_guess_game(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    max_value = int(call.data.split("_")[1])
    secret_number = random.randint(1, max_value)
    
    guess_games[chat_id] = {
        "max_value": max_value,
        "secret_number": secret_number,
        "attempts": 0
    }
    
    await bot.send_message(chat_id, f"Men 1 dan {max_value} gacha son o'yladim. Uni topishga harakat qiling!")

@dp.message_handler(lambda message: message.text.isdigit())
async def process_guess(message: types.Message):
    chat_id = message.chat.id
    game = guess_games.get(chat_id)

    if not game:
        return

    guess = int(message.text)
    game["attempts"] += 1

    if guess < game["secret_number"]:
        await message.reply("⬆ Kattaroq son kiriting!")
    elif guess > game["secret_number"]:
        await message.reply("⬇ Kichikroq son kiriting!")
    else:
        update_stats(message.from_user.id, "guess_number")
        await message.reply(f"🎉 To'g'ri topdingiz! {game['secret_number']} ({game['attempts']} urinishda) +1 ochko")
        del guess_games[chat_id]

# **Tosh-Qaychi-Qog'oz**
@dp.message_handler(lambda message: message.text == "✊✌️✋ TQQ")
async def tqq_game(message: types.Message):
    if await is_spam(message.from_user.id):
        return
    
    buttons = [
        InlineKeyboardButton("✊", callback_data="rock"),
        InlineKeyboardButton("✌️", callback_data="scissors"),
        InlineKeyboardButton("✋", callback_data="paper")
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await message.reply("✊✌️✋ Tanlang:", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data in ["rock", "scissors", "paper"])
async def tqq_result(call: types.CallbackQuery):
    choices = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
    user_choice = choices[call.data]
    bot_choice = random.choice(list(choices.values()))

    result = "🤝 Durrang!"
    win = False
    if (user_choice == "✊" and bot_choice == "✌️") or \
       (user_choice == "✌️" and bot_choice == "✋") or \
       (user_choice == "✋" and bot_choice == "✊"):
        result = "🎉 Siz yutdingiz! +1 ochko"
        win = True
    elif user_choice != bot_choice:
        result = "🤖 Men yutdim!"
    
    update_stats(call.from_user.id, "tqq", win)
    await bot.send_message(call.message.chat.id, f"👤 Siz: {user_choice}\n🤖 Men: {bot_choice}\n🏆 Natija: {result}")

# **Admin komandalari**
@dp.message_handler(commands=['send'])
async def send_to_all(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Sizda bunday buyruqni bajarish huquqi yo'q!")
        return

    text = message.get_args()  # /send dan keyingi matnni olish
    if not text:
        await message.reply("⚠ Iltimos, xabar matnini kiriting:\n/send <matn>")
        return

    # Barcha foydalanuvchilarga xabar yuborish
    sent = 0
    for user_id in active_users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
            time.sleep(0.3)  # 300ms kutish har bir xabardan keyin
        except Exception as e:
            print(f"Xatolik {user_id} ga xabar yuborishda: {e}")

    await message.reply(f"✅ Xabar {sent} ta foydalanuvchiga yuborildi!")

@dp.message_handler(commands=['top'])
async def show_top(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Sizda bunday buyruqni bajarish huquqi yo'q!")
        return
    
    if not user_stats:
        await message.reply("❌ Hali hech qanday statistika to'plalmagan!")
        return
    
    # Foydalanuvchilarni g'alabalar bo'yicha saralash
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['wins'], reverse=True)
    
    top_text = "🏆 Top foydalanuvchilar:\n\n"
    for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.get_chat(user_id)
            username = user.username or user.first_name or str(user_id)
        except:
            username = str(user_id)
        
        top_text += f"{i}. {username} - {stats['wins']} g'alaba\n"
    
    await message.reply(top_text)

# Botni ishga tushurish
if __name__ == "__main__":
    executor.start_polling(dp,skip_updates=True)
