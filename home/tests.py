from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from decimal import Decimal
import json

from .models import (
    Cliente,
    Categoria,
    Marca,
    Color,
    Producto,
    ImagenProducto,
    TallaProducto,
    Carrito,
    ItemCarrito,
    Pedido,
    ItemPedido,
)
from .forms import ClienteRegistrationForm


User = get_user_model()


class TestsCliente(TestCase):
    def test_crear_cliente_con_email(self):
        cliente = Cliente.objects.create_user(
            username="oscar",
            email="oscar@example.com",
            password="pass123",
            telefono="600111222",
            direccion="Calle Mayor 1",
            ciudad="Sevilla",
            codigo_postal="41001",
        )
        self.assertEqual(str(cliente), "oscar (oscar@example.com)")

    def test_crear_cliente_sin_email(self):
        cliente = Cliente.objects.create_user(
            username="maria",
            password="pass123",
            telefono="600333444",
            direccion="Avenida 2",
            ciudad="Madrid",
            codigo_postal="28001",
        )
        self.assertEqual(str(cliente), "maria")

    def test_cliente_anonimo(self):
        cliente = Cliente.objects.create_user(
            username="invitado123",
            password="temp123",
            telefono="000000000",
            direccion="Temporal",
            ciudad="Temporal",
            codigo_postal="00000",
            is_anonymous_user=True,
        )
        self.assertTrue(cliente.is_anonymous_user)

class TestsCatalogo(TestCase):
    def test_crear_color(self):
        color = Color.objects.create(nombre="Rojo", codigo_hex="#FF0000")
        self.assertEqual(str(color), "Rojo")
        self.assertEqual(color.codigo_hex, "#FF0000")

    def test_crear_color_sin_hex(self):
        color = Color.objects.create(nombre="Azul")
        self.assertEqual(str(color), "Azul")
        self.assertEqual(color.codigo_hex, "")

    def test_crear_categoria(self):
        cat = Categoria.objects.create(nombre="Perros", descripcion="Para perros")
        self.assertEqual(str(cat), "Perros")

    def test_crear_marca(self):
        marca = Marca.objects.create(nombre="PetBrand")
        self.assertEqual(str(marca), "PetBrand")

