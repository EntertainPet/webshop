from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q

import uuid
import secrets

from .forms import ClienteRegistrationForm
from .models import (
    Categoria, Marca, Producto, Carrito, ItemCarrito, 
    Pedido, ItemPedido, TallaProducto, Cliente
)

from django.conf import settings
import stripe
from rest_framework.response import Response
from rest_framework.decorators import api_view

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
        color = self.request.GET.getlist("color", [])
        material = self.request.GET.getlist("material", [])

        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        if categoria:
            qs = qs.filter(categoria__id__in=categoria)
        if marca:
            qs = qs.filter(marca__id__in=marca)
        if material:
            qs = qs.filter(material__in=material)
        if color:
            qs = qs.filter(color__in=color)
        if precio_min:
            qs = qs.filter(precio__gte=precio_min)
        if precio_max:
            qs = qs.filter(precio__lte=precio_max)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Categoria.objects.all()
        ctx["marcas"] = Marca.objects.all()
        ctx["color"] = Producto.objects.exclude(color="").values_list("color", flat=True).distinct()
        ctx["material"] = Producto.objects.exclude(material="").values_list("material", flat=True).distinct()
        ctx["search"] = self.request.GET.get("q", "")
        ctx["selected_categorias"] = self.request.GET.getlist("categoria")
        ctx["selected_marcas"] = self.request.GET.getlist("marca")
        ctx["selected_colores"] = self.request.GET.getlist("color")
        ctx["selected_materiales"] = self.request.GET.getlist("material")
        return ctx


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
    cantidad = int(request.POST.get("cantidad", 1))
    
    if not talla_producto_id:
        messages.error(request, "Debes seleccionar una talla.")
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
    
    talla_producto = get_object_or_404(TallaProducto, pk=talla_producto_id, producto=producto)
    
    # Validar stock disponible
    if cantidad > talla_producto.stock:
        messages.error(request, f"Solo quedan {talla_producto.stock} unidades disponibles de la talla {talla_producto.talla}.")
        return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
    
    # Usuario autenticado
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
                messages.error(request, f"Solo quedan {talla_producto.stock} unidades disponibles de la talla {talla_producto.talla}.")
                return redirect(request.META.get('HTTP_REFERER', 'home:catalogo'))
            item.cantidad = nueva_cantidad
            item.save()
        messages.success(request, f"{producto.nombre} añadido al carrito.")
    else:
        # Usuario anónimo: sesión
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        key = f"{producto.pk}-{talla_producto.pk}"
        current_qty = request.session['cart'].get(key, 0)
        nueva_cantidad = current_qty + cantidad
        
        if nueva_cantidad > talla_producto.stock:
            messages.error(request, f"Solo quedan {talla_producto.stock} unidades disponibles de la talla {talla_producto.talla}.")
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


class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        
        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
            ctx["carrito"] = carrito
            ctx["cart_items"] = carrito.carrito_items.all()
            ctx["total"] = carrito.total
            ctx["cantidad_items"] = carrito.cantidad_total_items
        else:
            items = get_cart_items_from_session(request)
            ctx["cart_items"] = items
            ctx["total"] = sum(item["subtotal"] for item in items)
            ctx["cantidad_items"] = sum(item["cantidad"] for item in items)
        
        return ctx


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
        if not email:
            messages.error(request, "Debes ingresar un email válido.")
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
            success_url=request.build_absolute_uri("/success/"),
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

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded']:
        session = event['data']['object']
        cart_code = session.get("metadata", {}).get("cart_code")
        fulfill_checkout(session, cart_code)

    return HttpResponse(status=200)


def fulfill_checkout(session, cart_code):
    """Crea el pedido tras pago exitoso."""
    codigo_seguimiento = secrets.token_urlsafe(8).upper()
    
    order = Pedido.objects.create(
        stripe_checkout_id=session["id"],
        cantidad=session["amount_total"] / 100,
        divisa=session["currency"],
        cliente_email=session["customer_email"],
        status="Paid",
        codigo_seguimiento=codigo_seguimiento
    )

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
    
    carrito.delete()


def success_view(request):
    return render(request, "home/success.html")


def cancel_view(request):
    return render(request, "home/cancel.html")