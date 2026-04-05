import torch
import os

# --- Налаштування пристрою ---
# Автоматичне визначення: CUDA (якщо є GPU) або CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- Шляхи до моделей ---

# Шлях до вашої навченої моделі TrOCR (Українська мова)
TROCR_MODEL_PATH = r"C:\Program Files\trocr-ukrainian"

# Шлях до виконуваного файлу Tesseract OCR
# Переконайтеся, що файл tesseract.exe знаходиться саме за цією адресою
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Налаштування детекції (EasyOCR) ---
# Мови, які використовуватиме EasyOCR для пошуку координат тексту
EASYOCR_LANGS = ['uk']

# --- Налаштування обробки зображень ---
# Папка для збереження тимчасових нарізаних рядків (для дебагу)
OUTPUT_FOLDER = "cropped_full_width_lines"

# Створення папки, якщо її не існує
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- Параметри алгоритму групування рядків ---
Y_OVERLAP_THS = 5  # Поріг вертикального перекриття пікселів
LINE_MIN_HEIGHT = 15  # Мінімальна висота рядка, щоб ігнорувати шум/пунктир