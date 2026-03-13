from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["name", "city", "rating", "text"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ваше имя"}),
            "city": forms.TextInput(attrs={"placeholder": "Город (необязательно)"}),
            "rating": forms.Select(choices=[(5, "5"), (4, "4"), (3, "3"), (2, "2"), (1, "1")]),
            "text": forms.Textarea(attrs={"placeholder": "Поделитесь впечатлениями", "rows": 5}),
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Оценка должна быть от 1 до 5.")
        return rating
