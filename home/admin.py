from django.contrib import admin
from .models import (
    Categoria, Marca, Producto, ImagenProducto, TallaProducto
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ["nombre"]

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    search_fields = ["nombre"]

class ImagenInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

class TallaInline(admin.TabularInline):
    model = TallaProducto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "categoria", "marca", "precio", "stock", "esta_disponible"]
    list_filter = ["categoria", "marca", "es_destacado", "esta_disponible"]
    search_fields = ["nombre"]
    inlines = [ImagenInline, TallaInline]