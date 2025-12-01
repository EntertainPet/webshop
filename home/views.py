from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from django.db.models.functions import Coalesce

import uuid
import secrets

from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from email.mime.image import MIMEImage
import os
from django.http import HttpResponse
from django.templatetags.static import static
import urllib.request

from .forms import ClienteRegistrationForm
from .models import (
    Categoria, Marca, Producto, Carrito, ItemCarrito, 
    Pedido, ItemPedido, TallaProducto, Cliente
)

from django.conf import settings
import stripe
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.http import JsonResponse
from django.db.models import Count

from home import models

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.WEBHOOK_SECRET


# ============================================
# UTILIDADES
# ============================================

def get_or_create_carrito(request):
    """
    Obtiene o crea un carrito para el usuario actual.
    - Si está autenticado: usa/crea carrito en BD asociado al cliente
    - Si es anónimo: usa/crea carrito en sesión
    """
    if request.user.is_authenticated:
        carrito, created = Carrito.objects.get_or_create(cliente=request.user)
        return carrito
    else:
        # Carrito en sesión: {"producto_id-talla_id": cantidad}
        if 'cart' not in request.session:
            request.session['cart'] = {}
        return None  # Indicamos que es carrito de sesión


def get_cart_items_from_session(request):
    """
    Convierte el carrito de sesión en una lista de items procesables.
    Retorna lista de diccionarios: {"producto": Producto, "talla_producto": TallaProducto, "cantidad": int}
    """
    session_cart = request.session.get('cart', {})
    items = []
    
    for key, cantidad in session_cart.items():
        try:
            producto_id, talla_producto_id = key.split('-')
            producto = Producto.objects.get(pk=int(producto_id))
            talla_producto = TallaProducto.objects.get(pk=int(talla_producto_id))
            items.append({
                "producto": producto,
                "talla_producto": talla_producto,
                "cantidad": cantidad,
                "subtotal": producto.precio_final * cantidad,
                "key": key
            })
        except (ValueError, Producto.DoesNotExist, TallaProducto.DoesNotExist):
            continue
    
    return items


def merge_session_cart_to_user(request, user):
    """
    Fusiona el carrito de sesión con el carrito del usuario al hacer login/registro.
    """
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return
    
    carrito, _ = Carrito.objects.get_or_create(cliente=user)
    
    for key, cantidad in session_cart.items():
        try:
            producto_id, talla_producto_id = key.split('-')
            producto = Producto.objects.get(pk=int(producto_id))
            talla_producto = TallaProducto.objects.get(pk=int(talla_producto_id))
            
            # Fusionar: si ya existe el item, sumar cantidades
            item, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                talla_producto=talla_producto,
                defaults={"cantidad": cantidad}
            )
            if not created:
                item.cantidad += cantidad
                item.save()
        except (ValueError, Producto.DoesNotExist, TallaProducto.DoesNotExist):
            continue
    
    # Limpiar sesión
    request.session['cart'] = {}
    request.session.modified = True


# ============================================
# PÁGINAS INFORMATIVAS
# ============================================

class HomeView(TemplateView):
    template_name = "home/inicio.html"


class AboutView(TemplateView):
    template_name = "home/acerca.html"


class ContactView(TemplateView):
    template_name = "home/contacto.html"


# ============================================
# AUTENTICACIÓN
# ============================================

class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        cliente = request.user
        resp = super().post(request, *args, **kwargs)
        if cliente.is_authenticated and cliente.is_anonymous_user:
            cliente.delete()
        return resp


