from django.contrib import admin
from .models import (
    Categoria, Marca, Producto, ImagenProducto, TallaProducto, Carrito, ItemCarrito, Pedido, ItemPedido
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

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("codigo_carrito", "creado_en", "actualizado_en")
    search_fields = ("codigo_carrito",)
    list_filter = ("creado_en",)

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ("carrito", "producto", "cantidad")
    list_filter = ("carrito", "producto")
    search_fields = ("carrito__codigo_carrito", "producto__nombre")

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("stripe_checkout_id", "cliente_email", "cantidad", "divisa", "status", "fecha_creacion")
    list_filter = ("status", "fecha_creacion")
    search_fields = ("stripe_checkout_id", "cliente_email")

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "cantidad")
    list_filter = ("pedido", "producto")
    search_fields = ("pedido__stripe_checkout_id", "producto__nombre")