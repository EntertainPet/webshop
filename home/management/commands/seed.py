# tuapp/management/commands/seed.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from decimal import Decimal
import random

from home.models import (
    Categoria, Marca, Producto, ImagenProducto,
    TallaProducto, Carrito, ItemCarrito,
    Pedido, ItemPedido
)

User = get_user_model()

class Command(BaseCommand):
    help = "Seed database with sample data"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Iniciando seeder...")

        # --------------------------
        # 0. BORRAR DATOS PREVIOS
        # --------------------------
        self.stdout.write("⚠️ Eliminando datos previos...")

        ItemPedido.objects.all().delete()
        Pedido.objects.all().delete()
        ItemCarrito.objects.all().delete()
        Carrito.objects.all().delete()
        TallaProducto.objects.all().delete()
        ImagenProducto.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Marca.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write("✔ Base de datos limpiada")

        # --------------------------
        # 1. CLIENTES
        # --------------------------
        user = User.objects.create_user(
            username="cliente_test",
            password="cliente123",
            email="cliente@test.com",
            telefono="600000000",
            direccion="Av. Principal 1",
            ciudad="Madrid",
            codigo_postal="28001"
        )

        anon = User.objects.create(
            username="anonimo",
            telefono="---",
            direccion="---",
            ciudad="---",
            codigo_postal="00000",
            is_anonymous_user=True
        )

        self.stdout.write("✔ Clientes creados")

        # --------------------------
        # 2. CATEGORÍAS
        # --------------------------
        categorias_data = [
            ("Zapatillas", "Calzado deportivo"),
            ("Botas", "Calzado de montaña"),
            ("Sandalias", "Verano"),
            ("Chaquetas", "Abrigo y outdoor"),
            ("Camisetas", "Ropa ligera"),
            ("Pantalones", "Deportivos y casual"),
        ]

        categorias = []
        for nombre, desc in categorias_data:
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre,
                descripcion=desc
            )
            categorias.append(categoria)

        self.stdout.write("✔ Categorías creadas")

        # --------------------------
        # 3. MARCAS
        # --------------------------
        marcas_nombres = [
            "Nike", "Adidas", "Puma", "Reebok",
            "New Balance", "Converse", "Jordan", "Vans"
        ]

        marcas = []
        for nombre in marcas_nombres:
            marca, _ = Marca.objects.get_or_create(nombre=nombre)
            marcas.append(marca)

        self.stdout.write("✔ Marcas creadas")

        # --------------------------
        # 4. PRODUCTOS (mínimo 30)
        # --------------------------
        productos = []
        total_productos = 30

        for i in range(1, total_productos + 1):
            nombre = f"Producto Test {i}"
            precio = Decimal(random.choice([49.99, 59.99, 79.99, 99.99, 129.99]))
            precio_oferta = precio - 20 if i % 5 == 0 else None

            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=f"Descripción completa del producto {i}.",
                precio=precio,
                precio_oferta=precio_oferta,
                categoria=random.choice(categorias),
                marca=random.choice(marcas),
                genero=random.choice(["Hombre", "Mujer", "Unisex"]),
                color=random.choice(["Rojo", "Negro", "Blanco", "Azul", "Verde"]),
                material=random.choice(["Cuero", "Sintético", "Algodón", "Poliéster"]),
                stock=random.randint(0, 100),
                es_destacado=random.choice([True, False])
            )

            productos.append(producto)

        self.stdout.write("✔ Productos creados (30+)")

       # --------------------------
        # 5. IMÁGENES DE PRODUCTO
        # --------------------------

        picsum_urls = [
            "https://picsum.photos/seed/pet-toy-1/600/600",
            "https://picsum.photos/seed/pet-toy-2/600/600",
            "https://picsum.photos/seed/pet-toy-3/600/600",
            "https://picsum.photos/seed/pet-toy-4/600/600",
            "https://picsum.photos/seed/pet-toy-5/600/600",
            "https://picsum.photos/seed/pet-toy-6/600/600",
        ]

        for idx, producto in enumerate(productos):
            base_url = picsum_urls[idx % len(picsum_urls)]

            ImagenProducto.objects.create(
                producto=producto,
                imagen=base_url,
                es_principal=True
            )

            # Dos variantes (puedes cambiar solo el tamaño, por ejemplo)
            ImagenProducto.objects.create(
                producto=producto,
                imagen=base_url,   # o mismo URL
                es_principal=False
            )
            ImagenProducto.objects.create(
                producto=producto,
                imagen=base_url,   # o mismo URL
                es_principal=False
            )
        self.stdout.write("✔ Imágenes de productos creadas")

        # --------------------------
        # 6. TALLAS
        # --------------------------
        tallas = ["S", "M", "L", "XL", "40", "41", "42", "43"]

        for producto in productos:
            for talla in random.sample(tallas, 4):
                TallaProducto.objects.create(
                    producto=producto,
                    talla=talla,
                    stock=random.randint(1, 30)
                )

        self.stdout.write("✔ Tallas creadas")

        # --------------------------
        # 7. CARRITOS
        # --------------------------
        for c in range(1, 5):
            carrito = Carrito.objects.create(codigo_carrito=f"CRT-{c:04}")
            for _ in range(random.randint(1, 5)):
                ItemCarrito.objects.create(
                    carrito=carrito,
                    producto=random.choice(productos),
                    cantidad=random.randint(1, 3)
                )

        self.stdout.write("✔ Carritos creados")

        # --------------------------
        # 8. PEDIDOS
        # --------------------------
        for i in range(1, 6):
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"chk_seed_{i}",
                cantidad=0,
                divisa="EUR",
                cliente_email="cliente@test.com",
                status=random.choice(["Pending", "Paid"]),
            )

            total = Decimal(0)

            for _ in range(random.randint(1, 4)):
                producto = random.choice(productos)
                cantidad = random.randint(1, 3)

                ItemPedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad
                )

                total += producto.precio_final * cantidad

            pedido.cantidad = total
            pedido.save()

        self.stdout.write(self.style.SUCCESS("🎉 SEED COMPLETADO CON ÉXITO"))