def invitado_view(request):
    """Crea un usuario invitado temporal y lo autentica."""
    nuevo_cliente = Cliente.objects.create(
        username=f"guest_{uuid.uuid4().hex[:8]}",
        email=f"guest_{uuid.uuid4().hex[:8]}@example.com",
        telefono="0000000000",
        direccion="Dirección de prueba",
        ciudad="Ciudad de prueba",
        codigo_postal="00000",
        is_anonymous_user=True
    )
    nuevo_cliente.set_unusable_password()
    nuevo_cliente.save()
    login(request, nuevo_cliente)
    
    # Fusionar carrito de sesión
    merge_session_cart_to_user(request, nuevo_cliente)
    
    if not request.session.get("cart_code"):
        cart_code = f"CRT-{uuid.uuid4().hex[:8].upper()}"
        Carrito.objects.create(codigo_carrito=cart_code)
        request.session["cart_code"] = cart_code
    return redirect("home:catalogo")


def register_view(request):
    """Registro de usuario."""
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("home:catalogo")
        form = ClienteRegistrationForm()
        return render(request, "registration/registro.html", {"form": form})
    
    if request.method == "POST":
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Fusionar carrito de sesión
            merge_session_cart_to_user(request, user)
            
            if not request.session.get("cart_code"):
                cart_code = f"CRT-{uuid.uuid4().hex[:8].upper()}"
                Carrito.objects.create(codigo_carrito=cart_code)
                request.session["cart_code"] = cart_code
            return redirect("home:catalogo")
    return render(request, "registration/registro.html", {"form": form})


# ============================================
# CATÁLOGO
# ============================================

class ProductListView(ListView):
    model = Producto
    template_name = "home/lista_productos.html"
    context_object_name = "productos"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().filter(esta_disponible=True)

        q = self.request.GET.get("q", "")
        categoria = self.request.GET.getlist("categoria", [])
        marca = self.request.GET.getlist("marca", [])
        precio_min = self.request.GET.get("min", "")
        precio_max = self.request.GET.get("max", "")
        color_ids = self.request.GET.getlist("color", []) 
        material = self.request.GET.getlist("material", [])

        qs = qs.annotate(
                stock_tallas=Sum("tallas__stock"),
            ).annotate(
                stock_total=Coalesce("stock_tallas", F("stock"))
            )
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        if categoria:
            qs = qs.filter(categoria__id__in=categoria)
        if marca:
            qs = qs.filter(marca__id__in=marca)
        if material:
            qs = qs.filter(material__in=material)
        if color_ids:
            qs = qs.filter(colores__id__in=color_ids)

        if precio_min:
            qs = qs.filter(precio__gte=precio_min)
        if precio_max:
            qs = qs.filter(precio__lte=precio_max)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Categoria.objects.all()
        ctx["marcas"] = Marca.objects.all()
        ctx["colores"] = models.Color.objects.all()
        ctx["material"] = Producto.objects.exclude(material="").values_list("material", flat=True).distinct()
        ctx["search"] = self.request.GET.get("q", "")
        ctx["selected_categorias"] = self.request.GET.getlist("categoria")
        ctx["selected_marcas"] = self.request.GET.getlist("marca")
        ctx["selected_colores"] = [int(c) for c in self.request.GET.getlist("color") if c.isdigit()]
        ctx["selected_materiales"] = self.request.GET.getlist("material")
        ctx["productos_destacados"] = Producto.objects.filter(
            es_destacado=True,
            esta_disponible=True
        )[:12]
        ctx["min_value"] = self.request.GET.get("min", "")
        ctx["max_value"] = self.request.GET.get("max", "")
        return ctx
    

def autocomplete_productos(request):
    q = request.GET.get("q", "")
    productos = Producto.objects.filter(
        Q(nombre__icontains=q) | Q(descripcion__icontains=q),
        esta_disponible=True
    )[:6]

    data = [{
        "nombre": p.nombre,
        "slug": p.slug,
        "precio": float(p.precio),
        "imagen": p.imagenes.first().imagen if p.imagenes.exists() else None
    } for p in productos]

    return JsonResponse(data, safe=False)


class ProductDetailView(DetailView):
    model = Producto
    template_name = "producto_detalle.html"
    context_object_name = "producto"


