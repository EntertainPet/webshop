from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.HomeView.as_view(), name="inicio"),
    path("acerca/", views.AboutView.as_view(), name="acerca"),
    path("contacto/", views.ContactView.as_view(), name="contacto"),

    path("categorias/", views.CategoryListView.as_view(), name="categorias"),
    path("productos/", views.ProductListView.as_view(), name="productos"),
    # alias histórico usado en plantillas y enlaces: /catalogo/
    path("catalogo/", views.ProductListView.as_view(), name="catalogo"),
    path("producto/<int:pk>/", views.ProductDetailView.as_view(), name="producto_detalle"),

    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("carrito/add/<int:pk>/", views.add_to_cart, name="carrito_add"),
    path("carrito/remove/<int:item_id>/", views.remove_from_cart, name="carrito_remove"),

    path("identificacion/", views.IdentificacionView.as_view(), name="identificacion"),
    # alias en inglés/español para compatibilidad con plantillas antiguas
    path("login/", views.IdentificacionView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="registro"),
    path("registro/", views.RegisterView.as_view(), name="registro_es"),
    path("logout/", views.CerrarSesionView.as_view(), name="logout"),

    path("checkout/entrega/", views.CheckoutEntregaView.as_view(), name="checkout_entrega"),
    path("checkout/pago/", views.CheckoutPagoView.as_view(), name="checkout_pago"),
    path("checkout/confirmacion/", views.CheckoutConfirmacionView.as_view(), name="checkout_confirmacion"),
]
