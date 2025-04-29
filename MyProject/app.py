from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'  # استخدم مفتاح أقوى في بيئة الإنتاج
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)

# نموذج قاعدة البيانات
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(200), nullable=False)

# دالة للتحقق من أنواع الملفات المسموح بها
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# إنشاء قاعدة البيانات والجداول
with app.app_context():
    if not os.path.exists('files.db'):
        db.create_all()
        print("تم إنشاء قاعدة البيانات والجداول بنجاح!")
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"تم إنشاء مجلد الرفع: {app.config['UPLOAD_FOLDER']}")

# المسارات
@app.route('/')
def index():
    files = File.query.all()
    return render_template('index.html', files=files)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار أي ملف.')
            return redirect(request.url)

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            flash('الرجاء اختيار ملف لرفعه.')
            return redirect(request.url)

        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            # حفظ الملف في قاعدة البيانات
            new_file = File(filename=filename, filepath=filepath)
            db.session.add(new_file)
            db.session.commit()

            flash('تم رفع الملف بنجاح!')
            return redirect(url_for('admin'))
        else:
            flash('نوع الملف غير مسموح.')
            return redirect(request.url)

    files = File.query.all()
    return render_template('admin.html', files=files)

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    # حذف الملف من المجلد
    if os.path.exists(file.filepath):
        os.remove(file.filepath)

    # حذف الملف من قاعدة البيانات
    db.session.delete(file)
    db.session.commit()
    flash('تم حذف الملف بنجاح!')
    return redirect(url_for('admin'))

@app.route('/edit/<int:file_id>', methods=['GET', 'POST'])
def edit_file(file_id):
    file = File.query.get_or_404(file_id)
    if request.method == 'POST':
        new_filename = request.form['filename']
        if new_filename:
            # تحديث اسم الملف في النظام
            new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(new_filename))
            os.rename(file.filepath, new_filepath)

            # تحديث اسم الملف في قاعدة البيانات
            file.filename = new_filename
            file.filepath = new_filepath
            db.session.commit()
            flash('تم تعديل الملف بنجاح!')
            return redirect(url_for('admin'))
        else:
            flash('اسم الملف لا يمكن أن يكون فارغًا.')
    return render_template('edit.html', file=file)

@app.route('/download/<int:file_id>')
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    return send_file(file.filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)