# ============================================
# CARRITO
# ============================================

def add_to_cart(request, pk):
    """Añade un producto al carrito."""
    if request.method != "POST":
        return redirect("home:catalogo")
    
    producto = get_object_or_404(Producto, pk=pk)
    talla_producto_id = request.POST.get("talla_producto_id")
    
    # Validación de cantidad con límite máximo de seguridad
    try:
        cantidad = int(request.POST.get("cantidad", 1))
        if cantidad <= 0 or cantidad > 99:  # Límite de seguridad
            messages.error(request, "La cantidad debe estar entre 1 y 99.")
            return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
    except (ValueError, TypeError):
        messages.error(request, "Cantidad no válida.")
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))

    # Validación correcta de talla
    if not talla_producto_id or talla_producto_id in ["", "None", None]:
        messages.error(request, "Debes seleccionar una talla antes de añadir el producto.")
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))

    try:
        talla_producto = TallaProducto.objects.get(pk=int(talla_producto_id), producto=producto)
    except (ValueError, TallaProducto.DoesNotExist):
        messages.error(request, "La talla seleccionada no es válida.")
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))

    
       # Helper to build stock message
    def build_stock_message(talla_producto, producto):
        if talla_producto.talla == "Única" or producto.tallas.count() <= 1:
            return f"Solo quedan {talla_producto.stock} unidades disponibles."
        return f"Solo quedan {talla_producto.stock} unidades disponibles de la talla {talla_producto.talla}."

    # Validate available stock
    if cantidad > talla_producto.stock:
        messages.error(request, build_stock_message(talla_producto, producto))
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
    
    # Authenticated user
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
        item, created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            talla_producto=talla_producto,
            defaults={"cantidad": cantidad}
        )
        if not created:
            nueva_cantidad = item.cantidad + cantidad
            if nueva_cantidad > talla_producto.stock:
                messages.error(request, build_stock_message(talla_producto, producto))
                return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
            item.cantidad = nueva_cantidad
            item.save()
        messages.success(request, f"{producto.nombre} añadido al carrito.")
    else:
        # Anonymous user: session
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        key = f"{producto.pk}-{talla_producto.pk}"
        current_qty = request.session['cart'].get(key, 0)
        nueva_cantidad = current_qty + cantidad
        
        if nueva_cantidad > talla_producto.stock:
            messages.error(request, build_stock_message(talla_producto, producto))
            return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
        
        request.session['cart'][key] = nueva_cantidad
        request.session.modified = True
        messages.success(request, f"{producto.nombre} añadido al carrito.")
    
    return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))

def update_cart_item(request, item_id):
    """Actualiza la cantidad de un item en el carrito."""
    if request.method != "POST":
        return redirect("home:carrito")
    
    action = request.POST.get("action")  # "increase" o "decrease"
    
    if request.user.is_authenticated:
        item = get_object_or_404(ItemCarrito, pk=item_id, carrito__cliente=request.user)
        
        if action == "increase":
            if item.cantidad + 1 > item.talla_producto.stock:
                messages.error(request, f"Solo quedan {item.talla_producto.stock} unidades disponibles.")
            else:
                item.cantidad += 1
                item.save()
                messages.success(request, "Cantidad actualizada.")
        elif action == "decrease":
            if item.cantidad > 1:
                item.cantidad -= 1
                item.save()
                messages.success(request, "Cantidad actualizada.")
            else:
                messages.warning(request, "La cantidad mínima es 1. Usa 'Eliminar' para quitar el producto.")
    else:
        # Sesión
        key = request.POST.get("key")
        if key and 'cart' in request.session and key in request.session['cart']:
            if action == "increase":
                request.session['cart'][key] += 1
            elif action == "decrease":
                if request.session['cart'][key] > 1:
                    request.session['cart'][key] -= 1
            request.session.modified = True
            messages.success(request, "Cantidad actualizada.")
    
    return redirect("home:carrito")


