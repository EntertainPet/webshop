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
            "telefono", "direccion", "ciudad", "codigo_postal"
        ]

class ClienteUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar los datos de un cliente desde el panel de admin.
    No maneja la contraseña.
    """
    class Meta:
        model = User
        fields = [
            "username", "email",
            "first_name", "last_name",
            "telefono", "direccion", "ciudad", "codigo_postal",
            "is_staff", "is_active"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

