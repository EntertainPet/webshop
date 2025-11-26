from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views

app_name = "home"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="catalogo"),
    path("catalogo/<slug:slug>/", views.ProductDetailView.as_view(), name="producto_detalle"),
    path("carrito/", views.CartView.as_view(), name="carrito"),
    path("carrito/add/<int:pk>/", views.add_to_cart, name="carrito_add"),
    path("carrito/remove/<int:item_id>/", views.remove_from_cart, name="carrito_remove"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),
    path("guest/", views.invitado_view, name="guest"),
    path("autocomplete/", views.autocomplete_productos, name="autocomplete"),

    path('pedido/seguimiento/<int:pedido_id>/', views.seguimiento_pedido, name='seguimiento'),

    #stripe
    path("create_checkout_session/", views.create_checkout_session, name="create_checkout_session"),
    path("webhook/", views.my_webhook_view, name="webhook"),
    path("success/", views.success_view, name="success"),
    path("cancel/", views.cancel_view, name="cancel"),
    path("historial/", views.OrderHistoryListView.as_view(), name="historial"),
    path("historial/<int:pk>/", views.PedidoDetailView.as_view(), name="historial_detalle"),
]
