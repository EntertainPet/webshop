from django.contrib.auth.decorators import user_passes_test

def superuser_required(view_func):
    """
    Decorador que comprueba que el usuario es un superusuario.
    """
    return user_passes_test(lambda u: u.is_superuser)(view_func)