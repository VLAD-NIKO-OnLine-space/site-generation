import random
from bs4 import BeautifulSoup
from pathlib import Path
# Массив случайных значений для атрибута alt
alt_values = [
    "Online casino",
    "Casino slots",
    "Jackpot win",
    "Fast payouts",
    "Bonus spins",
    "Live dealer",
    "Secure gaming",
    "Slot reels",
    "Casino games",
    "Card table",
    "Big win",
    "Roulette wheel",
    "Blackjack hand",
    "Vegas vibes",
    "Lucky spin",
    "Mobile casino",
    "Free spins",
    "Casino bonus",
    "Poker chips",
    "Exclusive games"
]

# дай мне 25 alt для картирок по футбольной тематике, состтоящие из максимум 2х слов, в виде массива



# Загрузка локального HTML-файла
SCRIPT_DIR = Path(__file__).resolve().parent
file_path = SCRIPT_DIR / "index.html"

# Чтение HTML-файла
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Парсинг HTML с использованием BeautifulSoup
soup = BeautifulSoup(html_content, 'lxml')

# Найдём все теги <img> и добавим alt, если его нет
images = soup.find_all('img')

for img in images:
    random_alt = random.choice(alt_values)
    img['alt'] = random_alt

# Записываем обновлённый HTML обратно в файл
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

print("HTML file updated successfully.")
