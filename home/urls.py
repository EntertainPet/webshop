from django.urls import include, path
from . import views
from django.contrib.auth import urls as auth_urls

app_name = "home"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="catalogo"),
    path("catalogo/<slug:slug>/", views.ProductDetailView.as_view(), name="producto_detalle"),
    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("carrito/add/<int:pk>/", views.add_to_cart, name="carrito_add"),
    path("carrito/remove/<int:item_id>/", views.remove_from_cart, name="carrito_remove"),
    path("", include(auth_urls)),
    path("register/", views.register_view, name="register"),
]
