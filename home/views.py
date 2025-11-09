from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView

from .forms import ClienteRegistrationForm, ClienteLoginForm
from .models import Categoria, Producto, Carrito, ItemCarrito
from django.shortcuts import render

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
class CartView(LoginRequiredMixin, TemplateView):
    template_name = "home/carrito.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        carrito, _ = Carrito.objects.get_or_create(cliente=self.request.user)
        ctx["carrito"] = carrito
        ctx["total"] = carrito.total
        return ctx

def add_to_cart(request, pk):
    if not request.user.is_authenticated:
        return redirect("home:identificacion")
    producto = get_object_or_404(Producto, pk=pk)
    carrito, _ = Carrito.objects.get_or_create(cliente=request.user)
    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito, producto=producto, talla=""
    )
    if not created:
        item.cantidad += 1
    item.save()
    return redirect("home:carrito")

def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        return redirect("home:identificacion")
    ItemCarrito.objects.filter(id=item_id, carrito__cliente=request.user).delete()
    return redirect("home:carrito")


# Checkout (placeholders)
class CheckoutEntregaView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_entrega.html"

class CheckoutPagoView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_pago.html"

class CheckoutConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "home/checkout_confirmacion.html"