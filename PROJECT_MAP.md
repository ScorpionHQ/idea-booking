# PROJECT_MAP — منصة حجز أفكار المشاريع الجامعية

منصة ويب بالعربية (RTL) تتيح للطلبة تصفح أفكار المشاريع وحجزها لفرقهم
بكتابة أعضاء الفريق يدوياً، وللمشرفين إدارة الأفكار والموافقة على الحجوزات.
الهدف: نشرها على PythonAnywhere المجاني ليتمكن الجميع من الدخول.

تاريخ الإنشاء: 2026

---

## 1. المتطلبات من المستخدم

1. **حجز الفكرة مع فريق** — الطالب يحجز فكرة ويكتب أعضاء فريقه.
2. **كتابة أعضاء الفريق يدوياً** — اسم + رقم جامعي لكل عضو (بدون حسابات).
3. **موقع ويب كامل قابل للنشر** — الجميع يدخل عبر رابط عام + تسجيل ذاتي مفتوح.

## 2. البنية

```
idea_booking/
├── config/          إعدادات Django (env + إنتاج + عربي RTL)
├── accounts/        User مخصص بالأدوار + تسجيل ذاتي
├── ideas/           Category + ProjectIdea + صفحات العرض والحجز
├── bookings/        Booking + BookingMember + خدمات العمل
├── core/            أمر seed (بيانات أولية)
├── templates/       قوالب عربية RTL
├── static/          CSS + JS (أعضاء ديناميكيون)
├── DEPLOY.md        دليل نشر عربي على PythonAnywhere
└── requirements.txt Django 6.1.1 + whitenoise + waitress
```

## 3. النماذج

| النموذج | ملاحظات |
|---|---|
| `accounts.User` | AbstractUser + `role` (طالب/مشرف/مدير) + رقم جامعي |
| `ideas.Category` | تصنيفات (ويب، ذكاء اصطناعي، شبكات...) |
| `ideas.ProjectIdea` | عنوان، وصف، تصنيف، مشرف، `max_members`، الحالة |
| `bookings.Booking` | حجز: فكرة + طالب + حالة + قيود فريدة |
| `bookings.BookingMember` | عضو فريق يُكتب يدوياً (اسم + رقم جامعي) |

**حالات الفكرة**: `approved` (متاحة) → `booked` (محجوزة) → `closed` (مغلقة)
**حالات الحجز**: `pending` → `approved` / `rejected` / `cancelled`

## 4. قواعد العمل (bookings/services.py)

- حجز واحد **نشط** لكل فكرة (قيد فريد في قاعدة البيانات).
- حجز واحد **نشط** لكل طالب (قيد فريد في قاعدة البيانات).
- `1 (الحائز) + الأعضاء ≤ max_members`.
- لا حجز على فكرة مغلقة.
- **الاعتماد** = قفل الفكرة (`approved` → `booked`).
- **الرفض/الإلغاء** = تحرير الفكرة (`booked` → `approved`).
- الموافقة/الرفض: مشرف الفكرة أو المدير فقط (يتحقق `services` + صلاحيات).

## 5. الصفحات

| الرابط | الوصف |
|---|---|
| `/` | قائمة الأفكار + بحث + تصفية (تصنيف/حالة) |
| `/add/` | إضافة فكرة (مشرفون فقط) |
| `/<slug>/` | تفاصيل + فريق حاضر + نموذج حجز بأعضاء ديناميكيون (JS) |
| `/bookings/mine/` | حجوزاتي + إلغاء |
| `/supervisor/` | لوحة المشرف: الحجوزات المعلقة (اعتماد/رفض) + أفكاره |
| `/accounts/register|login|logout/` | مصادقة مفتوحة |
| `/admin/` | لوحة Django |

## 6. قرارات تقنية (ADR مختصر)

- **Django 6.1.1 + Templates** (لا REST/SPA) — أبسط للنشر على PythonAnywhere.
- **SQLite** — كافية ومنصة تحفظها على قرصها الدائم (مختلفاً عن Render).
- **WhiteNoise** — ملفات static بدون إعداد خادم إضافي.
- **`<str:slug>`** بدلاً من `<slug:slug>` — لدعم الأسماء العربية.
- **CSRF_TRUSTED_ORIGINS + HTTPS redirect** عند `DEBUG=0` للإنتاج خلف بروكسي PythonAnywhere.

## 7. الأوامر المفيدة

```bash
python manage.py runserver                 # التطوير
python manage.py test                      # 27 اختباراً
python manage.py seed --with-supervisor --with-student   # بيانات أولية
python manage.py migrate && python manage.py collectstatic --noinput
```

حسابات تجريبية بعد `seed`:
- مشرف: `supervisor` / `supervisor1234`
- طالب: `student` / `student1234`

## 8. النشر

انظر `DEPLOY.md` — دليل عربي خطوة بخطوة على PythonAnywhere المجاني
(رفع كود → venv → `.env` → migrate → WSGI → Reload).
