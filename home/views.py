from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView
import uuid

from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponse

from .forms import ClienteRegistrationForm
from .models import Categoria, Producto, Carrito, ItemCarrito

from django.conf import settings
import stripe

from rest_framework.response import Response

from rest_framework.decorators import api_view

from home import models

stripe.api_key = settings.STRIPE_SECRET_KEY

# Páginas informativas
class HomeView(TemplateView):
    template_name = "home/inicio.html"

class AboutView(TemplateView):
    template_name = "home/acerca.html"

class ContactView(TemplateView):
    template_name = "home/contacto.html"

class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        cliente = request.user
        resp = super().post(request, *args, **kwargs)      
        if cliente.is_authenticated and cliente.is_anonymous_user:
            cliente.delete()
        return resp

def invitado_view(request):
    nuevo_cliente = models.Cliente.objects.create(
        username=f"guest_{uuid.uuid4()}",
        email=f"guest_{uuid.uuid4()}@example.com",
        telefono="0000000000",
        direccion="Dirección de prueba",
        ciudad="Ciudad de prueba",
        codigo_postal="00000",
        is_anonymous_user=True
    )
    nuevo_cliente.set_unusable_password()
    nuevo_cliente.save()
    login(request, nuevo_cliente)
    return redirect("home:catalogo")

def register_view(request):
    form = ClienteRegistrationForm()
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("home:catalogo")
        return render(request, "registration/registro.html", {"form": form})
    if request.method == "POST":
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Carrito.objects.get_or_create(cliente=user)
            return redirect("home:catalogo")
    return render(request, "registration/registro.html", {"form": form})


def cart_view(request):
    return render(request, "cart.html")

# Catálogo (mínimo)
class CategoryListView(ListView):
    model = Categoria
    template_name = "home/categorias.html"
    context_object_name = "categorias"

class ProductListView(ListView):
    model = Producto
    template_name = "home/lista_productos.html"
    context_object_name = "productos"
    paginate_by = 12

class ProductDetailView(DetailView):
    model = Producto
    template_name = "home/producto_detalle.html"
    context_object_name = "producto"


# Carrito simple
class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        # Usuario autenticado -> usar modelo Carrito
        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
            ctx["carrito"] = carrito
            ctx["total"] = carrito.total
        else:
            # Carrito en sesión: {"<producto_pk>": cantidad}
            session_cart = request.session.get("cart", {})
            items = []
            total = 0
            if session_cart:
                pks = [int(pk) for pk in session_cart.keys()]
                productos = Producto.objects.filter(pk__in=pks)
                prod_map = {p.pk: p for p in productos}
                for pk_str, qty in session_cart.items():
                    try:
                        pk = int(pk_str)
                        cantidad = int(qty)
                    except (TypeError, ValueError):
                        continue
                    producto = prod_map.get(pk)
                    if not producto:
                        continue
                    subtotal = producto.precio_final * cantidad
                    total += subtotal
                    items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
            ctx["cart_items"] = items
            ctx["total"] = total
        return ctx

