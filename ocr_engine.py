import torch
import easyocr
import os
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from config import TROCR_MODEL_PATH, DEVICE

# 1. Налаштування шляхів та пристрою
model_path = TROCR_MODEL_PATH
device = DEVICE

def recognize_handwriting(image_path):
    # 2. Завантаження моделей
    processor = TrOCRProcessor.from_pretrained(model_path)
    model = VisionEncoderDecoderModel.from_pretrained(model_path).to(device)
    reader = easyocr.Reader(["uk"], gpu=torch.cuda.is_available())
    
    def process_single_line_with_your_trocr(cropped_img):
        # Конвертування в RGB для моделі
        pixel_values = processor(
            images=cropped_img.convert("RGB"), return_tensors="pt"
        ).pixel_values.to(device)

        generated_ids = model.generate(
            pixel_values,
            max_length=64,
            num_beams=1,
            early_stopping=False,
            no_repeat_ngram_size=0,
            length_penalty=1.0,  # Штраф за занадто короткі відповіді
        )

        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return str(text + "\n\n")

    # 1. Ініціалізація
    # Працює тільки як детектор
    reader = easyocr.Reader(["uk"], gpu=torch.cuda.is_available())
    output_folder = "cropped_full_width_lines"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 2. Відкриття фото
    original_img = Image.open(image_path).convert("RGB")
    orig_w, orig_h = original_img.size

    # 3. ДЕТЕКЦІЯ ОКРЕМИХ СЛІВ ( paragraph=False )
    raw_results = reader.readtext(image_path, paragraph=False)

    if not raw_results:
        print("Текст не знайдено.")
        exit()

    # 4. АЛГОРИТМ ГРУПУВАННЯ В РЯДКИ
    lines = []

    # Фільтруємо дрібне сміття (пунктирні лінії тощо)
    raw_results = [res for res in raw_results if (max([p[1] for p in res[0]]) - min([p[1] for p in res[0]])) > 10]

    # Сортування всіх знайдених слів
    raw_results.sort(key=lambda x: x[0][0][1])

    if raw_results:
        # Початкові дані для першого слова
        first_word_y = [p[1] for p in raw_results[0][0]]
        curr_line_y_min = min(first_word_y)
        curr_line_y_max = max(first_word_y)
        
        # Якщо наступне слово нижче/вище більше ніж на 5 пікс - це новий рядок.
        y_overlap_ths = 5 

        for i in range(1, len(raw_results)):
            word_bbox = raw_results[i][0]
            w_y_min = min([p[1] for p in word_bbox])
            w_y_max = max([p[1] for p in word_bbox])
            
            # Перевірка, чи центр нового слова лежить в межах поточного рядка
            word_center_y = (w_y_min + w_y_max) / 2
            
            if curr_line_y_min - y_overlap_ths <= word_center_y <= curr_line_y_max + y_overlap_ths:
                curr_line_y_min = min(curr_line_y_min, w_y_min)
                curr_line_y_max = max(curr_line_y_max, w_y_max)
            else:
                lines.append({'y_min': curr_line_y_min, 'y_max': curr_line_y_max})
                # Початок нового рядка
                curr_line_y_min = w_y_min
                curr_line_y_max = w_y_max
                
        # Додалення останнього знайденого рядка
        lines.append({'y_min': curr_line_y_min, 'y_max': curr_line_y_max})

    # Видалення дублікатів та надто тонких смужок
    unique_lines = []
    for line in lines:
        if (line['y_max'] - line['y_min']) > 15: # Рядок має бути вищим за 15 пікс
            unique_lines.append(line)

    final_text = []

    # 5. НАРІЗАННЯ НА ВСЮ ШИРИНУ
    for i, line_coords in enumerate(unique_lines):
        y_min = line_coords['y_min']
        y_max = line_coords['y_max']
        
        pad_y = 10    
        top = max(0, int(y_min - pad_y))
        bottom = min(orig_h, int(y_max + pad_y))
        left = 0
        right = orig_w
        
        # Вирізання смужки на всю ширину
        cropped_img = original_img.crop((left, top, right, bottom))
        
        # Збереження
        save_path = os.path.join(output_folder, f"full_width_line_{i}.jpg")
        cropped_img.save(save_path)
        
        # Виклик моделі
        line_text = process_single_line_with_your_trocr(cropped_img)
        final_text.append(line_text)

    return final_text