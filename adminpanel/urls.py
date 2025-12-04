from django.urls import path
from . import views
from .utils import superuser_required
app_name = 'adminpanel'

urlpatterns = [
    path('', superuser_required(views.DashboardView.as_view()), name='dashboard'),
    path('productos/', superuser_required(views.ProductListView.as_view()), name='product_list'),
    path('productos/add/', superuser_required(views.ProductCreateView.as_view()), name='product_add'),
    path('productos/<int:pk>/edit/', superuser_required(views.ProductUpdateView.as_view()), name='product_edit'),
    path('productos/<int:pk>/delete/', superuser_required(views.ProductDeleteView.as_view()), name='product_delete'),
    path("categorias/", superuser_required(views.CategoriaListView.as_view()), name="categoria_list"),
    path("categorias/add/", superuser_required(views.CategoriaCreateView.as_view()), name="categoria_add"),
    path("categorias/<int:pk>/edit/", superuser_required(views.CategoriaUpdateView.as_view()), name="categoria_edit"),
    path("categorias/<int:pk>/delete/", superuser_required(views.CategoriaDeleteView.as_view()), name="categoria_delete"),
    path("marcas/", superuser_required(views.marca_list), name="marca_list"),
    path("marcas/nueva/", superuser_required(views.marca_create), name="marca_create"),
    path("marcas/<int:pk>/editar/", superuser_required(views.marca_update), name="marca_update"),
    path("marcas/<int:pk>/eliminar/", superuser_required(views.MarcaDeleteView.as_view()), name="marca_delete"),
    path("pedidos/", superuser_required(views.PedidoListView.as_view()), name="pedido_list"),
    path("pedidos/<int:pk>/", superuser_required(views.PedidoDetailView.as_view()), name="pedido_detail"),
    path("pedidos/<int:pk>/envio/", superuser_required(views.PedidoUpdateEnvioView.as_view()), name="pedido_update_envio"),
    #CLIENTES
    path("clientes/", superuser_required(views.cliente_list), name="cliente_list"),
    path("clientes/<int:pk>/", superuser_required(views.cliente_detail), name="cliente_detail"),
    path("clientes/<int:pk>/forzar-reset-password/", superuser_required(views.cliente_forzar_reset_password), name="cliente_forzar_reset_password"),
    path("clientes/<int:pk>/compras/", superuser_required(views.consultar_compras_cliente), name="consultar_compras_cliente"),
    ]
