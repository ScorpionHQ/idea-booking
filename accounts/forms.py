from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label=_("الاسم الكامل"), max_length=150, widget=forms.TextInput(
            attrs={"placeholder": _("مثال: علي حسن محمد")}
        )
    )
    university_number = forms.CharField(
        label=_("الرقم الجامعي"), max_length=30, required=False,
        widget=forms.TextInput(attrs={"placeholder": _("مثال: 20231234")})
    )
    email = forms.EmailField(
        label=_("البريد الإلكتروني"), required=False,
        widget=forms.EmailInput(attrs={"placeholder": "name@example.com"})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "university_number", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("اسم المستخدم")
        self.fields["username"].help_text = _(
            "حروف وأرقام و @/./+/-/_ فقط — مطلوب لتسجيل الدخول."
        )
        self.fields["password1"].label = _("كلمة المرور")
        self.fields["password2"].label = _("تأكيد كلمة المرور")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_STUDENT
        if commit:
            user.save()
        return user
