import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
import uuid
from django.db.models import Sum
from django.db.models.functions import Coalesce

class Cliente(AbstractUser):
    telefono = models.CharField(max_length=20, blank=False)
    direccion = models.CharField(max_length=255, blank=False)
    ciudad = models.CharField(max_length=100, blank=False)
    codigo_postal = models.CharField(max_length=10, blank=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    is_anonymous_user = models.BooleanField(default=False, blank=True)

    def __str__(self):
        base = self.username or self.email or "cliente"
        return f"{base} ({self.email})" if self.email else base


class Categoria(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.URLField(blank=True)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    imagen = models.URLField(blank=True)

    def __str__(self):
        return self.nombre

class Color(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    codigo_hex = models.CharField(max_length=7, blank=True, help_text="Ej: #FF0000 para rojo") 

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Colores"

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="productos")
    genero = models.CharField(max_length=50, blank=True)
    colores = models.ManyToManyField(Color, blank=True, related_name="productos")
    material = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    es_destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return f"/catalogo/{self.slug or slugify(self.nombre)}/"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:200]
            slug_candidate = base
            i = 1
            while Producto.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                i += 1
                slug_candidate = f"{base}-{i}"
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    @property
    def precio_final(self):
        return self.precio_oferta if self.precio_oferta else self.precio
    


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="imagenes")
    imagen = models.URLField()
    es_principal = models.BooleanField(default=False)

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"


class TallaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="tallas")
    talla = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("producto", "talla")

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla}"

# Carrito / Pedido (esqueleto funcional)
class Carrito(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="carritos", null=True, blank=True)
    codigo_carrito = models.CharField(max_length=11, unique=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.codigo_carrito or f"Carrito #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.codigo_carrito:
            self.codigo_carrito = f"CRT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(item.subtotal for item in self.carrito_items.all())

    @property
    def cantidad_total_items(self):
        return sum(item.cantidad for item in self.carrito_items.all())

    @property
    def subtotalIVA(self):
        return float(self.total) * 0.21

    @property
    def total_con_envio(self):
        ENVIO = 4.50
        subtotal = float(self.total)
        return subtotal + ENVIO if subtotal > 0 else 0


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="carrito_items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="items_carrito")
    talla_producto = models.ForeignKey(TallaProducto, on_delete=models.CASCADE, related_name="items_carrito")
    cantidad = models.IntegerField(default=1)

    class Meta:
        unique_together = ("carrito", "producto", "talla_producto")

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} ({self.talla_producto.talla}) en {self.carrito}"

    @property
    def subtotal(self):
        return self.producto.precio_final * self.cantidad


class Pedido(models.Model):
    class EstadoEnvio(models.TextChoices):
        EN_PREPARACION = "Preparing", "Preparandolo"
        EN_CAMINO = "On the way", "En camino"
        ENTREGADO = "Delivered", "Entregado"
    stripe_checkout_id = models.CharField(max_length=255, unique=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    divisa = models.CharField(max_length=10)
    cliente_email = models.EmailField()
    codigo_seguimiento = models.CharField(max_length=50, blank=True, null=True)
    estado_envio = models.CharField(max_length=20, choices=EstadoEnvio.choices,blank=True, null=True)
    status = models.CharField(max_length=20, choices=[("Pending", "Pendiente de pago"), ("Paid", "Pagado")])
    seguimiento_token = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.stripe_checkout_id} - {self.status}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='pedido_items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    talla = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Order {self.producto.nombre} - {self.pedido.stripe_checkout_id}"