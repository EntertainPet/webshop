from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import uuid

from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from email.mime.image import MIMEImage
import os
from django.http import HttpResponse
from django.templatetags.static import static
import urllib.request

from .forms import ClienteRegistrationForm

from .models import Categoria, Cliente, Marca, Producto, Carrito, ItemCarrito, Pedido, ItemPedido


from django.conf import settings
import stripe

from rest_framework.response import Response

from rest_framework.decorators import api_view
from django.db.models import Q

from home import models

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.WEBHOOK_SECRET

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

    def get_queryset(self):
        qs = super().get_queryset().filter(esta_disponible=True)

        # --- Obtener parámetros GET ---
        q = self.request.GET.get("q", "")
        categoria = self.request.GET.getlist("categoria", [])
        marca = self.request.GET.getlist("marca", [])
        precio_min = self.request.GET.get("min", "")
        precio_max = self.request.GET.get("max", "")
        color = self.request.GET.getlist("color", [])
        material = self.request.GET.getlist("material", [])

        # --- Búsqueda ---
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q)
            )

        # --- Filtros ---
        if categoria:
            qs = qs.filter(categoria__id__in=categoria)

        if marca:
            qs = qs.filter(marca__id__in=marca)

        if material:
            qs = qs.filter(material__in=material)
        
        if color:
            qs = qs.filter(color__in=color)

        if precio_min:
            qs = qs.filter(precio__gte = precio_min)

        if precio_max:
            qs = qs.filter(precio__lte =precio_max)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Categoria.objects.all()
        ctx["marcas"] = Marca.objects.all()
        ctx["color"] = Producto.objects.exclude(color = "").values_list("color", flat=True).distinct()
        ctx["material"] = Producto.objects.exclude(material = "").values_list("material", flat=True).distinct()
        ctx["search"] = self.request.GET.get("q", "")


        ctx["selected_categorias"] = self.request.GET.getlist("categoria")
        ctx["selected_marcas"] = self.request.GET.getlist("marca")
        ctx["selected_colores"] = self.request.GET.getlist("color")
        ctx["selected_materiales"] = self.request.GET.getlist("material")
        return ctx

class ProductDetailView(DetailView):
    model = Producto
    template_name = "home/producto_detalle.html"
    context_object_name = "producto"


# Carrito simple
class CartView(TemplateView):
    template_name = "cart.html"

    # def get_context_data(self, **kwargs):
    #     ctx = super().get_context_data(**kwargs)
    #     request = self.request
    #     # Usuario autenticado -> usar modelo Carrito
    #     if request.user.is_authenticated:
    #         carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
    #         ctx["carrito"] = carrito
    #         ctx["total"] = carrito.total
    #     else:
    #         # Carrito en sesión: {"<producto_pk>": cantidad}
    #         session_cart = request.session.get("cart", {})
    #         items = []
    #         total = 0
    #         if session_cart:
    #             pks = [int(pk) for pk in session_cart.keys()]
    #             productos = Producto.objects.filter(pk__in=pks)
    #             prod_map = {p.pk: p for p in productos}
    #             for pk_str, qty in session_cart.items():
    #                 try:
    #                     pk = int(pk_str)
    #                     cantidad = int(qty)
    #                 except (TypeError, ValueError):
    #                     continue
    #                 producto = prod_map.get(pk)
    #                 if not producto:
    #                     continue
    #                 subtotal = producto.precio_final * cantidad
    #                 total += subtotal
    #                 items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
    #         ctx["cart_items"] = items
    #         ctx["total"] = total
    #     return ctx

def add_to_cart(request, pk):
    # producto = get_object_or_404(Producto, pk=pk)
    # # Si el usuario está autenticado, persistir en modelo
    # if request.user.is_authenticated:
    #     carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
    #     item, created = ItemCarrito.objects.get_or_create(
    #         carrito=carrito, producto=producto, talla=""
    #     )
    #     if not created:
    #         item.cantidad += 1
    #     item.save()
    #     return redirect("home:carrito")

    # # Usuario anónimo -> usar sesión
    # session_cart = request.session.get("cart", {})
    # key = str(producto.pk)
    # session_cart[key] = int(session_cart.get(key, 0)) + 1
    # request.session["cart"] = session_cart
    # request.session.modified = True
    return redirect("home:carrito")

def remove_from_cart(request, item_id):
    # # Si está autenticado, eliminar por id de ItemCarrito
    # if request.user.is_authenticated:
    #     ItemCarrito.objects.filter(id=item_id, carrito__cliente=request.user).delete()
    #     return redirect("home:carrito")

    # # Para anónimos, item_id se interpreta como pk de Producto en la sesión
    # session_cart = request.session.get("cart", {})
    # key = str(item_id)
    # if key in session_cart:
    #     session_cart.pop(key)
    #     request.session["cart"] = session_cart
    #     request.session.modified = True
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
    FROM_EMAIL = "entertainpet2025@gmail.com"
    to_email = [pedido.cliente_email]

    items_con_subtotal = [
        {
            "producto": item.producto,
            "cantidad": item.cantidad,
            "subtotal": item.producto.precio_final * item.cantidad,
            "imagen_url": getattr(item.producto.imagenes.filter(es_principal=True).first(), "imagen", None),
        }
        for item in pedido.pedido_items.select_related("producto")
    ]

    cliente = Cliente.objects.filter(email=pedido.cliente_email).first()

    context = {
        "pedido": pedido,
        "items_con_subtotal": items_con_subtotal,
        "cliente": cliente,
    }

    html_content = render_to_string("email/confirmacion.html", context)
    correo = EmailMultiAlternatives(asunto, "", FROM_EMAIL, to_email)
    correo.attach_alternative(html_content, "text/html")

    correo.send(fail_silently=False)
@api_view(['POST'])
def create_checkout_session(request):
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")
    cart = Carrito.objects.get(codigo_carrito=cart_code)
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email= email,
            payment_method_types=['card'],


            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item.producto.nombre},
                        'unit_amount': int(item.producto.precio * 100),  # Amount in cents
                    },
                    'quantity': item.cantidad,
                }
                for item in cart.carrito_items.all()
            ] + [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'VAT Fee'},
                        'unit_amount': 500,  # $5 in cents
                    },
                    'quantity': 1,
                }
            ],
           
            mode='payment',
            success_url="https://0686e37fcb6f.ngrok-free.app/success",
            cancel_url="https://0686e37fcb6f.ngrok-free.app/cancel",
            metadata = {"cart_code": cart_code}
        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@csrf_exempt
def my_webhook_view(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  if (
    event['type'] == 'checkout.session.completed'
    or event['type'] == 'checkout.session.async_payment_succeeded'
  ):
    session = event['data']['object']
    cart_code = session.get("metadata", {}).get("cart_code")

    print("creando pedido")
    fulfill_checkout(session, cart_code)

  return HttpResponse(status=200)



def fulfill_checkout(session, cart_code):
    
    order = Pedido.objects.create(stripe_checkout_id=session["id"],
        cantidad=session["amount_total"],
        divisa=session["currency"],
        cliente_email=session["customer_email"],
        status="Paid")
    print("pedido creado")

    cart = Carrito.objects.get(codigo_carrito=cart_code)
    cartitems = cart.carrito_items.all()

    for item in cartitems:
        orderitem = ItemPedido.objects.create(pedido=order, producto=item.producto, 
                                             cantidad=item.cantidad)
    
    try:
        enviar_correo(order)
    except Exception as e:
        print("Error enviando correo:", e)
        
    cart.delete()

def success_view(request):

    return render(request, "home/success.html")


def cancel_view(request):
    return render(request, "home/cancel.html")
