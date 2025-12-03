from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.forms import modelformset_factory
from django.core.files.storage import default_storage
from django.conf import settings
from home.models import Cliente

from home.models import Categoria, Marca, Producto, ImagenProducto, Pedido, ItemPedido
from .forms import CategoriaForm, ProductForm, ImagenProductoForm, ImagenFormSet


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