def add_to_cart(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    # Si el usuario está autenticado, persistir en modelo
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
        item, created = ItemCarrito.objects.get_or_create(
            carrito=carrito, producto=producto, talla=""
        )
        if not created:
            item.cantidad += 1
        item.save()
        return redirect("home:carrito")

    # Usuario anónimo -> usar sesión
    session_cart = request.session.get("cart", {})
    key = str(producto.pk)
    session_cart[key] = int(session_cart.get(key, 0)) + 1
    request.session["cart"] = session_cart
    request.session.modified = True
    return redirect("home:carrito")

def remove_from_cart(request, item_id):
    # Si está autenticado, eliminar por id de ItemCarrito
    if request.user.is_authenticated:
        ItemCarrito.objects.filter(id=item_id, carrito__cliente=request.user).delete()
        return redirect("home:carrito")

    # Para anónimos, item_id se interpreta como pk de Producto en la sesión
    session_cart = request.session.get("cart", {})
    key = str(item_id)
    if key in session_cart:
        session_cart.pop(key)
        request.session["cart"] = session_cart
        request.session.modified = True
    return redirect("home:carrito")


# Checkout (placeholders)
class CheckoutEntregaView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_entrega.html"

class CheckoutPagoView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_pago.html"

class CheckoutConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_confirmacion.html"
    

def enviar_correo(pedido):
    asunto = f"Confirmación de tu pedido #{pedido.stripe_checkout_id}"
    to_email = [pedido.cliente_email]

    items_con_subtotal = []
    # Revisar con lo de oscar
    for item in pedido.pedido_items.all(): 
        subtotal = item.producto.precio_final * item.cantidad
        item.subtotal = subtotal 
        
        imagen_principal = item.producto.imagenes.filter(es_principal=True).first()
        item.imagen_url = imagen_principal.imagen if imagen_principal else ""   #Añadir una foto
    
        items_con_subtotal.append(item)

    context = {
        "pedido": pedido,
        "items_con_subtotal": items_con_subtotal,
    }

    html_content = render_to_string("email/confirmacion.html", context)

    correo = EmailMultiAlternatives(asunto, html_content, to_email)
    correo.send(fail_silently=False) #Para que no pete la app si falla, quitar al final


from django.http import HttpResponse
class MockImage:
    def __init__(self, url):
        self.imagen = url

class MockImageManager:
    def __init__(self, url):
        self.url = url
    def first(self):
        return MockImage(self.url) if self.url else None

class MockProduct:
    def __init__(self, nombre, precio, imagen_url):
        self.nombre = nombre
        self.precio_final = precio # Usamos precio_final directamente
        # Simulamos el related_name="imagenes" y el método .first()
        self.imagenes = MockImageManager(imagen_url)

class MockItemPedido:
    def __init__(self, producto, cantidad):
        self.producto = producto
        self.cantidad = cantidad
        # Calculamos subtotal para el template
        self.subtotal = "{:.2f}".format(producto.precio_final * cantidad)

class MockPedido:
    def __init__(self, checkout_id, total, email):
        self.stripe_checkout_id = checkout_id
        self.status = "Paid"
        self.cantidad = total
        self.cliente_email = email

class MockCliente:
    def __init__(self, nombre, direccion, ciudad, cp):
        self.username = nombre
        self.first_name = nombre.split()[0]
        self.last_name = nombre.split()[1] if len(nombre.split()) > 1 else ""
        self.direccion = direccion
        self.ciudad = ciudad
        self.codigo_postal = cp
        self.telefono = "+34 600 00 00 00"

def prueba_correo_pedido_simulado(request):
    """
    Simula un pedido usando la foto del perro y el remitente CORRECTO.
    """
    
    url_perro = "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=300&q=80"

    prod1 = MockProduct("Cachorro Boyero de Berna (Macho)", 1200.00, url_perro)
    prod2 = MockProduct("Cachorro Boyero de Berna (Hembra)", 1200.00, url_perro)
    
    items = [MockItemPedido(prod1, 1), MockItemPedido(prod2, 1)]
    cliente_mock = MockCliente("Pablo Arrabal", "Av. Reina Mercedes 17", "Sevilla, España", "41012")
    pedido_mock = MockPedido("ORD-3295815", "2400.00", "entertainpet2025@gmail.com")

    html_content = render_to_string("email/confirmacion.html", {
        "pedido": pedido_mock,
        "items_con_subtotal": items,
        "cliente": cliente_mock
    })

    # --- AQUÍ ESTÁ EL CAMBIO ---
    remitente = "noreply@entertainpet.com"
    # ---------------------------

    asunto = "Confirmación de Pedido (Remitente Correcto)"
    msg = EmailMultiAlternatives(asunto, "Gracias por tu compra.", remitente, [pedido_mock.cliente_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    return HttpResponse(f"Correo enviado desde <strong>{remitente}</strong>")