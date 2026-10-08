from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from ideas.models import Category, ProjectIdea

CATEGORIES = [
    "ويب وتطبيقات",
    "ذكاء اصطناعي",
    "شبكات وأمن",
    "قواعد بيانات",
    "هندسة برمجيات",
    " إنترنت الأشياء",
]

IDEAS = [
    {
        "title": "نظام حجز مختبرات الجامعة",
        "description": (
            "منصة تتيح للطلبة حجز مقاعد المختبرات حسب المواعيد المتاحة، "
            "مع لوحة تحكم لإدارة المختبرات وتقارير عن الإشغال."
        ),
        "category": "ويب وتطبيقات",
        "max_members": 4,
    },
    {
        "title": "مساعد أكاديمي بالذكاء الاصطناعي",
        "description": (
            "تطبيق يجيب عن أسئلة الطلبة الأكاديمية اعتماداً على محتوى المقررات، "
            "مع نظام تقييم للإجابات ومصادر مرجعية."
        ),
        "category": "ذكاء اصطناعي",
        "max_members": 5,
    },
    {
        "title": "نظام كشف التسلل للشبكات الجامعية",
        "description": (
            "أداة تراقب حركة الشبكة وتنذر عند رصد أنماط هجومية شائعة، "
            "مع لوحة عرض للتنبيهات وسجل الأحداث."
        ),
        "category": "شبكات وأمن",
        "max_members": 3,
    },
    {
        "title": "منصة إدارة مشاريع التخرج",
        "description": (
            "نظام يتابع مراحل مشروع التخرج: التسجيل، اجتماعات المشرف، "
            "التقارير الدورية، وتسليم المخرجات النهائية."
        ),
        "category": "هندسة برمجيات",
        "max_members": 5,
    },
    {
        "title": "تتبع درجات المركبات (expiry-track)",
        "description": (
            "تطبيق يذكّر أصحاب المركبات بمواعيد تجديد الرسوم والفحص الدوري "
            "والتأمين مع تنبيهات متكررة."
        ),
        "category": "ويب وتطبيقات",
        "max_members": 3,
    },
]


class Command(BaseCommand):
    help = "تهيئة البيانات الأولية: تصنيفات + أفكار تجريبية + حساب مشرف (اختياري)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-supervisor",
            action="store_true",
            help="إنشاء حساب مشرف تجريبي (supervisor / supervisor1234)",
        )
        parser.add_argument(
            "--with-student",
            action="store_true",
            help="إنشاء حساب طالب تجريبي (student / student1234)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for name in CATEGORIES:
            _, was_created = Category.objects.get_or_create(
                name=name.strip(), defaults={"slug": ""}
            )
            created += int(was_created)
        self.stdout.write(f"التصنيفات: {Category.objects.count()} (جديد: {created})")

        supervisor = None
        if options["with_supervisor"]:
            supervisor, was_created = User.objects.get_or_create(
                username="supervisor",
                defaults={
                    "first_name": "د. مشرف تجريبي",
                    "role": User.ROLE_SUPERVISOR,
                },
            )
            if was_created:
                supervisor.set_password("supervisor1234")
                supervisor.save(update_fields=["password"])
                self.stdout.write(
                    self.style.SUCCESS("تم إنشاء مشرف: supervisor / supervisor1234")
                )

        if options["with_student"]:
            student, was_created = User.objects.get_or_create(
                username="student",
                defaults={
                    "first_name": "طالب تجريبي",
                    "role": User.ROLE_STUDENT,
                    "university_number": "20230001",
                },
            )
            if was_created:
                student.set_password("student1234")
                student.save(update_fields=["password"])
                self.stdout.write(
                    self.style.SUCCESS("تم إنشاء طالب: student / student1234")
                )

        ideas_created = 0
        for item in IDEAS:
            category = Category.objects.filter(name=item["category"].strip()).first()
            if not category:
                continue
            _, was_created = ProjectIdea.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "category": category,
                    "max_members": item["max_members"],
                    "supervisor": supervisor,
                    "status": ProjectIdea.STATUS_APPROVED,
                },
            )
            ideas_created += int(was_created)
        self.stdout.write(
            f"الأفكار: {ProjectIdea.objects.count()} (جديد: {ideas_created})"
        )
        self.stdout.write(self.style.SUCCESS("اكتملت التهيئة."))
