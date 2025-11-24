from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Cliente,
    Categoria,
    Marca,
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


class ClienteModelTests(TestCase):
    def test_str_uses_username_and_email(self):
        cliente = Cliente.objects.create_user(
            username="oscar",
            email="oscar@example.com",
            password="testpass123",
            telefono="600000000",
            direccion="Calle 1",
            ciudad="Sevilla",
            codigo_postal="41000",
        )
        self.assertEqual(str(cliente), "oscar (oscar@example.com)")

    def test_str_falls_back_when_no_email(self):
        cliente = Cliente.objects.create_user(
            username="sinemail",
            password="testpass123",
            telefono="600000000",
            direccion="Calle 1",
            ciudad="Sevilla",
            codigo_postal="41000",
        )
        self.assertEqual(str(cliente), "sinemail")


class CategoriaMarcaProductoModelTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Perros", descripcion="Productos para perros")
        self.marca = Marca.objects.create(nombre="Acme")

    def test_categoria_str(self):
        self.assertEqual(str(self.cat), "Perros")

    def test_marca_str(self):
        self.assertEqual(str(self.marca), "Acme")

    def test_producto_basic_str_and_precio_final_no_oferta(self):
        p = Producto.objects.create(
            nombre="Correa",
            descripcion="Correa resistente",
            precio=10.00,
            categoria=self.cat,
            marca=self.marca,
        )
        self.assertEqual(str(p), "Correa")
        self.assertEqual(p.precio_final, p.precio)

    def test_producto_precio_final_con_oferta(self):
        p = Producto.objects.create(
            nombre="Correa",
            descripcion="Correa resistente",
            precio=10.00,
            precio_oferta=7.50,
            categoria=self.cat,
            marca=self.marca,
        )
        self.assertEqual(p.precio_final, p.precio_oferta)

    def test_producto_auto_slug_on_save_and_get_absolute_url(self):
        p = Producto.objects.create(
            nombre="Correa para perro grande",
            descripcion="Correa",
            precio=10.00,
            categoria=self.cat,
            marca=self.marca,
        )
        expected_slug = slugify("Correa para perro grande")
        self.assertEqual(p.slug, expected_slug)
        self.assertEqual(p.get_absolute_url(), f"/catalogo/{expected_slug}/")

    def test_producto_unique_slug_increment(self):
        base_name = "Juguete pelota"
        p1 = Producto.objects.create(
            nombre=base_name,
            descripcion="Pelota",
            precio=5.00,
            categoria=self.cat,
            marca=self.marca,
        )
        p2 = Producto.objects.create(
            nombre=base_name,
            descripcion="Otra pelota",
            precio=6.00,
            categoria=self.cat,
            marca=self.marca,
        )
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.startswith(slugify(base_name)))


class ImagenTallaProductoTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Gatos")
        self.marca = Marca.objects.create(nombre="CatBrand")
        self.prod = Producto.objects.create(
            nombre="Rascador",
            descripcion="Rascador alto",
            precio=30.00,
            categoria=self.cat,
            marca=self.marca,
        )

    def test_imagen_producto_str(self):
        img = ImagenProducto.objects.create(
            producto=self.prod,
            imagen="https://example.com/img1.jpg",
            es_principal=True,
        )
        self.assertEqual(str(img), f"Imagen de {self.prod.nombre}")

    def test_talla_producto_str_and_unique(self):
        talla = TallaProducto.objects.create(producto=self.prod, talla="M", stock=3)
        self.assertEqual(str(talla), f"{self.prod.nombre} - M")

        with self.assertRaises(Exception):
            # unique_together debe impedir duplicados
            TallaProducto.objects.create(producto=self.prod, talla="M", stock=1)


class CarritoPedidoModelTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Roedores")
        self.marca = Marca.objects.create(nombre="RodentCo")
        self.prod = Producto.objects.create(
            nombre="Jaula",
            descripcion="Jaula amplia",
            precio=50.00,
            categoria=self.cat,
            marca=self.marca,
        )
        self.carrito = Carrito.objects.create(codigo_carrito="CARRITO123")

    def test_carrito_str(self):
        self.assertEqual(str(self.carrito), "CARRITO123")

    def test_item_carrito_str(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.prod,
            cantidad=2,
        )
        expected = f"2 x {self.prod.nombre} en el carrito {self.carrito.codigo_carrito}"
        self.assertEqual(str(item), expected)

    def test_pedido_y_itempedido_str(self):
        pedido = Pedido.objects.create(
            stripe_checkout_id="cs_test_123",
            cantidad=100.00,
            divisa="usd",
            cliente_email="cliente@example.com",
            status="Paid",
        )
        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            producto=self.prod,
            cantidad=1,
        )
        self.assertEqual(str(pedido), "Order cs_test_123 - Paid")
        self.assertEqual(
            str(item_pedido),
            f"Order {self.prod.nombre} - {pedido.stripe_checkout_id}",
        )


class PaginasSimplesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/lista_productos.html")

    # def test_about_page(self):
    #     url = reverse("home:acerca")
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertTemplateUsed(resp, "home/acerca.html")

    # def test_contact_page(self):
    #     url = reverse("home:contacto")
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertTemplateUsed(resp, "home/contacto.html")


class RegistroInvitadoViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="cliente1",
            email="cliente1@example.com",
            password=self.password,
            telefono="600000000",
            direccion="Calle 1",
            ciudad="Sevilla",
            codigo_postal="41000",
        )

    # def test_invitado_view_crea_cliente_anonimo_y_redirige_catalogo(self):
    #     url = reverse("home:invitado")
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 302)
    #     self.assertRedirects(resp, reverse("home:catalogo"))
    #     self.assertTrue(Cliente.objects.filter(is_anonymous_user=True).exists())

    def test_register_view_get_usuario_autenticado_redirige_catalogo(self):
        self.client.login(username="cliente1", password=self.password)
        url = reverse("home:register")
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("home:catalogo"))

    # def test_register_view_get_usuario_anonimo_muestra_template(self):
    #     url = reverse("home:registro")
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertTemplateUsed(resp, "registration/registro.html")

    # def test_register_view_post_valido_crea_usuario_y_carrito_y_loguea(self):
        # url = reverse("home:register")
        # data = {
        #     "username": "nuevo",
        #     "email": "nuevo@example.com",
        #     "first_name": "Nuevo",
        #     "last_name": "Usuario",
        #     "telefono": "600000001",
        #     "direccion": "Calle 2",
        #     "ciudad": "Madrid",
        #     "codigo_postal": "28000",
        #     "password1": "SuperSegura123",
        #     "password2": "SuperSegura123",
        # }
        # resp = self.client.post(url, data)
        # self.assertRedirects(resp, reverse("home:catalogo"))
        # self.assertTrue(User.objects.filter(username="nuevo").exists())
        # nuevo = User.objects.get(username="nuevo")
        # self.assertTrue(nuevo.is_authenticated)
        # self.assertTrue(Carrito.objects.filter(cliente=nuevo).exists())

    def test_register_view_post_invalido_repite_template(self):
        url = reverse("home:register")
        data = {
            "username": "",
            "email": "correo-no-valido",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "registration/registro.html")


