# دليل النشر على PythonAnywhere — منصة حجز أفكار المشاريع

دليل خطوة بخطوة لجعل المنصة متاحة للجميع عبر رابط عام مجاني:
`https://YOURUSERNAME.pythonanywhere.com`

---

## أولاً: رفع الكود إلى GitHub (مرة واحدة)

```powershell
cd "E:\Document\Default Project\idea_booking"
git init
git add .
git commit -m "منصة حجز أفكار المشاريع — الإصدار الأول"
```

أنشئ مستودعاً جديداً على github.com (New Repository) بدون README، ثم:

```powershell
git remote add origin https://github.com/YOURUSERNAME/idea-booking.git
git branch -M main
git push -u origin main
```

> يمكنك بدلاً من ذلك رفع المشروع كملف ZIP من PythonAnywhere (Upload file).

---

## ثانياً: إعداد الحساب على PythonAnywhere

1. سجّل حساباً مجانياً على [pythonanywhere.com](https://www.pythonanywhere.com/)
   (خطة **Beginner** — مجانية بالكامل، لا تحتاج بطاقة ائتمان).
2. من الشريط العلوي اختر **Files → Upload a file** وارفع نسخة ZIP من مجلد
   `idea_booking` (بدون `.venv` وبدون `staticfiles`)، ثم فك ضغطها.
   **أو** من الـ Console نفّذ:
   ```bash
   git clone https://github.com/YOURUSERNAME/idea-booking.git ~/idea_booking
   ```

---

## ثالثاً: البيئة الافتراضية والحزم

افتح **Console** ونفّذ:

```bash
cd ~/idea_booking
python3.12 -m venv venv          # أو أي إصدار Python 3 المتاح لديك
source venv/bin/activate
pip install -r requirements.txt
```

---

## رابعاً: ملف البيئة `.env`

أنشئ الملف `~/idea_booking/.env` (من خلال Files أو الأمر):

```bash
cat > ~/idea_booking/.env <<'EOF'
DJANGO_SECRET_KEY=ولّد-مفتاحا-سريطا-طويلا-عشوائيا-من-هنا
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=YOURUSERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://YOURUSERNAME.pythonanywhere.com
DB_ENGINE=sqlite
DB_NAME=db.sqlite3
SESSION_COOKIE_AGE=28800
EOF
```

**ولّد مفتاحاً سرياً حقيقياً:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> استبدل `YOURUSERNAME` باسم مستخدمك في PythonAnywhere في كل مكان أعلاه.

---

## خامساً: تجهيز قاعدة البيانات

```bash
cd ~/idea_booking
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed --with-supervisor
python manage.py createsuperuser
```

- `seed` ينشئ 6 تصنيفات + 5 أفكار تجريبية + حساب مشرف تجريبي
  (`supervisor` / `supervisor1234`) — **غيّر كلمة المرور بعد أول دخول**.
- `createsuperuser` ينشئ حساب المدير للوحة Django.

---

## سادساً: إعداد تطبيق الويب (Web tab)

1. من الشريط العلوي اختر **Web → Add a new web app**
2. اختر **Manual configuration** (لا تختار OnceXY — سنبني يدوياً)
3. اختر إصدار Python المطابق لبيئتك (مثلاً Python 3.12)
4. بعد إنشائه، افتح ملف **WSGI configuration file** واجعل محتواه التالي:

```python
import sys
import os

project_home = os.path.expanduser('~/idea_booking')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. من نفس صفحة Web، أضف **Static files mapping**:
   | URL | Directory |
   |---|---|
   | `/static/` | `/home/YOURUSERNAME/idea_booking/staticfiles` |

6. اضغط **Reload** (أعلى الصفحة).

---

## سابعاً: التحقق من النشر

افتح `https://YOURUSERNAME.pythonanywhere.com` — يجب أن تظهر قائمة الأفكار.

اختبر السيناريو كاملاً:
1. **إنشاء حساب** طالب جديداً من رابط التسجيل
2. **حجز فكرة** بكتابة أعضاء الفريق
3. الدخول بحساب `supervisor` والموافقة من **لوحة المشرف**
4. التأكد من قفل الفكرة (شارة «محجوزة»)

---

## ثامناً: النشر بعد أي تعديل لاحق

```bash
cd ~/idea_booking
git pull
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

ثم اضغط **Reload** في صفحة Web.

---

## أخطاء شائعة

| المشكلة | الحل |
|---|---|
| `DisallowedHost` | تأكد أن `DJANGO_ALLOWED_HOSTS` يحتوي اسم مستخدمك بالضبط |
| `CSRF verification failed` | تأكد أن `DJANGO_CSRF_TRUSTED_ORIGINS` يبدأ بـ `https://` |
| ملفات CSS غير موجودة | نفّذ `collectstatic --noinput` وتحقق من مسار static mapping |
| `OperationalError: no such table` | نفّذ `python manage.py migrate` |
| الصفحة تعيد توجيه كثيراً | تأكد أن `DJANGO_DEBUG=0` وأن `X-Forwarded-Proto` (مفعّل افتراضياً في الإنتاج) |

## حدود الخطة المجانية

- 100 ثانية معالجة يومياً (تكفي للاستخدام الصفّي)
- 512 ميجابايت للقرص
- نطاق فرعي فقط: `username.pythonanywhere.com`
- outbound HTTP مقيّد (المنصة لا تحتاجه)
