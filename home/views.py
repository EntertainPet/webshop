from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import ClienteRegistrationForm, ClienteLoginForm
from .models import Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido


from django.conf import settings
import stripe

from rest_framework.response import Response

from rest_framework.decorators import api_view

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.WEBHOOK_SECRET

# Páginas informativas
class HomeView(TemplateView):
    template_name = "home/inicio.html"

class AboutView(TemplateView):
    template_name = "home/acerca.html"

class ContactView(TemplateView):
    template_name = "home/contacto.html"


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
    
    cart.delete()


from django.shortcuts import render
def success_view(request):

    return render(request, "home/success.html")


def cancel_view(request):
    return render(request, "home/cancel.html")
# # Newly Added


# @api_view(["POST"])
# def create_user(request):
#     username = request.data.get("username")
#     email = request.data.get("email")
#     first_name = request.data.get("first_name")
#     last_name = request.data.get("last_name")
#     profile_picture_url = request.data.get("profile_picture_url")

#     new_user = User.objects.create(username=username, email=email,
#                                        first_name=first_name, last_name=last_name, profile_picture_url=profile_picture_url)
#     serializer = UserSerializer(new_user)
#     return Response(serializer.data)


# @api_view(["GET"])
# def existing_user(request, email):
#     try:
#         User.objects.get(email=email)
#         return Response({"exists": True}, status=status.HTTP_200_OK)
#     except User.DoesNotExist:
#         return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)


# @api_view(['GET'])
# def get_orders(request):
#     email = request.query_params.get("email")
#     orders = Order.objects.filter(customer_email=email)
#     serializer = OrderSerializer(orders, many=True)
#     return Response(serializer.data)


# @api_view(["POST"])
# def add_address(request):
#     email = request.data.get("email")
#     street = request.data.get("street")
#     city = request.data.get("city")
#     state = request.data.get("state")
#     phone = request.data.get("phone")

#     if not email:
#         return Response({"error": "Email is required"}, status=400)
    
#     customer = User.objects.get(email=email)

#     address, created = CustomerAddress.objects.get_or_create(
#         customer=customer)
#     address.email = email 
#     address.street = street 
#     address.city = city 
#     address.state = state
#     address.phone = phone 
#     address.save()

#     serializer = CustomerAddressSerializer(address)
#     return Response(serializer.data)


# @api_view(["GET"])
# def get_address(request):
#     email = request.query_params.get("email") 
#     address = CustomerAddress.objects.filter(customer__email=email)
#     if address.exists():
#         address = address.last()
#         serializer = CustomerAddressSerializer(address)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     return Response({"error": "Address not found"}, status=200)


# @api_view(["GET"])
# def my_wishlists(request):
#     email = request.query_params.get("email")
#     wishlists = Wishlist.objects.filter(user__email=email)
#     serializer = WishlistSerializer(wishlists, many=True)
#     return Response(serializer.data)


# @api_view(["GET"])
# def product_in_wishlist(request):
#     email = request.query_params.get("email")
#     product_id = request.query_params.get("product_id")

#     if Wishlist.objects.filter(product__id=product_id, user__email=email).exists():
#         return Response({"product_in_wishlist": True})
#     return Response({"product_in_wishlist": False})



# @api_view(['GET'])
# def get_cart(request, cart_code):
#     cart = Cart.objects.filter(cart_code=cart_code).first()
    
#     if cart:
#         serializer = CartSerializer(cart)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
#     return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)




# @api_view(['GET'])
# def get_cart_stat(request):
#     cart_code = request.query_params.get("cart_code")
#     cart = Cart.objects.filter(cart_code=cart_code).first()

#     if cart:
#         serializer = SimpleCartSerializer(cart)
#         return Response(serializer.data)
#     return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)


# @api_view(['GET'])
# def product_in_cart(request):
#     cart_code = request.query_params.get("cart_code")
#     product_id = request.query_params.get("product_id")
    
#     cart = Cart.objects.filter(cart_code=cart_code).first()
#     product = Product.objects.get(id=product_id)
    
#     product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

#     return Response({'product_in_cart': product_exists_in_cart})
