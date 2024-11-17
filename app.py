from flask import Flask, request, send_file, render_template
from PIL import Image
import os
import zipfile
from io import BytesIO
import shutil  # Для удаления папок

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

# Убедимся, что папки существуют
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Размеры для генерации
ICON_SIZES = {
    "Windows": [16, 24, 32, 48, 256],
    "Linux": [16, 24, 48, 96],
    "iOS 6": [29, 50, 57, 58, 72, 100, 114, 144, 1024],
    "iOS 7": [29, 40, 58, 60, 76, 80, 120, 152, 1024],
    "Android": [36, 48, 72, 96, 512],
    "Custom": [64, 128, 256, 512, 1024]  # Дополнительные размеры
}


def generate_icons(image_path, selected_sizes, output_folder):
    """Генерация иконок заданных размеров"""
    with Image.open(image_path) as img:
        for platform, sizes in ICON_SIZES.items():
            platform_folder = os.path.join(output_folder, platform)
            os.makedirs(platform_folder, exist_ok=True)
            for size in sizes:
                if size in selected_sizes:
                    resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized_img.save(os.path.join(platform_folder, f"icon_{size}x{size}.png"))


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'sizes' not in request.form:
            return "No file or sizes selected", 400

        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        # Получение выбранных размеров от пользователя
        selected_sizes = list(map(int, request.form.getlist('sizes')))

        # Сохранение загруженного файла
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Папка для вывода
        output_path = os.path.join(OUTPUT_FOLDER, file.filename.split('.')[0])
        os.makedirs(output_path, exist_ok=True)

        # Генерация иконок
        generate_icons(filepath, selected_sizes, output_path)

        # Архивируем результаты
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)

        # Удаляем временные файлы
        os.remove(filepath)  # Удаляем загруженный файл
        shutil.rmtree(output_path)  # Удаляем папку с сгенерированными иконками

        # Отправляем архив пользователю
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='icons.zip')

    # Передаем размеры и платформы в шаблон
    return render_template('upload.html', icon_sizes=ICON_SIZES)


if __name__ == '__main__':
    app.run(debug=True)
