from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "home"

urlpatterns = [
    # Catálogo
    path("", views.ProductListView.as_view(), name="catalogo"),
    path("catalogo/<slug:slug>/", views.ProductDetailView.as_view(), name="producto_detalle"),
    
    # Carrito
    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("carrito/add/<int:pk>/", views.add_to_cart, name="carrito_add"),
    path("carrito/update/<int:item_id>/", views.update_cart_item, name="carrito_update"),
    path("carrito/remove/<int:item_id>/", views.remove_from_cart, name="carrito_remove"),
    
    # Autenticación
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),
    path("guest/", views.invitado_view, name="guest"),
    
    # Checkout
    path("checkout/guest/", views.guest_checkout_view, name="guest_checkout"),
    path("checkout/process/", views.process_payment_view, name="process_payment"),
    
    # Stripe
    path("create_checkout_session/", views.create_checkout_session, name="create_checkout_session"),
    path("webhook/", views.my_webhook_view, name="webhook"),
    path("success/", views.success_view, name="success"),
    path("cancel/", views.cancel_view, name="cancel"),
]
