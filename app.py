"""Module for area calculation from vector images using Flask and Pillow."""
import os
import subprocess
import base64
import io
import logging # Import logging module for better debugging
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename # Import secure_filename for security
from PIL import Image

# Configure logging for better visibility of errors and info messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CRITICAL FIX: Initialize Flask app correctly
# '__name__' tells Flask where to find static files and templates
app = Flask(__name__)

# مسارات للملفات المؤقتة
UPLOAD_FOLDER = 'uploads'
CONVERTED_IMAGES_FOLDER = 'converted_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_IMAGES_FOLDER'] = CONVERTED_IMAGES_FOLDER

# تأكد من وجود المجلدات عند بدء تشغيل التطبيق
# exist_ok=True يمنع الخطأ إذا كانت المجلدات موجودة بالفعل
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_IMAGES_FOLDER, exist_ok=True)

# دقة التحويل: 100 بكسل/سم = 254 بكسل/بوصة (DPI) تقريبًا
# (1 بوصة = 2.54 سم، لذا 100 بكسل/سم * 2.54 سم/بوصة = 254 بكسل/بوصة)
DPI = 254
# عدد البكسلات المربعة لكل سنتيمتر مربع بناءً على الـ DPI
# (DPI / 2.54)^2 = (254 / 2.54)^2 = 100^2 = 10000
PIXELS_PER_CM_SQUARED = (DPI / 2.54) ** 2

@app.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@app.route('/calculate_area', methods=['POST'])
def calculate_area():
    """Calculate black area in uploaded vector image."""
    # 1. تحقق من وجود الملف في الطلب
    if 'file' not in request.files:
        app.logger.error("No file part in request.")
        return jsonify(
            {"error": "لم يتم رفع أي ملف"}
        ), 400

    file = request.files['file']
    if file.filename == '':
        app.logger.error("No selected file.")
        return jsonify(
            {"error": "لم يتم اختيار ملف"}
        ), 400

    # 2. تحقق من امتداد الملف
    if not (
        file.filename.lower().endswith('.ai')
        or file.filename.lower().endswith('.eps')
    ):
        app.logger.error("Unsupported file extension: %s", file.filename)
        return jsonify(
            {"error": "الرجاء رفع ملف بصيغة AI أو EPS فقط"}
        ), 400

    # 3. تأمين اسم الملف وحفظه مؤقتًا
    # استخدام secure_filename لمنع مشاكل الأمان في اسم الملف
    filename = secure_filename(file.filename)
    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )
    file.save(filepath)
    app.logger.info("File saved temporarily: %s", filepath)

    # Define paths for the converted image
    converted_image_name = os.path.splitext(
        filename
    )[0] + '.jpg'
    converted_image_path = os.path.join(
        app.config['CONVERTED_IMAGES_FOLDER'],
        converted_image_name
    )

    try:
        # 4. استخدام ImageMagick لتحويل ملف الفيكتور إلى JPG
        app.logger.info("Converting %s to %s with DPI %d", filepath, converted_image_path, DPI)
        
        process_result = subprocess.run(
            [
                'convert',
                filepath,
                '-density', str(DPI),
                '-quality', '90',
                '-background', 'white',
                '-flatten',
                converted_image_path
            ],
            check=True,
            capture_output=True,
            text=True
        )
        app.logger.info("ImageMagick stdout: %s", process_result.stdout)
        if process_result.stderr:
            app.logger.warning("ImageMagick stderr: %s", process_result.stderr)
        app.logger.info("Conversion successful for %s", filename)

        # 5. فتح الصورة المحولة باستخدام Pillow
        img = Image.open(
            converted_image_path
        ).convert(
            'RGB'
        )

        # 6. حساب البكسلات السوداء
        black_pixels_count = 0
        width, height = img.size
        black_threshold_sum = 50

        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))
                if r + g + b <= black_threshold_sum:
                    black_pixels_count += 1

        # 7. حساب المساحة بالسنتيمتر المربع
        area_cm2 = black_pixels_count / PIXELS_PER_CM_SQUARED

        # 8. إرسال الصورة المحولة كـ Base64 للواجهة الأمامية
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(
            buffered.getvalue()
        ).decode("utf-8")

        app.logger.info("Area calculated for %s: %.2f cm²", filename, area_cm2)
        return jsonify(
            {
                "area": area_cm2,
                "image_base64": img_str
            }
        )

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode(errors='ignore')
        app.logger.error("ImageMagick conversion failed for %s: %s (stdout: %s)", filename, error_output, e.stdout.decode(errors='ignore'))
        return jsonify(
            {
                "error":
                "فشل في تحويل الملف: تأكد من صحة الملف ووجود ImageMagick. خطأ: "
                + error_output
            }
        ), 500
    except FileNotFoundError:
        app.logger.error(
            "ImageMagick 'convert' command not found. Is it installed and in PATH?"
        )
        return jsonify(
            {
                "error":
                "خطأ في الخادم: أداة تحويل الصور (ImageMagick) غير موجودة. الرجاء الاتصال بالدعم."
            }
        ), 500
    except Exception as e:
        app.logger.error("An unexpected error occurred during processing %s: %s", filename, str(e), exc_info=True)
        return jsonify(
            {
                "error":
                "حدث خطأ غير متوقع أثناء معالجة الملف: " + str(e)
            }
        ), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            app.logger.debug("Deleted temporary input file: %s", filepath)
        if os.path.exists(converted_image_path):
            os.remove(converted_image_path)
            app.logger.debug("Deleted temporary converted image: %s", converted_image_path)

if __name__ == '__main__':
    app.run(debug=True)
