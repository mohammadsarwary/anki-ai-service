from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate

from apps.ai.schemas import LEVELS
from apps.decks.models import Card


DIFFICULTY_CHOICES = [("", "No difficulty"), *Card.DIFFICULTY_CHOICES]


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid email or password.")
        return cleaned_data


class CardForm(forms.Form):
    front = forms.CharField(max_length=1000)
    back = forms.CharField(widget=forms.Textarea)
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, required=False)
    tags = forms.CharField(required=False)
    example_sentence = forms.CharField(required=False, widget=forms.Textarea)
    pronunciation = forms.CharField(max_length=255, required=False)

    def clean_tags(self):
        raw = self.cleaned_data.get("tags") or ""
        tags = [tag.strip() for tag in raw.split(",")]
        return [tag for tag in tags if tag]


class CardImportForm(forms.Form):
    import_file = forms.FileField(required=False)
    pasted_cards = forms.CharField(required=False, widget=forms.Textarea)
    default_difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, required=False)
    default_tags = forms.CharField(required=False)
    skip_duplicates = forms.BooleanField(required=False, initial=True)

    def clean(self):
        cleaned_data = super().clean()
        import_file = cleaned_data.get("import_file")
        pasted_cards = (cleaned_data.get("pasted_cards") or "").strip()
        if not import_file and not pasted_cards:
            raise forms.ValidationError("Upload a file or paste card rows.")
        return cleaned_data

    def clean_import_file(self):
        upload = self.cleaned_data.get("import_file")
        if upload and upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Import file must be 2 MB or smaller.")
        return upload

    def clean_default_tags(self):
        raw = self.cleaned_data.get("default_tags") or ""
        tags = [tag.strip() for tag in raw.split(",")]
        return [tag for tag in tags if tag]

    def source_text(self) -> str:
        upload = self.cleaned_data.get("import_file")
        if upload:
            raw = upload.read()
            try:
                return raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                return raw.decode("latin-1")
        return self.cleaned_data.get("pasted_cards") or ""


class DeckForm(forms.Form):
    name = forms.CharField(max_length=255, error_messages={"required": "Deck name is required."})
    description = forms.CharField(required=False, widget=forms.Textarea)
    category = forms.CharField(max_length=255, required=False)
    is_public = forms.BooleanField(required=False)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Deck name is required.")
        return name

    def clean_description(self):
        return (self.cleaned_data.get("description") or "").strip()

    def clean_category(self):
        return (self.cleaned_data.get("category") or "").strip()


class AIGenerateForm(forms.Form):
    topic = forms.CharField(min_length=1, max_length=500)
    count = forms.IntegerField(min_value=1, max_value=20)
    language = forms.CharField(min_length=2, max_length=10, initial="en", required=False)
    target_language = forms.CharField(min_length=2, max_length=10, initial="fa", required=False)
    level = forms.ChoiceField(choices=[(level, level.title()) for level in LEVELS], required=False)

    def clean_language(self):
        return self.cleaned_data.get("language") or "en"

    def clean_target_language(self):
        return self.cleaned_data.get("target_language") or "fa"

    def clean_level(self):
        return self.cleaned_data.get("level") or "beginner"
