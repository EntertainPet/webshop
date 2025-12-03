from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('productos/', views.ProductListView.as_view(), name='product_list'),
    path('productos/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('productos/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('productos/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path("categorias/", views.CategoriaListView.as_view(), name="categoria_list"),
    path("categorias/add/", views.CategoriaCreateView.as_view(), name="categoria_add"),
    path("categorias/<int:pk>/edit/", views.CategoriaUpdateView.as_view(), name="categoria_edit"),
    path("categorias/<int:pk>/delete/", views.CategoriaDeleteView.as_view(), name="categoria_delete"),
    path("marcas/", views.marca_list, name="marca_list"),
    path("marcas/nueva/", views.marca_create, name="marca_create"),
    path("marcas/<int:pk>/editar/", views.marca_update, name="marca_update"),
    path("marcas/<int:pk>/eliminar/", views.MarcaDeleteView.as_view(), name="marca_delete"),
    path("pedidos/", views.PedidoListView.as_view(), name="pedido_list"),
    path("pedidos/<int:pk>/", views.PedidoDetailView.as_view(), name="pedido_detail"),
    path("pedidos/<int:pk>/envio/", views.PedidoUpdateEnvioView.as_view(), name="pedido_update_envio"),

    ]