class TestsProducto(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Gatos")
        self.marca = Marca.objects.create(nombre="Whiskas")

    def test_crear_producto(self):
        producto = Producto.objects.create(
            nombre="Comida para gato",
            descripcion="Comida premium",
            precio=15.50,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.assertEqual(str(producto), "Comida para gato")
        self.assertEqual(producto.precio_final, producto.precio)

    def test_precio_con_oferta(self):
        producto = Producto.objects.create(
            nombre="Arena para gatos",
            precio=20.00,
            precio_oferta=15.00,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.assertEqual(producto.precio_final, Decimal('15.00'))


    def test_url_absoluta_producto(self):
        producto = Producto.objects.create(
            nombre="Juguete ratón",
            precio=5.00,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.assertEqual(producto.get_absolute_url(), f"/catalogo/{producto.slug}/")

    
    def test_producto_con_varios_colores(self):
        color_rojo = Color.objects.create(nombre="Rojo", codigo_hex="#FF0000")
        color_azul = Color.objects.create(nombre="Azul", codigo_hex="#0000FF")
        
        producto = Producto.objects.create(
            nombre="Collar ajustable",
            precio=12.00,
            categoria=self.categoria,
            marca=self.marca,
        )
        producto.colores.add(color_rojo, color_azul)
        
        self.assertEqual(producto.colores.count(), 2)
        self.assertIn(color_rojo, producto.colores.all())
        self.assertIn(color_azul, producto.colores.all())

class TestsImagen(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Aves")
        self.marca = Marca.objects.create(nombre="TrixieBird")
        self.producto = Producto.objects.create(
            nombre="Jaula para pájaros",
            precio=45.00,
            categoria=self.categoria,
            marca=self.marca,
        )

    def test_imagen_producto_str(self):
        imagen = ImagenProducto.objects.create(
            producto=self.producto,
            imagen="https://example.com/jaula.jpg",
            es_principal=True,
        )
        self.assertEqual(str(imagen), f"Imagen de {self.producto.nombre}")

class TestsCarrito(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Perros")
        self.marca = Marca.objects.create(nombre="Pedigree")
        self.producto = Producto.objects.create(
            nombre="Pienso adulto",
            precio=25.00,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.talla = TallaProducto.objects.create(
            producto=self.producto,
            talla="M",
            stock=50
        )

    def test_ver_carrito(self):
        carrito = Carrito.objects.create(codigo_carrito="CRT-ABC12345")
        self.assertEqual(str(carrito), "CRT-ABC12345")

    def test_carrito_genera_codigo(self):
        carrito = Carrito.objects.create()
        self.assertTrue(carrito.codigo_carrito.startswith("CRT-"))
        self.assertEqual(len(carrito.codigo_carrito), 12)

    def test_carrito_calcula_total(self):
        carrito = Carrito.objects.create(codigo_carrito="CRT-TEST001")
        ItemCarrito.objects.create(
            carrito=carrito,
            producto=self.producto,
            talla_producto=self.talla,
            cantidad=2,
        )
        self.assertEqual(carrito.total, Decimal('50.00'))

    def test_carrito_cantidad_total_items(self):
        carrito = Carrito.objects.create(codigo_carrito="CRT-TEST002")
        ItemCarrito.objects.create(
            carrito=carrito,
            producto=self.producto,
            talla_producto=self.talla,
            cantidad=3,
        )
        self.assertEqual(carrito.cantidad_total_items, 3)

    
    def test_item_carrito_subtotal(self):
        carrito = Carrito.objects.create(codigo_carrito="CRT-TEST004")
        item = ItemCarrito.objects.create(
            carrito=carrito,
            producto=self.producto,
            talla_producto=self.talla,
            cantidad=3,
        )
        self.assertEqual(item.subtotal, Decimal('75.00'))

class TestsPedido(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Accesorios")
        self.marca = Marca.objects.create(nombre="Generic")
        self.producto = Producto.objects.create(
            nombre="Correa extensible",
            precio=18.50,
            categoria=self.categoria,
            marca=self.marca,
        )

    def testcreacion_token(self):
        pedido = Pedido.objects.create(
            stripe_checkout_id="cs_test_abc",
            cantidad=50.00,
            divisa="eur",
            cliente_email="test@ejemplo.com",
            status="Paid",
        )
        self.assertIsNotNone(pedido.seguimiento_token)

    def test_pedido_estado_envio(self):
        pedido = Pedido.objects.create(
            stripe_checkout_id="cs_test_xyz",
            cantidad=75.00,
            divisa="eur",
            cliente_email="pedido@ejemplo.com",
            status="Paid",
            estado_envio=Pedido.EstadoEnvio.EN_PREPARACION
        )
        self.assertEqual(pedido.estado_envio, "Preparing")

    
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsFormularioRegistro(TestCase):
    def test_formulario_valido_con_datos_completos(self):
        datos = {
            "username": "oscar",
            "email": "oscar@mail.com",
            "first_name": "Gom",
            "last_name": "Gom",
            "telefono": "611222333",
            "direccion": "Calle Principal 10",
            "ciudad": "Barcelona",
            "codigo_postal": "08001",
            "password1": "ContraseñaSegura123!",
            "password2": "ContraseñaSegura123!",
        }
        form = ClienteRegistrationForm(data=datos)
        self.assertTrue(form.is_valid(), form.errors)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsPaginasBasicas(TestCase):    
    def setUp(self):
        self.client = Client()

    def test_pagina_catalogo_accesible(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/lista_productos.html")

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsAutenticacion(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = Cliente.objects.create_user(
            username="oscar",
            email="oscar@mail.com",
            password="pepito123",
            telefono="622333444",
            direccion="Calle Falsa 123",
            ciudad="Sevilla",
            codigo_postal="29001",
        )

    def test_vista_invitado_crea_usuario_anonimo(self):
        url = reverse("home:guest")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("home:catalogo"))
        self.assertTrue(Cliente.objects.filter(is_anonymous_user=True).exists())

    def test_registro_redirige_si_autenticado(self):
        self.client.login(username="oscar", password="pepito123")
        url = reverse("home:register")
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("home:catalogo"))

    def test_registro_exitoso_crea_usuario(self):
        url = reverse("home:register")
        datos = {
            "username": "nuevoregistro",
            "email": "registro@ejemplo.com",
            "first_name": "Nuevo",
            "last_name": "Registro",
            "telefono": "633444555",
            "direccion": "Avenida Test 5",
            "ciudad": "Sevilla",
            "codigo_postal": "41002",
            "password1": "MiPassword123!",
            "password2": "MiPassword123!",
        }
        resp = self.client.post(url, datos)
        self.assertRedirects(resp, reverse("home:catalogo"))
        self.assertTrue(Cliente.objects.filter(username="nuevoregistro").exists())

    def test_registro_invalido_muestra_errores(self):
        url = reverse("home:register")
        datos = {
            "username": "",
            "email": "email-invalido",
        }
        resp = self.client.post(url, datos)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "registration/registro.html")

    def test_login_superusuario_redirige_gestor(self):
        admin = Cliente.objects.create_superuser(
            username="admin",
            email="admin@ejemplo.com",
            password="admin123",
            telefono="999888777",
            direccion="Admin Street",
            ciudad="Admin City",
            codigo_postal="99999",
        )
        url = reverse("home:login")
        resp = self.client.post(url, {
            "username": "admin",
            "password": "admin123"
        })
        self.assertRedirects(resp, "/gestor/", fetch_redirect_response=False)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsCambioPassword(TestCase):    
    def setUp(self):
        self.client = Client()
        self.usuario = Cliente.objects.create_user(
            username="cambiopass",
            email="cambio@ejemplo.com",
            password="antigua123",
            telefono="644555666",
            direccion="Calle Cambio 1",
            ciudad="Bilbao",
            codigo_postal="48001",
            cambio_contraseña_requerido=True,
        )

    def test_vista_cambio_personalizado_accesible(self):
        self.client.login(username="cambiopass", password="antigua123")
        url = reverse("home:change_password")
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302])


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsCatalogoBusqueda(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_perros = Categoria.objects.create(nombre="Perros")
        self.cat_gatos = Categoria.objects.create(nombre="Gatos")
        self.marca_a = Marca.objects.create(nombre="MarcaA")
        self.marca_b = Marca.objects.create(nombre="MarcaB")
        self.color_negro = Color.objects.create(nombre="Negro", codigo_hex="#000000")
        self.color_blanco = Color.objects.create(nombre="Blanco", codigo_hex="#FFFFFF")

        self.prod1 = Producto.objects.create(
            nombre="Pienso premium para perro",
            descripcion="Pienso de alta calidad",
            precio=30.00,
            categoria=self.cat_perros,
            marca=self.marca_a,
            esta_disponible=True,
            material="natural",
        )
        self.prod1.colores.add(self.color_negro)
        
        self.prod2 = Producto.objects.create(
            nombre="Arena para gato",
            descripcion="Arena aglomerante",
            precio=12.00,
            categoria=self.cat_gatos,
            marca=self.marca_b,
            esta_disponible=True,
            material="arcilla",
        )
        self.prod2.colores.add(self.color_blanco)
        
        self.prod3 = Producto.objects.create(
            nombre="Producto no disponible",
            precio=99.99,
            categoria=self.cat_perros,
            marca=self.marca_a,
            esta_disponible=False,
        )

    def test_catalogo_solo_muestra_disponibles(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        productos = list(resp.context["productos"])
        self.assertIn(self.prod1, productos)
        self.assertIn(self.prod2, productos)
        self.assertNotIn(self.prod3, productos)

    def test_busqueda_por_texto(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url, {"q": "pienso"})
        productos = list(resp.context["productos"])
        self.assertIn(self.prod1, productos)
        self.assertNotIn(self.prod2, productos)

    def test_filtros(self):
        url = reverse("home:catalogo")
        params = {
            "categoria": [str(self.cat_perros.id)],
            "marca": [str(self.marca_a.id)],
            "color": [str(self.color_negro.id)],
            "material": ["natural"],
            "min": "20",
            "max": "40",
        }
        resp = self.client.get(url, params)
        productos = list(resp.context["productos"])
        self.assertIn(self.prod1, productos)
        self.assertNotIn(self.prod2, productos)

    def test_catalogo_contexto_incluye_filtros(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url, {"categoria": [str(self.cat_perros.id)]})
        ctx = resp.context
        self.assertIn(self.cat_perros, list(ctx["categorias"]))
        self.assertIn(self.marca_a, list(ctx["marcas"]))

    def test_autocompletado(self):
        url = reverse("home:autocomplete")
        resp = self.client.get(url, {"q": "pienso"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]["nombre"], self.prod1.nombre)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsDetalleProducto(TestCase):    
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre="Reptiles")
        self.marca = Marca.objects.create(nombre="ReptiPro")
        self.producto = Producto.objects.create(
            nombre="Terrario mediano",
            descripcion="Terrario de cristal",
            precio=85.00,
            categoria=self.categoria,
            marca=self.marca,
        )

    def test_detalle_producto_accesible(self):
        url = reverse("home:producto_detalle", kwargs={"slug": self.producto.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "producto_detalle.html")
        self.assertEqual(resp.context["producto"], self.producto)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsGestionCarrito(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre="Peces")
        self.marca = Marca.objects.create(nombre="AquaPro")
        self.producto = Producto.objects.create(
            nombre="Filtro acuario",
            precio=45.00,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.talla = TallaProducto.objects.create(
            producto=self.producto,
            talla="L",
            stock=10
        )
        self.usuario = Cliente.objects.create_user(
            username="comprador",
            email="comprador@ejemplo.com",
            password="compra123",
            telefono="655666777",
            direccion="Calle Compra 5",
            ciudad="Valencia",
            codigo_postal="46002",
        )
        self.carrito = Carrito.objects.create(
            codigo_carrito="CRT-COMPRA1",
            cliente=self.usuario
        )
        ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            talla_producto=self.talla,
            cantidad=1
        )

    def test_vista_carrito_accesible(self):
        url = reverse("home:carrito")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "cart.html")

    def test_añadir_producto_carrito_autenticado(self):
        self.client.login(username="comprador", password="compra123")
        url = reverse("home:carrito_add", kwargs={"pk": self.producto.pk})
        resp = self.client.post(url, {
            "talla_producto_id": self.talla.id,
            "cantidad": 1
        })
        self.assertEqual(resp.status_code, 302)

    def test_añadir_sin_talla(self):
        self.client.login(username="comprador", password="compra123")
        url = reverse("home:carrito_add", kwargs={"pk": self.producto.pk})
        resp = self.client.post(url, {"cantidad": 1})
        self.assertEqual(resp.status_code, 302)

    def test_añadir_sin_stock(self):
        self.client.login(username="comprador", password="compra123")
        url = reverse("home:carrito_add", kwargs={"pk": self.producto.pk})
        resp = self.client.post(url, {
            "talla_producto_id": self.talla.id,
            "cantidad": 999
        })
        self.assertEqual(resp.status_code, 302)

    def test_eliminar_item_carrito(self):
        self.client.login(username="comprador", password="compra123")
        item = self.carrito.carrito_items.first()
        url = reverse("home:carrito_remove", kwargs={"item_id": item.id})
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("home:carrito"))

    def test_aumentar_cantidad_item(self):
        self.client.login(username="comprador", password="compra123")
        item = self.carrito.carrito_items.first()
        cantidad_anterior = item.cantidad
        url = reverse("home:carrito_update", kwargs={"item_id": item.id})
        resp = self.client.post(url, {"action": "increase"})
        self.assertRedirects(resp, reverse("home:carrito"))
        item.refresh_from_db()
        self.assertGreaterEqual(item.cantidad, cantidad_anterior)

    def test_quitar_cantidad_item(self):
        self.client.login(username="comprador", password="compra123")
        item = self.carrito.carrito_items.first()
        item.cantidad = 3
        item.save()
        
        url = reverse("home:carrito_update", kwargs={"item_id": item.id})
        resp = self.client.post(url, {"action": "decrease"})
        self.assertRedirects(resp, reverse("home:carrito"))
        
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 2)

    def test_carrito_sesion_usuario_anonimo(self):
        url = reverse("home:carrito_add", kwargs={"pk": self.producto.pk})
        resp = self.client.post(url, {
            "talla_producto_id": self.talla.id,
            "cantidad": 1
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn('cart', self.client.session)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsCarritoSesion(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nombre="Hamsters")
        self.marca = Marca.objects.create(nombre="HamsterLand")
        self.producto = Producto.objects.create(
            nombre="Rueda ejercicio",
            precio=8.50,
            categoria=self.categoria,
            marca=self.marca,
        )
        self.talla = TallaProducto.objects.create(
            producto=self.producto,
            talla="S",
            stock=25
        )

    def test_actualizar_item_carrito_anonimo(self):
        session = self.client.session
        session['cart'] = {f"{self.producto.id}-{self.talla.id}-none": 1}
        session.save()

        url = reverse("home:carrito_update_session_item")
        resp = self.client.post(url, {
            "key": f"{self.producto.id}-{self.talla.id}-none",
            "action": "increase"
        })
        self.assertEqual(resp.status_code, 302)

    def test_eliminar_item_carrito_anonimo(self):
        session = self.client.session
        session['cart'] = {f"{self.producto.id}-{self.talla.id}-none": 2}
        session.save()

        url = reverse("home:carrito_remove_session_item")
        resp = self.client.post(url, {
            "key": f"{self.producto.id}-{self.talla.id}-none"
        })
        self.assertEqual(resp.status_code, 302)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsHistorialPedidos(TestCase):    
    def setUp(self):
        self.client = Client()
        self.usuario = Cliente.objects.create_user(
            username="pedidos",
            email="pedidos@ejemplo.com",
            password="pedidos123",
            telefono="666777888",
            direccion="Calle Pedidos 10",
            ciudad="Granada",
            codigo_postal="18001",
        )
        self.pedido = Pedido.objects.create(
            stripe_checkout_id="cs_pedido_123",
            cantidad=150.00,
            divisa="eur",
            cliente_email="pedidos@ejemplo.com",
            status="Paid",
        )

    def test_historial_requiere_login(self):
        url = reverse("home:historial")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/login/'))

    def test_historial_muestra_pedidos_usuario(self):
        self.client.login(username="pedidos", password="pedidos123")
        url = reverse("home:historial")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/historial_pedidos.html")

    def test_detalle_pedido_accesible(self):
        self.client.login(username="pedidos", password="pedidos123")
        url = reverse("home:historial_detalle", kwargs={"pk": self.pedido.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/pedido_detalle.html")
        self.assertEqual(resp.context["pedido"], self.pedido)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsSeguimientoPedido(TestCase):
    def setUp(self):
        self.client = Client()
        self.pedido_preparacion = Pedido.objects.create(
            stripe_checkout_id="cs_seguimiento_1",
            cantidad=80.00,
            divisa="eur",
            cliente_email="seguimiento@ejemplo.com",
            status="Paid",
            estado_envio=Pedido.EstadoEnvio.EN_PREPARACION,
        )
        self.pedido_camino = Pedido.objects.create(
            stripe_checkout_id="cs_seguimiento_2",
            cantidad=120.00,
            divisa="eur",
            cliente_email="seguimiento2@ejemplo.com",
            status="Paid",
            estado_envio=Pedido.EstadoEnvio.EN_CAMINO,
        )
        self.pedido_entregado = Pedido.objects.create(
            stripe_checkout_id="cs_seguimiento_3",
            cantidad=200.00,
            divisa="eur",
            cliente_email="seguimiento3@ejemplo.com",
            status="Paid",
            estado_envio=Pedido.EstadoEnvio.ENTREGADO,
        )

    def test_seguimiento_con_token(self):
        url = reverse("home:seguimiento_token", kwargs={"token": self.pedido_preparacion.seguimiento_token})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/estado_envio.html")
        self.assertEqual(resp.context["pedido"], self.pedido_preparacion)

    def test_progreso_en_camino_50(self):
        url = reverse("home:seguimiento_token", kwargs={"token": self.pedido_camino.seguimiento_token})
        resp = self.client.get(url)
        self.assertEqual(resp.context["progreso"], 50)

    def test_progreso_entregado_100(self):
        url = reverse("home:seguimiento_token", kwargs={"token": self.pedido_entregado.seguimiento_token})
        resp = self.client.get(url)
        self.assertEqual(resp.context["progreso"], 100)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestsStripeCheckout(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pagina_success_accesible(self):
        url = reverse("home:success")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/success.html")

    def test_pagina_cancel_accesible(self):
        url = reverse("home:cancel")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/cancel.html")