def remove_from_cart(request, item_id):
    """Elimina un item del carrito."""
    if request.user.is_authenticated:
        ItemCarrito.objects.filter(id=item_id, carrito__cliente=request.user).delete()
        messages.success(request, "Producto eliminado del carrito.")
    else:
        # Para sesión, item_id es el "key"
        key = str(item_id)
        if 'cart' in request.session and key in request.session['cart']:
            del request.session['cart'][key]
            request.session.modified = True
            messages.success(request, "Producto eliminado del carrito.")
    
    return redirect("home:carrito")


# CARRITO DE SESIÓN
from django.views.decorators.http import require_POST

@require_POST
def carrito_update_session_item(request):
    """Actualizar cantidad de item en carrito de sesión (usuarios no autenticados)"""
    key = request.POST.get('key')
    action = request.POST.get('action')
    
    cart = request.session.get('cart', {})
    
    if key in cart:
        if action == 'increase':
            # Verificar stock antes de aumentar
            try:
                producto_id, talla_producto_id = key.split('-')
                talla = TallaProducto.objects.get(pk=int(talla_producto_id))
                if cart[key] < talla.stock:
                    cart[key] += 1
                    messages.success(request, 'Cantidad actualizada')
                else:
                    messages.warning(request, 'No hay más stock disponible')
            except (ValueError, TallaProducto.DoesNotExist):
                messages.error(request, 'Producto no encontrado')
        elif action == 'decrease':
            if cart[key] > 1:
                cart[key] -= 1
                messages.success(request, 'Cantidad actualizada')
            else:
                messages.warning(request, 'La cantidad mínima es 1')
        
        request.session['cart'] = cart
        request.session.modified = True
    
    return redirect('home:carrito')

class CheckoutConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_confirmacion.html"
    
def enviar_correo(pedido):
    asunto = f"Confirmación de tu pedido #{pedido.stripe_checkout_id}"
    FROM_EMAIL = "entertainpet2025@gmail.com"
    to_email = [pedido.cliente_email]
    
    dom = "http://localhost:8000"
    seguimiento_url = dom + reverse("home:seguimiento_token", args=[pedido.seguimiento_token])   
    
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
        "seguimiento_url": seguimiento_url,
    }

    html_content = render_to_string("email/confirmacion.html", context)
    correo = EmailMultiAlternatives(asunto, "", FROM_EMAIL, to_email)
    correo.attach_alternative(html_content, "text/html")

    correo.send(fail_silently=False)

@require_POST
def carrito_remove_session_item(request):
    """Eliminar item del carrito de sesión (usuarios no autenticados)"""
    key = request.POST.get('key')
    
    cart = request.session.get('cart', {})
    
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Producto eliminado del carrito')
    
    return redirect('home:carrito')

class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request

        # Lógica para obtener el email solo si es un usuario real
        client_email = ""
        if request.user.is_authenticated:
            # Verificamos que no sea un usuario invitado temporal (flag is_anonymous_user del modelo Cliente)
            if not getattr(request.user, 'is_anonymous_user', False):
                client_email = request.user.email

            # Lógica existente del carrito autenticado
            carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
            
            ctx["carrito"] = carrito
            ctx["cart_items"] = carrito.carrito_items.all()
            ctx["total"] = carrito.total
            ctx["codigo_carrito"] = carrito.codigo_carrito
            ctx["cantidad_items"] = carrito.cantidad_total_items
        else:
            # Lógica existente del carrito de sesión
            items = get_cart_items_from_session(request)
            ctx["cart_items"] = items
            ctx["total"] = sum(item["subtotal"] for item in items)
            ctx["cantidad_items"] = sum(item["cantidad"] for item in items)
        
        # --- AÑADIDO ---
        ctx["client_email"] = client_email
        
        return ctx

