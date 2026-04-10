const dropArea = document.getElementById("dropArea");
const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const form = document.getElementById("uploadForm");
const result = document.getElementById("result");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");

// Клік — відкриття вибору файлу
dropArea.addEventListener("click", () => imageInput.click());

// Валідація типу файлу
function validateFile(file) {
    const allowedExtensions = /(\.jpg|\.jpeg|\.png)$/i;
    if (!allowedExtensions.exec(file.name)) {
        alert('Невідповідний тип файлу! Будь ласка, завантажте зображення у форматі .png або .jpg');
        imageInput.value = "";
        preview.src = "";
        preview.style.display = "none";
        dropArea.classList.remove("active");
        return false;
    }
    return true;
}

imageInput.addEventListener("change", () => {
    if (imageInput.files.length > 0) {
        const file = imageInput.files[0];
        if (validateFile(file)) {
            showPreview(file);
        }
    }
});

// Drag & drop
dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropArea.classList.add("dragover");
});

dropArea.addEventListener("dragleave", () => {
    dropArea.classList.remove("dragover");
});

dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropArea.classList.remove("dragover");

    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];

        if (validateFile(file)) {
            const dt = new DataTransfer();
            dt.items.add(file);
            imageInput.files = dt.files;
            showPreview(file);
        }
    }
});

// Показ превʼю
function showPreview(file) {
    const reader = new FileReader();
    reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = "block";
        clearBtn.style.display = "inline-block";
    };
    reader.readAsDataURL(file);
}

// Видалення зображення
clearBtn.addEventListener("click", () => {
    preview.src = "";
    preview.style.display = "none";

    imageInput.value = "";
    result.textContent = "";
    copyBtn.style.display = "none";
    clearBtn.style.display = "none";
});

// Обробка сабміту
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (imageInput.files.length === 0) return;

    result.value = "Зачекайте, обробка зображення...";
    copyBtn.style.display = "none";

    const modelType = document.querySelector('input[name="model_type"]:checked').value;
    let formData = new FormData();
    formData.append("image", imageInput.files[0]);
    formData.append("model_type", modelType);

    // Контролер для скасування запиту через довгий час
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 18000000); 

    try {
        let response = await fetch("/upload", {
            method: "POST",
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        let data = await response.json();
        result.value = data.text || "Текст не знайдено.";
        if (data.text) showCopyButton();

    } catch (error) {
        if (error.name === 'AbortError') {
            result.value = "Помилка: Час очікування вичерпано. Модель працює занадто повільно.";
        } else {
            result.value = "Помилка зв'язку з сервером.";
            console.error(error);
        }
    }
});

function showCopyButton() {
    copyBtn.style.display = "inline-block";
}

// Логіка копіювання
copyBtn.addEventListener("click", () => {
    const textToCopy = result.value; 
    if (!textToCopy) return;

    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = "Скопійовано! ✓";
            copyBtn.style.background = "#1e7e34";
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.style.background = "#28a745";
            }, 2000);
        });
});