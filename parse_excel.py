import pandas as pd
import json
from collections import defaultdict

# Имя твоего Excel-файла
EXCEL_FILE = "КАТАЛОГ.xlsx"
# Листы, которые нужно обработать (пока только Барселона)
SHEETS_TO_PROCESS = ["Барселона"]  # позже добавишь "Реал Мадрид" и т.д.


def process_sheet(sheet_name, df):
    """
    Преобразует DataFrame листа в список уникальных игроков с вариантами.
    """
    players_dict = defaultdict(list)

    # Проходим по каждой строке
    for _, row in df.iterrows():
        name = str(row["Имя"]).strip()
        position = str(row["Позиция"]).strip(
        ) if pd.notna(row["Позиция"]) else ""
        season = str(row["Сезон"]).strip() if pd.notna(row["Сезон"]) else ""
        stock = int(row["В наличии"]) if pd.notna(row["В наличии"]) else 0
        image = str(row["Фото"]).strip() if pd.notna(row["Фото"]) else ""

        # Сохраняем вариант
        variant = {
            "season": season,
            "stock": stock,
            "image": image
        }

        # Добавляем вариант к игроку
        players_dict[name].append(variant)

    # Формируем итоговый список игроков
    players_list = []
    for name, variants in players_dict.items():
        # Позиция: берём из первого варианта (по условию у всех вариантов она одинаковая)
        # Можно также взять наиболее частую, но для простоты - первый
        first_variant = variants[0]
        # Нам нужно где-то взять позицию. В листе Барселона позиция есть в каждой строке.
        # Но в словаре у нас variants — это список словарей без поля "position".
        # Придётся либо хранить позицию отдельно, либо добавить её в каждый вариант.
        # Логичнее добавить позицию в вариант, но по условию позиция у всех вариантов одинакова,
        # поэтому можно вынести её на уровень игрока.
        # Найдём позицию из первой строки. Для этого нужно получить позицию из строки, соответствующей первому варианту.
        # У нас нет прямой связи строки с вариантом, поэтому проще при построении словаря сохранять и позицию.
        # Переделаем: будем хранить кортеж (позиция, вариант).
        # Но для читаемости кода, проще собрать сначала все строки в список, а потом группировать.
        # Давай перепишем аккуратно.
        pass

    # Лучше переделать логику: сразу собирать строки с нужными полями, а потом группировать.
    # Так как код выше не закончен, напишу правильный вариант ниже.
    # Извини за путаницу, сейчас исправлю.

# Более правильный и простой способ:


def process_sheet_correct(sheet_name, df):
    """
    Группирует строки по имени игрока, возвращает список игроков с вариантами.
    """
    # Словарь: имя -> {"position": позиция, "variants": []}
    players = {}

    for _, row in df.iterrows():
        name = str(row["Имя"]).strip()
        # Позиция может отсутствовать? В Барселоне есть, оставим как есть.
        position = str(row["Позиция"]).strip(
        ) if pd.notna(row["Позиция"]) else ""
        season = str(row["Сезон"]).strip() if pd.notna(row["Сезон"]) else ""
        stock = int(row["В наличии"]) if pd.notna(row["В наличии"]) else 0
        image = str(row["Фото"]).strip() if pd.notna(row["Фото"]) else ""

        variant = {
            "season": season,
            "stock": stock,
            "image": image
        }

        if name not in players:
            # Новый игрок
            players[name] = {
                "name": name,
                "position": position,  # сохраняем позицию из первого вхождения
                "variants": [variant]
            }
        else:
            # У существующего игрока добавляем вариант
            players[name]["variants"].append(variant)
            # Можно проверить, совпадает ли позиция, но по условию не должна отличаться.
            # Если вдруг отличается, можно, например, брать наиболее частую, но пока не заморачиваемся.

    # Превращаем словарь в список
    return list(players.values())


def main():
    # Читаем Excel-файл
    xls = pd.ExcelFile(EXCEL_FILE)

    for sheet_name in SHEETS_TO_PROCESS:
        if sheet_name not in xls.sheet_names:
            print(f"Лист '{sheet_name}' не найден, пропускаем.")
            continue

        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Убираем возможные пустые строки
        df = df.dropna(how='all')

        # Обрабатываем лист
        players = process_sheet_correct(sheet_name, df)

        # Сохраняем в JSON
        # например, барселона.json
        output_filename = f"{sheet_name.lower()}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=2)

        print(
            f"Обработан лист '{sheet_name}': {len(players)} уникальных игроков. Результат в {output_filename}")


if __name__ == "__main__":
    main()
