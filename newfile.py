import os
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Bot tokenini o'rnating
API_TOKEN = '8123615072:AAF6rjHqjxR9McBX3UR_2nRvTVPNUDPfjKg'

# Ma'lumotlar fayli
DATA_FILE = 'user_data.json'

# Botni ishga tushirish
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Foydalanuvchi ma'lumotlarini yuklash
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Foydalanuvchi ma'lumotlarini saqlash
def save_user_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# O'yin holatlari
class GameStates(StatesGroup):
    MAIN_MENU = State()
    EXPLORING = State()
    INVENTORY = State()
    SHOP = State()
    UPGRADE = State()
    COMBAT = State()
    MISSION = State()

# Knopkalar
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Sarguzashtga chiqish'))
    kb.add(KeyboardButton('Inventar'), KeyboardButton('Do\'kon'))
    kb.add(KeyboardButton('Missiyalar'), KeyboardButton('Statistika'))
    return kb

def explore_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Oldinga yurish'))
    kb.add(KeyboardButton('Atrofni tekshirish'))
    kb.add(KeyboardButton('Asosiy menyu'))
    return kb

def combat_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Hujum qilish'))
    kb.add(KeyboardButton('Maxsus hujum'), KeyboardButton('Doridan foydalanish'))
    kb.add(KeyboardButton('Qochish'))
    return kb

def mission_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Boshqotirma qo\'riqchi'))
    kb.add(KeyboardButton('Qora jodugar'))
    kb.add(KeyboardButton('Afsonaviy ajdaho'))
    kb.add(KeyboardButton('Asosiy menyu'))
    return kb

# Do'kon buyumlari
shop_items = {
    1: {"name": "Temir qilich", "type": "weapon", "damage": "15-25", "price": 200},
    2: {"name": "Sehrli tayoq", "type": "weapon", "damage": "10-20", "mana": "+5", "price": 300},
    3: {"name": "Charm zirh", "type": "armor", "defense": 10, "price": 150},
    4: {"name": "Hayot eliksiri", "type": "potion", "effect": "+25 HP", "price": 50},
}

# Missiyalar
missions = {
    "beginner": {
        "name": "Boshqotirma qo'riqchi",
        "reward": 100,
        "enemy_hp": 50,
        "enemy_damage": "5-10",
        "description": "Qal'a darvozasini qo'riqlayotgan qo'riqchini yengib, darvozadan kirishga urining."
    },
    "advanced": {
        "name": "Qora jodugar",
        "reward": 300,
        "enemy_hp": 120,
        "enemy_damage": "15-25",
        "description": "Qal'aning maxfiy xonasida yashovchi qora jodugarga qarshi kurashing."
    },
    "secret": {
        "name": "Afsonaviy ajdaho",
        "reward": 1000,
        "enemy_hp": 300,
        "enemy_damage": "30-50",
        "description": "Faqat haqiqiy qahramonlar bu jangda g'alaba qozonishi mumkin!",
        "required_level": 3
    }
}

async def apply_effect(user_id, effect_type, duration):
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    if not user_stats:
        return
    
    if "active_effects" not in user_stats:
        user_stats["active_effects"] = {}
        
    user_stats["active_effects"][effect_type] = duration
    user_data[user_id] = user_stats
    save_user_data(user_data)

async def process_effects(user_id):
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    if not user_stats or not user_stats.get("active_effects"):
        return []
    
    effects = user_stats["active_effects"]
    messages = []
    
    for effect in list(effects.keys()):
        effects[effect] -= 1
        
        if effect == "regeneration":
            heal = 10
            user_stats["hp"] = min(user_stats["max_hp"], user_stats["hp"] + heal)
            messages.append(f"♻️ Regeneratsiya: +{heal} HP")
        
        elif effect == "strength":
            messages.append("💪 Kuch eliksiri faol")
        
        elif effect == "resistance":
            messages.append("🛡️ Qarshilik eliksiri faol")
        
        if effects[effect] <= 0:
            del effects[effect]
            messages.append(f"⏳ {effect} eliksir ta'siri tugadi")
    
    user_data[user_id] = user_stats
    save_user_data(user_data)
    return messages

