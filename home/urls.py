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
    # Carrito de sesión (usuarios no autenticados)
    path("carrito/session/update/", views.carrito_update_session_item, name="carrito_update_session_item"),
    path("carrito/session/remove/", views.carrito_remove_session_item, name="carrito_remove_session_item"),
    
    # Autenticación
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),
    path("guest/", views.invitado_view, name="guest"),
    
    # Stripe
    path("autocomplete/", views.autocomplete_productos, name="autocomplete"),
    path('pedido/seguimiento/<int:pedido_id>/', views.seguimiento_pedido, name='seguimiento'),
    path('pedido/seguimiento/token/<uuid:token>/', views.seguimiento_pedido_token, name='seguimiento_token'),
    
    #stripe
    path("create_checkout_session/", views.create_checkout_session, name="create_checkout_session"),
    path("guestBuy/", views.invitado_compra_view, name="guestBuy"),
    path("webhook/", views.my_webhook_view, name="webhook"),
    path("success/", views.success_view, name="success"),
    path("cancel/", views.cancel_view, name="cancel"),
    path("historial/", views.OrderHistoryListView.as_view(), name="historial"),
    path("historial/<int:pk>/", views.PedidoDetailView.as_view(), name="historial_detalle"),
]
