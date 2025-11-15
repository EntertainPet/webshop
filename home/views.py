from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView

from .forms import ClienteRegistrationForm, ClienteLoginForm
from .models import Categoria, Producto, Carrito, ItemCarrito

from django.conf import settings
import stripe

from rest_framework.response import Response

from rest_framework.decorators import api_view

stripe.api_key = settings.STRIPE_SECRET_KEY

# Páginas informativas
class HomeView(TemplateView):
    template_name = "home/inicio.html"

class AboutView(TemplateView):
    template_name = "home/acerca.html"

class ContactView(TemplateView):
    template_name = "home/contacto.html"

def login_view(request):
    return render(request, "login.html")


def register_view(request):
    return render(request, "register.html")

def cart_view(request):
    return render(request, "cart.html")

# Auth
class RegisterView(FormView):
    template_name = "home/registro.html"
    form_class = ClienteRegistrationForm
    success_url = reverse_lazy("home:inicio")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        # crea carrito vacío al registrarse
        Carrito.objects.get_or_create(cliente=user)
        return super().form_valid(form)

class IdentificacionView(LoginView):
    template_name = "home/identificacion.html"
    authentication_form = ClienteLoginForm

class CerrarSesionView(LogoutView):
    pass


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