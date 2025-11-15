from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model


User = get_user_model()
class ClienteRegistrationForm(UserCreationForm):
    telefono = forms.CharField(
        max_length=20, 
        widget=forms.TextInput(attrs={'placeholder': '+34 600 123 456'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username", "email",
            "first_name", "last_name",
            "telefono", "direccion", "ciudad", "codigo_postal",
            "password", "password2",
        ]

