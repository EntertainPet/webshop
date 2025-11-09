from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Cliente

class ClienteRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = Cliente
        fields = [
            "username", "email",
            "first_name", "last_name",
            "telefono", "direccion", "ciudad", "codigo_postal",
            "password1", "password2",
        ]

class ClienteLoginForm(AuthenticationForm):
    pass
