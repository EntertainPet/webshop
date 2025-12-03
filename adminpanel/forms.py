from django import forms
from django.forms import modelformset_factory
from home.models import Categoria, Producto, ImagenProducto


class ProductForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre", "slug", "descripcion",
            "precio", "precio_oferta",
            "categoria", "marca",
            "genero", "material",
            "stock", "esta_disponible", "es_destacado",
            "colores",
        ]
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "marca": forms.Select(attrs={"class": "form-select"}),
            "colores": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # style inputs consistently for the admin panel
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, forms.Select)):
                field.widget.attrs.update({'class': 'form-control'})
            if name == 'descripcion':
                field.widget.attrs.update({'class': 'form-control', 'rows': 6})


class ImagenProductoForm(forms.ModelForm):
    imagen_file = forms.FileField(required=False, label='Imagen')
    
    class Meta:
        model = ImagenProducto
        fields = ['id', 'es_principal']  # ¡Agregar 'id' aquí!
        widgets = {
            'es_principal': forms.CheckboxInput(),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "imagen"]



ImagenFormSet = modelformset_factory(
    ImagenProducto,
    form=ImagenProductoForm,
    can_delete=True,
    fields=('id', 'es_principal'),  # Especificar campos explícitamente
)

