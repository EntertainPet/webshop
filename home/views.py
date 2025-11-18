from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView
import uuid

from .forms import ClienteRegistrationForm
from .models import Categoria, Producto, Carrito, ItemCarrito

from django.conf import settings
import stripe

from rest_framework.response import Response

from rest_framework.decorators import api_view
from django.db.models import Q

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

    def get_queryset(self):
        qs = super().get_queryset().filter(esta_disponible=True)

        # --- Obtener parámetros GET ---
        q = self.request.GET.get("q", "")
        categoria = self.request.GET.get("categoria", "")
        marca = self.request.GET.get("marca", "")
        precio_min = self.request.GET.get("min", "")
        precio_max = self.request.GET.get("max", "")

        # --- Búsqueda ---
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q)
            )

        # --- Filtros ---
        if categoria:
            qs = qs.filter(categoria__id=categoria)

        if marca:
            qs = qs.filter(marca=marca)

        if precio_min:
            qs = qs.filter(precio__gte = precio_min)

        if precio_max:
            precio = qs.model._meta.get_field("precio")
            qs = qs.filter(precio__lte =precio_max)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Categoria.objects.all()
        ctx["marcas"] = Producto.objects.values_list("marca__id", "marca__nombre").distinct()
        ctx["search"] = self.request.GET.get("q", "")
        return ctx

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