# Boshlang'ich komanda
@dp.message_handler(commands=['start'], state="*")
async def start_game(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    
    if user_id not in user_data:
        user_data[user_id] = {
            "hp": 100,
            "max_hp": 100,
            "mana": 50,
            "max_mana": 50,
            "gold": 100,
            "level": 1,
            "xp": 0,
            "inventory": [],
            "weapon": {"name": "Oddiy pichoq", "damage": "5-10", "level": 1, "upgrade_cost": 100},
            "armor": {"name": "Yoq", "defense": 0},
            "missions_completed": [],
            "current_mission": None,
            "active_effects": {}
        }
        save_user_data(user_data)
    
    await GameStates.MAIN_MENU.set()
    await message.answer("🎮 Qal'aning Sirli Devori 🏰\nSiz qadimiy qal'a oldidasiz. Qorong'i tushmoqda...", reply_markup=main_menu_kb())

# Asosiy menyu
@dp.message_handler(lambda m: m.text == 'Asosiy menyu', state="*")
async def return_to_main_menu(message: types.Message):
    await GameStates.MAIN_MENU.set()
    await message.answer("Asosiy menyuga qaytdingiz", reply_markup=main_menu_kb())

# Sarguzashtga chiqish
@dp.message_handler(lambda m: m.text == 'Sarguzashtga chiqish', state=GameStates.MAIN_MENU)
async def start_exploring(message: types.Message):
    await GameStates.EXPLORING.set()
    events = [
        "Siz qal'a hovlisida yuribsiz va to'satdan...",
        "Qorong'i tunneldan o'tayotganda...",
        "Qadimiy xonaga kirganingizda..."
    ]
    event = random.choice(events)
    await message.answer(event, reply_markup=explore_kb())

# Explore harakatlari
@dp.message_handler(lambda m: m.text in ['Oldinga yurish', 'Atrofni tekshirish'], state=GameStates.EXPLORING)
async def explore_action(message: types.Message):
    actions = {
        'Oldinga yurish': [
            "Siz qorong'i koridorda oldinga yuryapsiz...",
            "Qadimiy devor yonidan o'tayotganingizda..."
        ],
        'Atrofni tekshirish': [
            "Atrofni diqqat bilan tekshiryapsiz...",
            "Devorlarni qarab chiqyapsiz..."
        ]
    }
    
    result = random.choice(actions[message.text])
    rewards = {
        'gold': random.randint(5, 20),
        'xp': random.randint(1, 5)
    }
    
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    user_stats['gold'] = user_stats.get('gold', 0) + rewards['gold']
    user_stats['xp'] = user_stats.get('xp', 0) + rewards['xp']
    
    # Level up tekshirish
    if user_stats['xp'] >= user_stats['level'] * 100:
        user_stats['level'] += 1
        user_stats['max_hp'] += 20
        user_stats['max_mana'] += 10
        user_stats['hp'] = user_stats['max_hp']
        user_stats['mana'] = user_stats['max_mana']
        level_up_msg = f"\n\n🎉 Tabriklaymiz! Siz {user_stats['level']} darajaga ko'tarildingiz!"
    else:
        level_up_msg = ""
    
    user_data[user_id] = user_stats
    save_user_data(user_data)
    
    await message.answer(
        f"{result}\n"
        f"💰 Topdingiz: {rewards['gold']} gold\n"
        f"⭐ XP: +{rewards['xp']}{level_up_msg}",
        reply_markup=explore_kb()
    )

# Missiyalar
@dp.message_handler(lambda m: m.text == 'Missiyalar', state=GameStates.MAIN_MENU)
async def show_missions(message: types.Message):
    await GameStates.MISSION.set()
    await message.answer("Missiyalarni tanlang:", reply_markup=mission_kb())

@dp.message_handler(lambda m: m.text in ['Boshqotirma qo\'riqchi', 'Qora jodugar', 'Afsonaviy ajdaho'], state=GameStates.MISSION)
async def accept_mission(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    mission_map = {
        'Boshqotirma qo\'riqchi': 'beginner',
        'Qora jodugar': 'advanced',
        'Afsonaviy ajdaho': 'secret'
    }
    
    mission_id = mission_map[message.text]
    
    if mission_id in user_stats.get("missions_completed", []):
        await message.answer("⚠️ Siz bu missiyani allaqachon bajargansiz!", reply_markup=main_menu_kb())
        return
    
    mission = missions[mission_id]
    user_stats["current_mission"] = mission_id
    user_data[user_id] = user_stats
    save_user_data(user_data)
    
    await GameStates.COMBAT.set()
    await message.answer(
        f"⚔️ {mission['name']} ⚔️\n"
        f"{mission['description']}\n\n"
        f"Jang boshlandi!",
        reply_markup=combat_kb()
    )

# Jang logikasi
@dp.message_handler(lambda m: m.text in ['Hujum qilish', 'Maxsus hujum', 'Doridan foydalanish', 'Qochish'], state=GameStates.COMBAT)
async def combat_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    mission_id = user_stats.get("current_mission")
    
    if not mission_id:
        await message.answer("⚠️ Missiya topilmadi!", reply_markup=main_menu_kb())
        return
    
    mission = missions[mission_id]
    combat_stats = {
        "enemy_hp": mission["enemy_hp"],
        "enemy_max_hp": mission["enemy_hp"],
        "enemy_damage": mission["enemy_damage"],
        "reward": mission["reward"]
    }
    
    # Effektlarni qayta ishlash
    effect_msgs = await process_effects(user_id)
    effect_text = "\n".join(effect_msgs) + "\n\n" if effect_msgs else ""
    
    # Harakatlar
    if message.text == 'Hujum qilish':
        min_dmg, max_dmg = map(int, user_stats["weapon"]["damage"].split('-'))
        damage = random.randint(min_dmg, max_dmg)
        
        # Kuch eliksiri tekshirish
        if "strength" in user_stats.get("active_effects", {}):
            damage = int(damage * 1.5)
        
        combat_stats["enemy_hp"] -= damage
        
        # Dushman javobi
        enemy_min, enemy_max = map(int, combat_stats["enemy_damage"].split('-'))
        enemy_damage = random.randint(enemy_min, enemy_max)
        
        # Qarshilik eliksiri tekshirish
        if "resistance" in user_stats.get("active_effects", {}):
            enemy_damage = int(enemy_damage * 0.7)
        
        # Zirh himoyasi
        defense = user_stats["armor"].get("defense", 0)
        user_stats["hp"] -= max(0, enemy_damage - defense)
        
        response = [
            f"{effect_text}",
            f"⚔️ Siz {damage} zarar yetkazdingiz!",
            f"☠️ Dushman sizga {enemy_damage} zarar yetkazdi!"
        ]
    
    elif message.text == 'Maxsus hujum' and user_stats["mana"] >= 10:
        user_stats["mana"] -= 10
        damage = random.randint(20, 30)
        
        if "strength" in user_stats.get("active_effects", {}):
            damage = int(damage * 1.5)
        
        combat_stats["enemy_hp"] -= damage
        
        response = [
            f"{effect_text}",
            f"✨ Maxsus hujum! {damage} zarar yetkazdingiz!",
            f"☠️ Dushman sizga 0 zarar yetkazdi (hujumni blokladingiz)!"
        ]
    
    elif message.text == 'Doridan foydalanish':
        potions = [item for item in user_stats["inventory"] if item.get("type") == "potion"]
        if potions:
            potion = potions[0]
            user_stats["inventory"].remove(potion)
            
            if potion["effect"] == "+25 HP":
                heal = 25
                user_stats["hp"] = min(user_stats["max_hp"], user_stats["hp"] + heal)
                response = [f"{effect_text}🧪 Doridan foydalandingiz! +{heal} HP"]
            else:
                response = [f"{effect_text}⚠️ Bu doridan jangda foydalanib bo'lmaydi!"]
        else:
            response = [f"{effect_text}⚠️ Sizda dorilar yo'q!"]
    
    elif message.text == 'Qochish':
        if random.random() < 0.5:
            user_stats["current_mission"] = None
            user_data[user_id] = user_stats
            save_user_data(user_data)
            
            await GameStates.MAIN_MENU.set()
            await message.answer("🏃‍♂️ Qochishga muvaffaq bo'ldingiz! Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb())
            return
        else:
            response = ["⚠️ Qochishga urinish muvaffaqiyatsiz yakunlandi!"]
    
    # Jang natijasi
    if combat_stats["enemy_hp"] <= 0:
        reward = combat_stats["reward"]
        user_stats["gold"] += reward
        user_stats["missions_completed"].append(mission_id)
        user_stats["current_mission"] = None
        user_stats["xp"] += reward // 10
        
        # Level up tekshirish
        if user_stats["xp"] >= user_stats["level"] * 100:
            user_stats["level"] += 1
            user_stats["max_hp"] += 20
            user_stats["max_mana"] += 10
            user_stats["hp"] = user_stats["max_hp"]
            user_stats["mana"] = user_stats["max_mana"]
            level_up_msg = f"\n🎉 Tabriklaymiz! Siz {user_stats['level']} darajaga ko'tarildingiz!"
        else:
            level_up_msg = ""
        
        user_data[user_id] = user_stats
        save_user_data(user_data)
        
        await GameStates.MAIN_MENU.set()
        await message.answer(
            f"🎉 G'alaba! {mission['name']} missiyasini yakunladingiz!\n"
            f"💰 {reward} gold qozondingiz!{level_up_msg}",
            reply_markup=main_menu_kb()
        )
        return
    
    elif user_stats["hp"] <= 0:
        user_stats["hp"] = user_stats["max_hp"] // 2
        user_stats["current_mission"] = None
        user_data[user_id] = user_stats
        save_user_data(user_data)
        
        await GameStates.MAIN_MENU.set()
        await message.answer(
            "☠️ Siz yutqazdingiz! Ammo qayta tirildingiz.\n"
            "Asosiy menyuga qaytdingiz",
            reply_markup=main_menu_kb()
        )
        return
    
    # Yangi holatni ko'rsatish
    response.extend([
        f"\n❤️ Sizning HP: {user_stats['hp']}/{user_stats['max_hp']}",
        f"✨ Mana: {user_stats['mana']}/{user_stats['max_mana']}",
        f"☠️ Dushman HP: {combat_stats['enemy_hp']}/{mission['enemy_hp']}"
    ])
    
    # Yangilangan ma'lumotlarni saqlash
    user_data[user_id] = user_stats
    save_user_data(user_data)
    
    await message.answer("\n".join(response), reply_markup=combat_kb())

# Inventar
@dp.message_handler(lambda m: m.text == 'Inventar', state="*")
async def show_inventory(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    if not user_stats:
        await message.answer("⚠️ Iltimos, avval /start buyrug'ini bering!", reply_markup=main_menu_kb())
        return
    
    inventory_text = [
        "🎒 Inventar:",
        f"⚔️ Qurol: {user_stats.get('weapon', {}).get('name', 'Yoq')} (Damage: {user_stats.get('weapon', {}).get('damage', '0')})",
        f"🛡️ Zirh: {user_stats.get('armor', {}).get('name', 'Yoq')} (+{user_stats.get('armor', {}).get('defense', 0)} def)",
        "",
        "🧪 Dorilar:"
    ]
    
    if user_stats.get("inventory"):
        for item in user_stats["inventory"]:
            inventory_text.append(f"- {item['name']} ({item.get('effect', 'Nomalum')})")
    else:
        inventory_text.append("⚠️ Inventaringiz bosh")
    
    inventory_text.extend([
        "",
        f"💰 Gold: {user_stats.get('gold', 0)}"
    ])
    
    await message.answer("\n".join(inventory_text), reply_markup=main_menu_kb())

# Do'kon
@dp.message_handler(lambda m: m.text == 'Do\'kon', state=GameStates.MAIN_MENU)
async def open_shop(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    if not user_stats:
        await message.answer("⚠️ Iltimos, avval /start buyrug'ini bering!", reply_markup=main_menu_kb())
        return
    
    shop_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for item_id, item in shop_items.items():
        shop_kb.add(KeyboardButton(f"Sotib olish: {item['name']} - {item['price']} gold"))
    shop_kb.add(KeyboardButton('Asosiy menyu'))
    
    await GameStates.SHOP.set()
    await message.answer(
        f"🏪 Do'kon:\nSizda: {user_stats.get('gold', 0)} gold 💰\n\n"
        "Quyidagi buyumlarni sotib olishingiz mumkin:",
        reply_markup=shop_kb
    )

@dp.message_handler(state=GameStates.SHOP)
async def buy_item(message: types.Message):
    if message.text == 'Asosiy menyu':
        await GameStates.MAIN_MENU.set()
        await message.answer("Asosiy menyuga qaytdingiz", reply_markup=main_menu_kb())
        return
    
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    try:
        item_name = message.text.split(':')[1].split('-')[0].strip()
        item = next((x for x in shop_items.values() if x['name'] == item_name), None)
        
        if not item:
            await message.answer("⚠️ Noto'g'ri buyum!", reply_markup=main_menu_kb())
            return
        
        if user_stats.get("gold", 0) < item["price"]:
            await message.answer("⚠️ Yetarli pul mablag'ingiz yo'q!", reply_markup=main_menu_kb())
            return
        
        user_stats["gold"] -= item["price"]
        
        if item["type"] == "weapon":
            user_stats["weapon"] = {
                "name": item["name"],
                "damage": item["damage"],
                "level": 1,
                "upgrade_cost": 100
            }
        elif item["type"] == "armor":
            user_stats["armor"] = {"name": item["name"], "defense": item["defense"]}
        else:
            user_stats["inventory"].append(item)
        
        user_data[user_id] = user_stats
        save_user_data(user_data)
        
        await message.answer(f"✅ {item['name']} sotib olindi!", reply_markup=main_menu_kb())
        await GameStates.MAIN_MENU.set()
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {str(e)}", reply_markup=main_menu_kb())

# Statistika
@dp.message_handler(lambda m: m.text == 'Statistika', state="*")
async def show_stats(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_stats = user_data.get(user_id, {})
    
    if not user_stats:
        await message.answer("⚠️ Iltimos, avval /start buyrug'ini bering!", reply_markup=main_menu_kb())
        return
    
    stats_text = [
        "📊 Statistika:",
        f"🧙‍♂️ Daraja: {user_stats.get('level', 1)}",
        f"⭐ XP: {user_stats.get('xp', 0)}/{user_stats.get('level', 1) * 100}",
        f"❤️ Hayot: {user_stats.get('hp', 0)}/{user_stats.get('max_hp', 100)}",
        f"✨ Mana: {user_stats.get('mana', 0)}/{user_stats.get('max_mana', 50)}",
        f"💰 Gold: {user_stats.get('gold', 0)}",
        f"🎯 Yakunlangan missiyalar: {len(user_stats.get('missions_completed', []))}"
    ]
    
    await message.answer("\n".join(stats_text), reply_markup=main_menu_kb())

# Botni ishga tushirish
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)