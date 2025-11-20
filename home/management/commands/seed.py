from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal

from home.models import (
    Categoria, Marca, Producto, ImagenProducto, TallaProducto,
    Carrito, ItemCarrito, Cliente, Pedido, ItemPedido
)

class Command(BaseCommand):
    help = "Seed database with initial data"

    def handle(self, *args, **options):
        self.stdout.write("🧹 Clearing database…")

        ItemPedido.objects.all().delete()
        Pedido.objects.all().delete()
        ItemCarrito.objects.all().delete()
        Carrito.objects.all().delete()
        ImagenProducto.objects.all().delete()
        TallaProducto.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Marca.objects.all().delete()
        Cliente.objects.all().delete()

        self.stdout.write("✨ Creating seed data…")

        # Categorías
        cat1 = Categoria.objects.create(nombre="Zapatillas", descripcion="Calzado deportivo",
                                        imagen="https://via.placeholder.com/300")
        cat2 = Categoria.objects.create(nombre="Camisas", descripcion="Ropa casual",
                                        imagen="https://via.placeholder.com/300")

        # Marcas
        marca1 = Marca.objects.create(nombre="Nike", imagen="https://via.placeholder.com/300")
        marca2 = Marca.objects.create(nombre="Adidas", imagen="https://via.placeholder.com/300")

        # Productos
        p1 = Producto.objects.create(
            nombre="Nike Air Max",
            slug=slugify("Nike Air Max"),
            descripcion="Zapatillas muy cómodas",
            precio=Decimal("120.00"),
            genero="Unisex",
            color="Negro",
            material="Sintético",
            stock=10,
            categoria=cat1,
            marca=marca1,
        )
        p2 = Producto.objects.create(
            nombre="Adidas Superstar",
            slug=slugify("Adidas Superstar"),
            descripcion="Clásicas y elegantes",
            precio=Decimal("90.00"),
            precio_oferta=Decimal("75.00"),
            genero="Unisex",
            color="Blanco",
            material="Cuero",
            stock=15,
            categoria=cat1,
            marca=marca2,
        )

        # Imágenes
        ImagenProducto.objects.create(producto=p1, imagen="https://via.placeholder.com/500", es_principal=True)
        ImagenProducto.objects.create(producto=p2, imagen="https://via.placeholder.com/500", es_principal=True)

        # Tallas
        for talla in ["38", "39", "40", "41", "42"]:
            TallaProducto.objects.create(producto=p1, talla=talla, stock=5)

        for talla in ["S", "M", "L", "XL"]:
            TallaProducto.objects.create(producto=p2, talla=talla, stock=8)

        # Cliente
        cliente = Cliente.objects.create_user(
            username="testuser",
            password="12345678",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            telefono="123456789",
            direccion="Calle Falsa 123",
            ciudad="Madrid",
            codigo_postal="28001",
        )

        # Carrito
        carrito = Carrito.objects.create(codigo_carrito="ABC12345678")
        ItemCarrito.objects.create(carrito=carrito, producto=p1, cantidad=2)

        # Pedido
        pedido = Pedido.objects.create(
            stripe_checkout_id="chk_test_123456",
            cantidad=Decimal("240.00"),
            divisa="EUR",
            cliente_email="test@example.com",
            status="Paid"
        )
        ItemPedido.objects.create(pedido=pedido, producto=p1, cantidad=2)

        self.stdout.write(self.style.SUCCESS("🎉 Seed completed!"))
