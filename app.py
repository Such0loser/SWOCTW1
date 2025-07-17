"""Module for area calculation from vector images using Flask and Pillow."""
import os
import subprocess
import base64
import io
from flask import Flask, request, render_template, jsonify
from PIL import Image

app = Flask(app)

# مسارات للملفات المؤقتة
UPLOAD_FOLDER = 'uploads'
CONVERTED_IMAGES_FOLDER = 'converted_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_IMAGES_FOLDER'] = CONVERTED_IMAGES_FOLDER

# تأكد من وجود المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_IMAGES_FOLDER, exist_ok=True)

# دقة التحويل: 100 بكسل/سم = 254 بكسل/بوصة (DPI) تقريبًا
# (1 بوصة = 2.54 سم، لذا 100 بكسل/سم * 2.54 سم/بوصة = 254 بكسل/بوصة)
DPI = 254
PIXELS_PER_CM_SQUARED = 100 * 100 # 10000 بكسل مربع لكل سم مربع
@app.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')
@app.route('/calculate_area', methods=['POST'])
def calculate_area():
    """Calculate black area in uploaded vector image."""
    if 'file' not in request.files:
        return jsonify(
            {"error": "لم يتم رفع أي ملف"}
        ), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(
            {"error": "لم يتم اختيار ملف"}
        ), 400

    if not (
        file.filename.lower().endswith('.ai')
        or file.filename.lower().endswith('.eps')
    ):
        return jsonify(
            {"error": "الرجاء رفع ملف بصيغة AI أو EPS فقط"}
        ), 400

    # حفظ الملف مؤقتًا
    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file.filename
    )
    file.save(filepath)

    converted_image_name = os.path.splitext(
        file.filename
    )[0] + '.jpg'
    converted_image_path = os.path.join(
        app.config['CONVERTED_IMAGES_FOLDER'],
        converted_image_name
    )

    try:
        # استخدام ImageMagick لتحويل ملف الفيكتور إلى JPG
        # -density يحدد الدقة بالبكسل/بوصة
        # -quality يحدد جودة JPG (يمكن تعديلها)
        # -background white -flatten لضمان خلفية بيضاء ودمج الطبقات
        subprocess.run(
            [
                'convert',
                filepath,
                '-density',
                str(DPI),
                '-quality',
                '90',
                '-background',
                'white',
                '-flatten',
                converted_image_path
            ],
            check=True
        )

        # فتح الصورة المحولة باستخدام Pillow
        img = Image.open(
            converted_image_path
        ).convert(
            'RGB'
        )  # تأكد من التحويل لـ RGB للتعامل مع الألوان

        # حساب البكسلات السوداء
        black_pixels_count = 0
        width, height = img.size

        # تعريف عتبة اللون الأسود (يمكن تعديلها حسب درجة "الأسود" في ملفاتك)
        # إذا كان البكسل مظلماً جداً (قريب من الأسود)، اعتبره أسود.
        # مثلاً، مجموع قيم RGB لا يتجاوز 50 (من 255*3 = 765)
        black_threshold_sum = 50

        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))
                # إذا كان البكسل أسود أو قريباً جداً من الأسود
                if r + g + b <= black_threshold_sum:
                    black_pixels_count += 1

        # حساب المساحة بالسنتيمتر المربع
        area_cm2 = black_pixels_count / PIXELS_PER_CM_SQUARED

        # إرسال الصورة المحولة كـ Base64 للواجهة الأمامية
        # هذا يسمح بعرضها مباشرة دون الحاجة لحفظها كملف عام
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(
            buffered.getvalue()
        ).decode("utf-8")

        return jsonify(
            {
                "area": area_cm2,
                "image_base64": img_str
            }
        )

    except subprocess.CalledProcessError as e:
        app.logger.error(
            "ImageMagick conversion failed: %s",
            e.stderr.decode()
        )
        return jsonify(
            {
                "error":
                "فشل في تحويل الملف: تأكد من صحة الملف ووجود ImageMagick. خطأ: "
                + e.stderr.decode()
            }
        ), 500
    except FileNotFoundError:
        app.logger.error(
            "ImageMagick 'convert' command not found. Is it installed and in PATH?"
        )
        return jsonify(
            {
                "error":
                "خطأ في الخادم: أداة تحويل الصور غير موجودة. الرجاء الاتصال بالدعم."
            }
        ), 500
    except subprocess.SubprocessError as e:
        app.logger.error(
            "Subprocess error: %s",
            str(e)
        )
        return jsonify(
            {
                "error":
                "حدث خطأ أثناء المعالجة: " + str(e)
            }
        ), 500
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(converted_image_path):
            os.remove(converted_image_path)
        if os.path.exists(converted_image_path):
            os.remove(converted_image_path)            