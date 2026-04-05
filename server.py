from flask import Flask, request, jsonify, send_from_directory
import pytesseract
from PIL import Image, ImageFilter
from transformers import TrOCRProcessor, VisionEncoderDecoderModel # Потрібно встановити: pip install transformers torch
from ocr_engine import recognize_handwriting
from config import TESSERACT_CMD, TROCR_MODEL_PATH
app = Flask(__name__)

# Налаштування Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Ініціалізація TrOCR (завантажиться при першому запуску)
processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_PATH)
model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_PATH)

def process_trocr(image):
    try:
        # Перевірка, що зображення в RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Контроль тензорів
        inputs = processor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values
        
        generated_ids = model.generate(pixel_values, max_new_tokens=64, num_beams=1) 
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return generated_text
    except Exception as e:
        return f"Помилка моделі: {str(e)}"
    
@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"text": "Файл не отримано"})

    file = request.files["image"]
    model_type = request.form.get("model_type", "printed")

    try:
        # Тимчасове збереження файлу на диск
        # Це важливо, бо ocr_engine очікує шлях до файлу для OpenCV та EasyOCR
        temp_path = "temp_upload.jpg"
        file.save(temp_path)
        
        if model_type == "handwritten":
            text = recognize_handwriting(temp_path)
        else:
            # Для Tesseract - відкриття через PIL
            img = Image.open(temp_path).convert("RGB")
            img_gray = img.convert("L").filter(ImageFilter.SHARPEN)
            config = "--oem 3 --psm 6"
            text = pytesseract.image_to_string(img_gray, lang="ukr", config=config)

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"text": f"Помилка обробки: {str(e)}"})

# Головна сторінка
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# Маршрут для скриптів
@app.route("/script.js")
def js():
    return send_from_directory(".", "script.js")

# Маршрут для стилів
@app.route("/style.css")
def css():
    return send_from_directory(".", "style.css")

if __name__ == "__main__":
    app.run(debug=True)