from rest_framework.test import APIRequestFactory
def invitado_compra_view(request):
    """Crea un usuario invitado temporal y lo autentica, y procesa la compra correctamente."""

    # 1. Crear usuario invitado
    nuevo_cliente = Cliente.objects.create(
        username=f"guest_{uuid.uuid4().hex[:8]}",
        email=f"guest_{uuid.uuid4().hex[:8]}@example.com",
        telefono="0000000000",
        direccion="Dirección de prueba",
        ciudad="Ciudad de prueba",
        codigo_postal="00000",
        is_anonymous_user=True
    )
    nuevo_cliente.set_unusable_password()
    nuevo_cliente.save()
    login(request, nuevo_cliente)

    # 2. Fusionar carrito de sesión al usuario
    merge_session_cart_to_user(request, nuevo_cliente)

    # 3. OBTENER el carrito real del usuario
    carrito = Carrito.objects.filter(cliente=nuevo_cliente).first()

    if not carrito:
        return JsonResponse({"error": "El usuario no tiene carrito"}, status=400)

    cart_code = carrito.codigo_carrito

    # 4. Enviar cart_code correcto al endpoint de Stripe
    factory = APIRequestFactory()
    stripe_request = factory.post(
        '/create_checkout_session/', 
        {"cart_code": cart_code}, 
        format='json'
    )

    # IMPORTANTE: Copiar host y esquema del request actual para que 
    # Stripe reciba las URLs de success/cancel correctas del dominio real
    stripe_request.META['HTTP_HOST'] = request.META['HTTP_HOST']
    stripe_request.META['wsgi.url_scheme'] = request.scheme

    # 5. Llamar a la vista directamente como función
    response = create_checkout_session(stripe_request)

    if response.status_code == 200:
        # Al ser llamada interna, response.data mantiene el objeto Python original
        # (El objeto Session de Stripe)
        checkout_session = response.data['data']
        
        # Accedemos a la propiedad url del objeto Stripe y redirigimos
        return redirect(checkout_session.url)
    else:
        return JsonResponse(response.data, status=response.status_code)



# ============================================
# CHECKOUT
# ============================================

def guest_checkout_view(request):
    """Vista para que invitados ingresen email antes de pagar."""
    # Obtener items del carrito
    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(cliente=request.user).first()
        cart_items = carrito.carrito_items.all() if carrito else []
        total = carrito.total if carrito else 0
    else:
        items = get_cart_items_from_session(request)
        cart_items = items
        total = sum(item["subtotal"] for item in items)
    
    if not cart_items:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("home:carrito")
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        
        # Validación más robusta del email
        if not email:
            messages.error(request, "Debes ingresar un email válido.")
            return render(request, "guest_checkout.html", {"total": total, "cart_items": cart_items})
        
        # Verificar formato del email
        if "@" not in email or "." not in email.split("@")[-1]:
            messages.error(request, "El formato del email no es válido.")
            return render(request, "guest_checkout.html", {"total": total, "cart_items": cart_items})
        
        # Verificar longitud del email
        if len(email) > 254:  # RFC 5321 limit
            messages.error(request, "El email es demasiado largo.")
            return render(request, "guest_checkout.html", {"total": total, "cart_items": cart_items})
        
        # Generar código de seguimiento
        codigo_seguimiento = secrets.token_urlsafe(8).upper()
        
        # Guardar en sesión para usar en stripe checkout
        request.session['guest_email'] = email
        request.session['codigo_seguimiento'] = codigo_seguimiento
        request.session.modified = True
        
        # Redirigir a proceso de pago (Stripe)
        return redirect("home:process_payment")
    
    return render(request, "guest_checkout.html", {"total": total, "cart_items": cart_items})

import requests
import json

