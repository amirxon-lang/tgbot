import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = "7500083978:AAEFH8tyUpwZSNlex5rmLIBdXmXCkT1cs8I"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# O‘yinlar menyusi tugmalari
menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
menu_buttons.add("❌⭕ X O", "✊✌️✋ TQQ")
menu_buttons.add("🔢 Son topish", "🔠 So‘z topish")

# **START KOMANDASI**
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    start_text = ("🎮 *Mini o‘yinlar botiga xush kelibsiz!*\n\n"
                  "📌 Quyidagi o‘yinlardan birini tanlang:\n\n"
                  "✅ *❌⭕ X O* — Klassik X O o‘yini\n"
                  "✅ *✊✌️✋ TQQ* — Tosh-Qaychi-Qog‘oz\n"
                  "✅ *🔢 Son topish* — Berilgan diapazonda son topish\n"
                  "✅ *🔠 So‘z topish* — Harflarni ketma-ket tanlab so‘z topish\n\n"
                  "ℹ️ Har bir o‘yinda g‘alaba qozonishga harakat qiling! 🎯")
    await message.reply(start_text, parse_mode="Markdown", reply_markup=menu_buttons)

@dp.message_handler(lambda message: not (message.text in ["❌⭕ X O", "✊✌️✋ TQQ", "🔢 Son topish", "🔠 So‘z topish"] or message.text.isdigit()))
async def block_unwanted_messages(message: types.Message):
    await message.delete()
# **X O o‘yini**
games = {}
@dp.message_handler(lambda message: message.text == "❌⭕ X O")
async def xo_game(message: types.Message):
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

    if games[chat_id][move] == "⬜":
        games[chat_id][move] = "❌"
        await show_xo_board(chat_id)

        if check_winner(games[chat_id], "❌"):
            await bot.send_message(chat_id, "🎉 Siz yutdingiz!")
            del games[chat_id]
            return

        bot_move = best_move(games[chat_id])
        games[chat_id][bot_move] = "⭕"
        await show_xo_board(chat_id)

        if check_winner(games[chat_id], "⭕"):
            await bot.send_message(chat_id, "🤖 Bot yutdi!")
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
    return any(board[a] == board[b] == board[c] == player for a, b, c in win_positions)

# **So‘z topish o‘yini**
words = ["smartfon", "blog", "video", "robot", "montaj", "tizim", "funksiya"]

word_games = {}

@dp.message_handler(lambda message: message.text == "🔠 So‘z topish")
async def soz_topish_start(message: types.Message):
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

    await bot.send_message(chat_id, f"So‘z: {word_display}\nHarflarni tanlang:", reply_markup=buttons)

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
            await bot.send_message(chat_id, f"🎉 Siz so‘zni topdingiz! So‘z: {game['word']}")
            del word_games[chat_id]
            return

    await show_guess_board(chat_id)

# **Son topish o‘yini**

# Son topish o‘yini uchun o‘yinlar lug‘ati
guess_games = {}

# Diapazon tanlash tugmalari
@dp.message_handler(lambda message: message.text == "🔢 Son topish")
async def choose_range(message: types.Message):
    buttons = InlineKeyboardMarkup(row_width=3)
    buttons.add(
        InlineKeyboardButton("1-10", callback_data="range_10"),
        InlineKeyboardButton("1-100", callback_data="range_100"),
        InlineKeyboardButton("1-1000", callback_data="range_1000")
    )
    await message.reply("Diapazonni tanlang:", reply_markup=buttons)

# O‘yinni boshlash
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
    
    await bot.send_message(chat_id, f"Men 1 dan {max_value} gacha son o‘yladim. Uni topishga harakat qiling!")

# Foydalanuvchi javobini tekshirish
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
        await message.reply(f"🎉 To‘g‘ri topdingiz! {game['secret_number']} ({game['attempts']} urinishda)")
        del guess_games[chat_id]

# **Tosh-Qaychi-Qog‘oz**
@dp.message_handler(lambda message: message.text == "✊✌️✋ TQQ")
async def tqq_game(message: types.Message):
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
    if (user_choice == "✊" and bot_choice == "✌️") or \
       (user_choice == "✌️" and bot_choice == "✋") or \
       (user_choice == "✋" and bot_choice == "✊"):
        result = "🎉 Siz yutdingiz!"
    elif user_choice != bot_choice:
        result = "🤖 Men yutdim!"

    await bot.send_message(call.message.chat.id, f"👤 Siz: {user_choice}\n🤖 Men: {bot_choice}\n🏆 Natija: {result}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)