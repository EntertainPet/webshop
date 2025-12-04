from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from home.forms import ClienteUpdateForm
from home.models import Cliente,Categoria, Marca, Pedido, Producto, ImagenProducto, Pedido
from .forms import CategoriaForm, ProductForm, ImagenFormSet
import json



class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class DashboardView(SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard.html'


class ProductListView(SuperuserRequiredMixin, ListView):
    model = Producto
    template_name = 'product_list.html'
    context_object_name = 'productos'
    paginate_by = 20


class ProductCreateView(SuperuserRequiredMixin, CreateView):
    model = Producto
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('adminpanel:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["image_formset"] = ImagenFormSet(
                self.request.POST, 
                self.request.FILES, 
                queryset=ImagenProducto.objects.none(),
                prefix="images"
            )
        else:
            ctx["image_formset"] = ImagenFormSet(
                queryset=ImagenProducto.objects.none(),
                prefix="images"
            )
        return ctx

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["image_formset"]

        if not formset.is_valid():
            return self.form_invalid(form)

        producto = form.save()

        for cleaned in formset.cleaned_data:
            if not cleaned:
                continue
            if cleaned.get("DELETE"):
                continue

            file = cleaned.get("imagen_file")
            es_principal = cleaned.get("es_principal", False)

            if file:
                path = default_storage.save(f"productos/{file.name}", file)
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=default_storage.url(path),
                    es_principal=es_principal
                )

        messages.success(self.request, "Producto creado correctamente.")
        return super().form_valid(form)




class ProductUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('adminpanel:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        producto = self.get_object()

        if self.request.POST:
            ctx["image_formset"] = ImagenFormSet(
                self.request.POST,
                self.request.FILES,
                queryset=ImagenProducto.objects.filter(producto=producto),
                prefix="images"
            )
        else:
            ctx["image_formset"] = ImagenFormSet(
                queryset=ImagenProducto.objects.filter(producto=producto),
                prefix="images"
            )
        return ctx

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["image_formset"]

        if not formset.is_valid():
            return self.form_invalid(form)

        producto = form.save()

        for f in formset:
            data = f.cleaned_data
            instance = f.instance

            if not data:
                continue

            # Eliminar
            if data.get("DELETE") and instance.pk:
                instance.delete()
                continue

            file = data.get("imagen_file")
            es_principal = data.get("es_principal", False)

            if instance.pk:
                instance.es_principal = es_principal
                if file:
                    path = default_storage.save(f"productos/{file.name}", file)
                    instance.imagen = default_storage.url(path)
                instance.save()
            else:
                if file:
                    path = default_storage.save(f"productos/{file.name}", file)
                    ImagenProducto.objects.create(
                        producto=producto,
                        imagen=default_storage.url(path),
                        es_principal=es_principal
                    )

        messages.success(self.request, "Producto actualizado correctamente.")
        return super().form_valid(form)




class ProductDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Producto
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('adminpanel:product_list')


class CategoriaListView(SuperuserRequiredMixin, ListView):
    model = Categoria
    template_name = "categorias/list.html"
    context_object_name = "categorias"


class CategoriaCreateView(SuperuserRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categorias/form.html"
    
    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("adminpanel:categoria_list")

    def form_valid(self, form):
        messages.success(self.request, "Categoría creada correctamente.")
        return super().form_valid(form)


class CategoriaUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categorias/form.html"
    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("adminpanel:categoria_list")

    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada.")
        return super().form_valid(form)


class CategoriaDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Categoria
    template_name = "categorias/categoria_confirm_delete.html"
    success_url = reverse_lazy("adminpanel:categoria_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Categoría eliminada.")
        return super().delete(request, *args, **kwargs)
    
class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "imagen"]

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse("adminpanel:categoria_list")

def marca_list(request):
    marcas = Marca.objects.all()
    return render(request, "marcas/list.html", {"marcas": marcas})

def marca_create(request):
    next_url = request.GET.get("next")

    form = MarcaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()

        if next_url:
            return redirect(next_url)

        return redirect("adminpanel:marca_list")

    return render(request, "marcas/form.html", {
        "form": form,
        "next": next_url
    })

def marca_update(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    form = MarcaForm(request.POST or None, instance=marca)
    if form.is_valid():
        form.save()
        return redirect("adminpanel:marca_list")
    return render(request, "marcas/form.html", {"form": form})

def marca_delete(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    marca.delete()
    return render(request, 'marcas/marca_confirm_delete.html')

class MarcaDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Marca
    template_name = 'marcas/marca_confirm_delete.html'
    success_url = reverse_lazy('adminpanel:marca_list')

class PedidoEnvioForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["estado_envio", "codigo_seguimiento"]

class PedidoListView(SuperuserRequiredMixin, ListView):
    model = Pedido
    template_name = "pedidos/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 20
    ordering = ["-fecha_creacion"]

class PedidoDetailView(SuperuserRequiredMixin, TemplateView):
    template_name = "pedidos/pedido_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pedido = get_object_or_404(Pedido, pk=self.kwargs["pk"])
        items = pedido.pedido_items.select_related("producto")

        context["pedido"] = pedido
        context["items"] = items
        return context
    
class PedidoUpdateEnvioView(SuperuserRequiredMixin, UpdateView):
    model = Pedido
    form_class = PedidoEnvioForm
    template_name = "pedidos/pedido_envio_form.html"

    def get_success_url(self):
        return reverse("adminpanel:pedido_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Estado del envío actualizado correctamente.")
        return super().form_valid(form)


def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, "clientes/list.html", {"clientes": clientes})

def cliente_detail(request, pk):
    """
    Vista unificada para ver y editar un cliente.
    Muestra un formulario con los datos del cliente y procesa su actualización.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteUpdateForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Los datos de '{cliente.username}' se han actualizado correctamente.")
            return redirect('adminpanel:cliente_detail', pk=cliente.pk)
    else:
        form = ClienteUpdateForm(instance=cliente)

    return render(request, "clientes/detail.html", {
        "cliente": cliente,
        "form": form
    })

def cliente_forzar_reset_password(request, pk):
    '''
    La idea es forzar al cliente a resetear su password en el próximo login.
    '''
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.cambio_contraseña_requerido = True
    cliente.save()
    messages.success(request, f"Se ha forzado a '{cliente.username}' a resetear su contraseña en el próximo inicio de sesión.")
    return redirect("adminpanel:cliente_list")

def consultar_compras_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    compras = Pedido.objects.filter(cliente_email=cliente.email).order_by('-fecha_creacion')
    return render(request, "clientes/compras.html", {
        "cliente": cliente,
        "compras": compras
    })

def cliente_update(request, pk):
    from home.forms import ClienteRegistrationForm
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteRegistrationForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        return redirect("adminpanel:cliente_list")
    return render(request, "clientes/form.html", {"form": form})

# ============================================
# GESTIÓN DEL CATÁLOGO Y NAVEGACIÓN
# ============================================

@method_decorator(csrf_protect, name="dispatch")
class CatalogoGestionView(TemplateView):
    template_name = "catalogo/gestion.html"  # ajusta si tu ruta es distinta

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Productos destacados (orden general del catálogo)
        destacados = (
            Producto.objects.filter(es_destacado=True)
            .order_by("orden_catalogo", "nombre")
        )

        # Categorías con sus productos (para la pestaña "Por Categoría")
        categorias_con_productos = []
        categorias = Categoria.objects.all().order_by("nombre")

        for cat in categorias:
            productos_cat = (
                Producto.objects.filter(categoria=cat)
                .order_by("orden_categoria", "nombre")
            )
            categorias_con_productos.append(
                {
                    "categoria": cat,
                    "productos": productos_cat,
                }
            )

        marcas = Marca.objects.prefetch_related('productos').all()
        context['marcas_con_productos'] = [
            {
                'marca': marca,
                'productos': marca.productos.order_by('orden_catalogo')
            }
            for marca in marcas
        ]

        context["destacados"] = destacados
        context["categorias_con_productos"] = categorias_con_productos

        return context

@require_POST
@csrf_protect
def actualizar_orden_catalogo(request):
    """
    Actualiza el campo orden_catalogo según el orden recibido.
    Se usa para:
      - lista general de destacados
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    orden_ids = data.get("orden", [])

    if not isinstance(orden_ids, list):
        return JsonResponse({"success": False, "error": "Formato de datos incorrecto"}, status=400)

    # Asignamos índice a cada producto
    for index, producto_id in enumerate(orden_ids):
        try:
            producto_id = int(producto_id)
        except (TypeError, ValueError):
            continue

        Producto.objects.filter(pk=producto_id).update(orden_catalogo=index)

    return JsonResponse({"success": True})

@require_POST
@csrf_protect
def actualizar_orden_categoria(request, categoria_id):
    """
    Actualiza el orden dentro de una categoría (campo orden_categoria).
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    orden_ids = data.get("orden", [])

    if not isinstance(orden_ids, list):
        return JsonResponse({"success": False, "error": "Formato de datos incorrecto"}, status=400)

    for index, producto_id in enumerate(orden_ids):
        try:
            producto_id = int(producto_id)
        except (TypeError, ValueError):
            continue

        Producto.objects.filter(pk=producto_id, categoria_id=categoria_id).update(
            orden_categoria=index
        )

    return JsonResponse({"success": True})

@require_POST
@csrf_protect
def cambiar_seccion_producto(request, producto_id):
    """
    Cambia la seccion_destacada de un producto.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        seccion = data.get("seccion", "") or ""
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    try:
        producto = Producto.objects.get(pk=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({"success": False, "error": "Producto no encontrado"}, status=404)

    producto.seccion_destacada = seccion
    producto.save(update_fields=["seccion_destacada"])

    return JsonResponse({"success": True})

@require_POST
@csrf_protect
def toggle_destacado_producto(request, producto_id):
    """
    Activa/desactiva el flag es_destacado de un producto.
    """
    try:
        producto = Producto.objects.get(pk=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({"success": False, "error": "Producto no encontrado"}, status=404)

    producto.es_destacado = not producto.es_destacado
    producto.save(update_fields=["es_destacado"])

    return JsonResponse({"success": True, "es_destacado": producto.es_destacado})

@require_POST
@csrf_protect
def actualizar_orden_marca(request, marca_id):
    """Actualiza el orden de productos dentro de una marca"""
    try:
        data = json.loads(request.body)
        orden = data.get('orden', [])
        
        for index, producto_id in enumerate(orden):
            Producto.objects.filter(id=producto_id, marca_id=marca_id).update(orden_catalogo=index)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)