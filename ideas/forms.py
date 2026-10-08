from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, ProjectIdea


class IdeaFilterForm(forms.Form):
    q = forms.CharField(
        label=_("بحث"), required=False,
        widget=forms.TextInput(attrs={"placeholder": _("ابحث بالعنوان أو الوصف...")}),
    )
    category = forms.ModelChoiceField(
        label=_("التصنيف"), queryset=Category.objects.all(),
        required=False, empty_label=_("كل التصنيفات"),
    )
    status = forms.ChoiceField(
        label=_("الحالة"), required=False,
        choices=[("", _("كل الحالات"))] + ProjectIdea.STATUS_CHOICES,
    )


class IdeaForm(forms.ModelForm):
    class Meta:
        model = ProjectIdea
        fields = ["title", "description", "category", "max_members", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("مثال: نظام حجز مختبرات")}),
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": _("اشرح الفكرة، أهدافها، وما يتوقع من الفريق تنفيذه...")}
            ),
            "max_members": forms.NumberInput(attrs={"min": 2, "max": 20}),
        }
        labels = {
            "title": _("عنوان الفكرة"),
            "description": _("وصف الفكرة"),
            "category": _("التصنيف"),
            "max_members": _("أقصى عدد لأعضاء الفريق"),
            "status": _("الحالة"),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def clean_max_members(self):
        value = self.cleaned_data["max_members"]
        if value < 2:
            raise forms.ValidationError(_("الحد الأدنى عضوان."))
        return value

    def save(self, commit=True):
        idea = super().save(commit=False)
        if not idea.supervisor_id and self._user:
            idea.supervisor = self._user
        if commit:
            idea.save()
        return idea
