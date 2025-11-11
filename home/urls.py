from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("catalogo/", views.ProductListView.as_view(), name="catalogo"),
    path("producto/<int:pk>/", views.ProductDetailView.as_view(), name="producto_detalle"),
    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("login/", views.IdentificacionView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
]