def process_payment_view(request):
    """Procesa el pago y redirige a Stripe."""
    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(cliente=request.user).first()
        email = request.user.email
        codigo_carrito = carrito.codigo_carrito if carrito else ""
    else:
        email = request.session.get('guest_email')
        codigo_carrito = f"GUEST-{uuid.uuid4().hex[:8].upper()}"
        if not email:
            messages.error(request, "Debes ingresar tu email primero.")
            return redirect("home:guest_checkout")
    
    # Aquí iría la lógica de Stripe checkout
    messages.info(request, "Redirigiendo a pasarela de pago...")
    # Por ahora redirect temporal
    return redirect("home:carrito")


class OrderHistoryListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = "home/historial_pedidos.html"
    context_object_name = "pedidos"
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Pedido.objects.filter(cliente_email=self.request.user.email)
            .annotate(items_count=Count('pedido_items'))
            .order_by("-fecha_creacion")
        )
        q = self.request.GET.get("q", "")
        status = self.request.GET.get("status", "")
        if q:
            qs = qs.filter(Q(stripe_checkout_id__icontains=q))
        if status:
            qs = qs.filter(status__iexact=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_counts"] = (
            Pedido.objects.filter(cliente_email=self.request.user.email)
            .values("status")
            .annotate(count=Count("id"))
        )
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        # Calculate friendly display amounts (try to detect cents returned by Stripe)
        for pedido in ctx.get('pedidos', []):
            try:
                amount = float(pedido.cantidad)
                pedido.display_amount = amount / 100.0 if amount > 1000 else amount
            except Exception:
                pedido.display_amount = pedido.cantidad
        return ctx


class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = "home/pedido_detalle.html"
    context_object_name = "pedido"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.cliente_email != self.request.user.email:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pedido = self.get_object()
        # compute display amount -- Stripe returns cents in amount_total; try to make a readable amount
        try:
            amount = float(pedido.cantidad)
            if amount > 1000:
                # likely cents
                display_amount = amount / 100.0
            else:
                display_amount = amount
        except Exception:
            display_amount = pedido.cantidad
        ctx["display_amount"] = display_amount
        # Build items detail for the template with computed subtotals
        items_list = []
        for item in pedido.pedido_items.all():
            unit_price = float(item.producto.precio_final)
            subtotal = unit_price * int(item.cantidad)
            items_list.append({
                "producto": item.producto,
                "cantidad": item.cantidad,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })
        ctx["items_list"] = items_list
        # Total sum computed from items
        ctx["total_sum"] = sum(i.get("subtotal", 0) for i in items_list)
        return ctx


@api_view(['POST'])
def create_checkout_session(request):
    """Crea sesión de checkout de Stripe."""
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")
    carrito = Carrito.objects.get(codigo_carrito=cart_code)
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {'name': item.producto.nombre},
                        'unit_amount': int(item.producto.precio_final * 100),
                    },
                    'quantity': item.cantidad,
                }
                for item in carrito.carrito_items.all()
            ] + [
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {'name': 'Gastos de envío'},
                        'unit_amount': 450,
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=request.build_absolute_uri("/success/") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri("/cancel/"),
            metadata={"cart_code": cart_code}
        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@csrf_exempt
def my_webhook_view(request):
    """Webhook de Stripe para confirmar pagos."""
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    print("--- WEBHOOK RECIBIDO ---")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded']:
        session = event['data']['object']
        try:
            cart_code = session.get("metadata", {}).get("cart_code")
            fulfill_checkout(session, cart_code)
            print("🎉 Pedido creado con éxito")
        except Exception as e:
            print(f"❌ Error en fulfill_checkout: {e}") # DEBUG CRÍTICO

    return HttpResponse(status=200)


    
def enviar_correo(pedido):
    asunto = f"Confirmación de tu pedido #{pedido.stripe_checkout_id}"
    FROM_EMAIL = "entertainpet2025@gmail.com"
    to_email = [pedido.cliente_email]
    
    dom = "http://localhost:8000"
    seguimiento_url = dom + reverse("home:seguimiento_token", args=[pedido.seguimiento_token])   
    
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
        "seguimiento_url": seguimiento_url,
    }

    html_content = render_to_string("email/confirmacion.html", context)
    correo = EmailMultiAlternatives(asunto, "", FROM_EMAIL, to_email)
    correo.attach_alternative(html_content, "text/html")

    correo.send(fail_silently=False)
    asunto = f"Confirmación de tu pedido #{pedido.stripe_checkout_id}"
    FROM_EMAIL = "entertainpet2025@gmail.com"
    to_email = [pedido.cliente_email]
    
    dom = "http://localhost:8000"
    seguimiento_url = dom + reverse("home:seguimiento", args=[pedido.id])
    
