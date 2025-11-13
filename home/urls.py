from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.HomeView.as_view(), name="inicio"),
    path("acerca/", views.AboutView.as_view(), name="acerca"),
    path("contacto/", views.ContactView.as_view(), name="contacto"),

    path("categorias/", views.CategoryListView.as_view(), name="categorias"),
    path("productos/", views.ProductListView.as_view(), name="productos"),
    path("producto/<int:pk>/", views.ProductDetailView.as_view(), name="producto_detalle"),

    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("carrito/add/<int:pk>/", views.add_to_cart, name="carrito_add"),
    path("carrito/remove/<int:item_id>/", views.remove_from_cart, name="carrito_remove"),

    path("identificacion/", views.IdentificacionView.as_view(), name="identificacion"),
    path("registro/", views.RegisterView.as_view(), name="registro"),
    path("logout/", views.CerrarSesionView.as_view(), name="logout"),

    #stripe
    path("create_checkout_session/", views.create_checkout_session, name="create_checkout_session"),
    path("webhook/", views.my_webhook_view, name="webhook"),
    path("success/", views.success_view, name="success"),
    path("cancel/", views.cancel_view, name="cancel"),


]
