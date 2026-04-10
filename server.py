from flask import Flask, request, jsonify, send_from_directory
import pytesseract
import os
from PIL import Image, ImageFilter
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from ocr_engine import recognize_handwriting
from config import TESSERACT_CMD, TROCR_MODEL_PATH
app = Flask(__name__)

# Налаштування Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Ініціалізація TrOCR 
processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_PATH)
model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_PATH)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
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
        return jsonify({"text": "Файл не отримано"}), 400

    file = request.files["image"]
    
    if file.filename == '':
        return jsonify({"text": "Файл не обрано"}), 400

    # Перевірка формату на сервері
    if not allowed_file(file.filename):
        return jsonify({"text": "Невідповідний тип файлу"}), 400

    model_type = request.form.get("model_type", "printed")

    try:
        temp_path = "temp_upload.jpg"
        file.save(temp_path)
        
        if model_type == "handwritten":
            text = recognize_handwriting(temp_path)
        else:
            img = Image.open(temp_path).convert("RGB")
            img_gray = img.convert("L").filter(ImageFilter.SHARPEN)
            config = "--oem 3 --psm 6"
            text = pytesseract.image_to_string(img_gray, lang="ukr", config=config)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"text": f"Помилка обробки: {str(e)}"}), 500

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