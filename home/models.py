from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify

class Cliente(AbstractUser):
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        # “usuario (email)”
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


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="productos")
    genero = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    es_destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        # Prefer slug-based public URL under /catalogo/<slug>/
        return f"/catalogo/{self.slug or slugify(self.nombre)}/"

    def save(self, *args, **kwargs):
        # Auto-generate a unique slug from the nombre when missing
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
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name="carrito")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.cliente.username or self.cliente.email}"

    @property
    def total(self):
        return sum(item.total for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    talla = models.CharField(max_length=20, blank=True)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("carrito", "producto", "talla")

    @property
    def precio_unitario(self):
        return self.producto.precio_final

    @property
    def total(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"