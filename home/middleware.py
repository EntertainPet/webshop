from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Continuar solo si el usuario está autenticado y no es un superusuario
        if request.user.is_authenticated and not request.user.is_superuser:
            # Comprobar el flag
            if request.user.cambio_contraseña_requerido:
                # Permitir el acceso solo a la página de cambio de contraseña y a la de logout
                allowed_paths = [
                    reverse('home:change_password_forced'), 
                    reverse('home:logout')
                ]
                if request.path not in allowed_paths:
                    return redirect('home:change_password_forced')

        response = self.get_response(request)
        return response