import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def parse_keyboard_from_text(text: str) -> str:
    """Парсит текст в формате [Текст кнопки](url) и возвращает JSON для БД."""
    keyboard = []
    lines = text.strip().split('\n')
    for line in lines:
        row = []
        buttons = line.split('|')
        for button_text in buttons:
            button_text = button_text.strip()
            if ']' in button_text and '(' in button_text:
                text_part = button_text[button_text.find('[')+1:button_text.find(']')]
                url_part = button_text[button_text.find('(')+1:button_text.find(')')]
                row.append({'text': text_part, 'url': url_part})
        if row:
            keyboard.append(row)
    return json.dumps(keyboard, ensure_ascii=False) if keyboard else None

def build_keyboard_from_json(keyboard_json: str) -> InlineKeyboardMarkup:
    """Собирает InlineKeyboardMarkup из JSON строки."""
    if not keyboard_json:
        return None
    keyboard_data = json.loads(keyboard_json)
    markup = InlineKeyboardMarkup()
    for row_data in keyboard_data:
        row = [InlineKeyboardButton(text=button['text'], url=button['url']) for button in row_data]
        markup.row(*row)
    return markup