class ClienteRegistrationFormTests(TestCase):
    def test_form_fields_present(self):
        form = ClienteRegistrationForm()
        for field in [
            "username",
            "email",
            "first_name",
            "last_name",
            "telefono",
            "direccion",
            "ciudad",
            "codigo_postal",
            "password1",
            "password2",
        ]:
            self.assertIn(field, form.fields)

    def test_form_valid_data(self):
        data = {
            "username": "formuser",
            "email": "formuser@example.com",
            "first_name": "Form",
            "last_name": "User",
            "telefono": "600000002",
            "direccion": "Calle 3",
            "ciudad": "Valencia",
            "codigo_postal": "46000",
            "password1": "Pass12345!",
            "password2": "Pass12345!",
        }
        form = ClienteRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class CatalogoViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat1 = Categoria.objects.create(nombre="Perros")
        self.cat2 = Categoria.objects.create(nombre="Gatos")
        self.m1 = Marca.objects.create(nombre="BrandA")
        self.m2 = Marca.objects.create(nombre="BrandB")

        self.p1 = Producto.objects.create(
            nombre="Pienso para perro",
            descripcion="Pienso premium",
            precio=20.00,
            categoria=self.cat1,
            marca=self.m1,
            esta_disponible=True,
            color="rojo",
            material="plastico",
        )
        self.p2 = Producto.objects.create(
            nombre="Juguete gato",
            descripcion="Juguete divertido",
            precio=5.00,
            categoria=self.cat2,
            marca=self.m2,
            esta_disponible=True,
            color="azul",
            material="goma",
        )
        # No disponible, no debe aparecer
        self.p3 = Producto.objects.create(
            nombre="Producto oculto",
            descripcion="No disponible",
            precio=99.99,
            categoria=self.cat1,
            marca=self.m1,
            esta_disponible=False,
        )

    def test_product_list_view_basico_filtra_disponibles(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/lista_productos.html")
        productos = list(resp.context["productos"])
        self.assertIn(self.p1, productos)
        self.assertIn(self.p2, productos)
        self.assertNotIn(self.p3, productos)

    def test_product_list_view_busqueda_q(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url, {"q": "pienso"})
        productos = list(resp.context["productos"])
        self.assertIn(self.p1, productos)
        self.assertNotIn(self.p2, productos)

    def test_product_list_view_filtros_categoria_marca_color_material_precio(self):
        url = reverse("home:catalogo")
        params = {
            "categoria": [str(self.cat1.id)],
            "marca": [str(self.m1.id)],
            "color": ["rojo"],
            "material": ["plastico"],
            "min": "10",
            "max": "25",
        }
        resp = self.client.get(url, params)
        productos = list(resp.context["productos"])
        self.assertIn(self.p1, productos)
        self.assertNotIn(self.p2, productos)

    def test_product_list_view_context_incluye_filtros_disponibles(self):
        url = reverse("home:catalogo")
        resp = self.client.get(url, {"categoria": [str(self.cat1.id)], "color": ["rojo"]})
        ctx = resp.context
        self.assertIn(self.cat1, list(ctx["categorias"]))
        self.assertIn(self.m1, list(ctx["marcas"]))
        self.assertIn("color", ctx)
        self.assertIn("material", ctx)
        self.assertEqual(ctx["selected_categorias"], [str(self.cat1.id)])
        self.assertEqual(ctx["selected_colores"], ["rojo"])


class ProductoDetalleViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Categoria.objects.create(nombre="Aves")
        self.marca = Marca.objects.create(nombre="BirdBrand")
        self.prod = Producto.objects.create(
            nombre="Comedero",
            descripcion="Comedero",
            precio=12.00,
            categoria=self.cat,
            marca=self.marca,
        )

    # def test_detalle_producto(self):
    #     url = reverse("home:producto_detalle", kwargs={"pk": self.prod.pk})
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertTemplateUsed(resp, "home/producto_detalle.html")
    #     self.assertEqual(resp.context["producto"], self.prod)


class CartAndCheckoutViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Categoria.objects.create(nombre="Peces")
        self.marca = Marca.objects.create(nombre="FishBrand")
        self.prod = Producto.objects.create(
            nombre="Pecera",
            descripcion="Pecera grande",
            precio=100.00,
            categoria=self.cat,
            marca=self.marca,
        )
        self.user = User.objects.create_user(
            username="cliente_cart",
            email="cart@example.com",
            password="testcart123",
            telefono="600000003",
            direccion="Calle 4",
            ciudad="Bilbao",
            codigo_postal="48000",
        )
        self.carrito = Carrito.objects.create(codigo_carrito="CARTCODE1")
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.prod, cantidad=1)

    def test_cart_view_template(self):
        url = reverse("home:carrito")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "cart.html")

    # def test_add_to_cart_redirige_carrito(self):
    #     url = reverse("home:add_to_cart", kwargs={"pk": self.prod.pk})
    #     resp = self.client.get(url)
    #     self.assertRedirects(resp, reverse("home:carrito"))

    # def test_remove_from_cart_redirige_carrito(self):
        # url = reverse("home:remove_from_cart", kwargs={"item_id": 1})
        # resp = self.client.get(url)
        # self.assertRedirects(resp, reverse("home:carrito"))

    def test_checkout_requires_authentication(self):
        url = reverse("home:create_checkout_session")
        data = {"cart_code": "ALGUNO", "email": "test@example.com"}

        # Sin login → 403
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

def test_checkout_authenticated_user_ok(self):
        url = reverse("home:create_checkout_session")
        data = {"cart_code": "ALGUNO", "email": "test@example.com"}

        self.client.login(username="cliente_cart", password="testcart123")

        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)



class StripeCheckoutAndWebhookTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.cat = Categoria.objects.create(nombre="Reptiles")
        self.marca = Marca.objects.create(nombre="RepBrand")
        self.prod = Producto.objects.create(
            nombre="Terrario",
            descripcion="Terrario",
            precio=150.00,
            categoria=self.cat,
            marca=self.marca,
        )
        self.cart = Carrito.objects.create(codigo_carrito="STRIPECART1")
        ItemCarrito.objects.create(carrito=self.cart, producto=self.prod, cantidad=2)

    from rest_framework.test import APIClient
    from django.contrib.auth import get_user_model

    # def test_create_checkout_session_missing_cart_returns_400(self):
    #     url = reverse("home:create_checkout_session")
    #     data = {"cart_code": "NO_EXISTE", "email": "test@example.com"}

    #     user = get_user_model().objects.get(username="cliente_cart")
    #     self.api_client.force_authenticate(user=user)

    #     resp = self.api_client.post(url, data, format="json")
    #     self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_success_and_cancel_views(self):
        success_url = reverse("home:success")
        cancel_url = reverse("home:cancel")

        r1 = self.client.get(success_url)
        r2 = self.client.get(cancel_url)

        self.assertEqual(r1.status_code, 200)
        self.assertTemplateUsed(r1, "home/success.html")
        self.assertEqual(r2.status_code, 200)
        self.assertTemplateUsed(r2, "home/cancel.html")