def fulfill_checkout(session, cart_code):
    """Crea el pedido tras pago exitoso."""
    codigo_seguimiento = secrets.token_urlsafe(8).upper()
    customer_details = session.get("customer_details")
    email = None
    
    if customer_details and customer_details.get("email"):
        email = customer_details.get("email")
    elif session.get("customer_email"):
        email = session.get("customer_email")
    # Fallback por seguridad (aunque no debería ocurrir en pago exitoso)
    if not email:
        print("⚠️ ALERTA: No se encontró email en la sesión de Stripe.")
        email = "no-email@found.com"
    try:
        order = Pedido.objects.create(
            stripe_checkout_id=session["id"],
            cantidad=session["amount_total"] / 100,
            divisa=session["currency"],
            cliente_email=email,
            status="Pagado",
            codigo_seguimiento=codigo_seguimiento,
            estado_envio= Pedido.EstadoEnvio.EN_PREPARACION
        )
        print("pedido creado")
    except Exception as e:
        print("Error creando pedido:", e)

    try:
        carrito = Carrito.objects.get(codigo_carrito=cart_code)
        for item in carrito.carrito_items.all():
            ItemPedido.objects.create(
                pedido=order,
                producto=item.producto,
                cantidad=item.cantidad,
                talla=item.talla_producto.talla
            )
            
            # Descontar stock
            item.talla_producto.stock -= item.cantidad
            item.talla_producto.save()
    except Exception as e:
        print("Error creando ItemPedidos", e)
    
    try:
        enviar_correo(order)
    except Exception as e:
        print("Error enviando correo:", e)
        
    carrito.delete()

import time

def success_view(request):
    session_id = request.GET.get('session_id')
    pedido = None

    if session_id:
        # Intentamos buscar el pedido por el ID de sesión de Stripe
        pedido = Pedido.objects.filter(stripe_checkout_id=session_id).first()
        
        # OPCIONAL: Pequeño "retry" por si el webhook tiene un ligero retraso (race condition)
        # Si no es crítico, puedes omitir este bloque while
        intentos = 0
        while not pedido and intentos < 3:
            time.sleep(0.5) # Espera 500ms
            pedido = Pedido.objects.filter(stripe_checkout_id=session_id).first()
            intentos += 1

    # Ahora tienes el objeto 'pedido' disponible en el template
    return render(request, "home/success.html", {"pedido": pedido})



def cancel_view(request):
    return render(request, "home/cancel.html")

@login_required
def seguimiento_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    # Verificar que el usuario es el dueño del pedido
    if pedido.cliente_email != request.user.email:
        return HttpResponse("No autorizado para ver este pedido.", status=403)
    progreso = 0
    if pedido.estado_envio == 'On the way':
        progreso = 50
    elif pedido.estado_envio == 'Delivered':
        progreso = 100
    return render(request, "home/estado_envio.html", {"pedido": pedido,
                                                            "progreso": progreso})

def seguimiento_pedido_token(request, token):
    pedido = Pedido.objects.get(seguimiento_token=token)
    progreso = 0
    if pedido.estado_envio == 'On the way':
        progreso = 50
    elif pedido.estado_envio == 'Delivered':
        progreso = 100
    return render(request, "home/estado_envio.html", {"pedido": pedido,
                                                            "progreso": progreso})