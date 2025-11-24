from django.core.management.base import BaseCommand
from decimal import Decimal
import uuid
import random

from django.core.management import call_command

from home.models import Pedido, ItemPedido, Producto, Cliente 
from home.views import enviar_correo


class Command(BaseCommand):
    help = "Crea un pedido falso con productos *específicos* del seeder de tienda de mascotas y envía un correo de prueba."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            dest="email",
            help="Correo al que enviar la confirmación (si no, usa el del cliente test)",
        )

        parser.add_argument(
            "--pedido-id",
            type=int,
            dest="pedido_id",
            help="Enviar correo usando un pedido existente",
        )

        parser.add_argument(
            "--create",
            action="store_true",
            help="Crear un pedido de prueba con productos del seeder",
        )

    def handle(self, *args, **options):
        pedido = None
        email_override = options.get("email")
        
        # Tarifa fija para simular el cargo de Stripe (500 cents = $5.00 USD)
        TASA_FIJA_CHECKOUT = Decimal("5.00") 

        # ----------------------------------------------------
        # 1) Usar un pedido existente
        # ----------------------------------------------------
        if options.get("pedido_id"):
            pid = options["pedido_id"]
            try:
                pedido = Pedido.objects.get(pk=pid)
            except Pedido.DoesNotExist:
                self.stderr.write(f"❌ No existe un Pedido con ID {pid}")
                return

        # ----------------------------------------------------
        # 2) Crear un pedido falso con productos del nuevo seeder
        # ----------------------------------------------------
        elif options.get("create"):
            self.stdout.write("⚙️ Ejecutando 'seed' para asegurar que los productos existen...")
            try:
                # 1. Asegurar que los productos del seeder estén creados
                call_command("seed") 
                self.stdout.write("✅ Comando 'seed' ejecutado.")
            except Exception as e:
                self.stderr.write(f"⚠️ El comando 'seed' falló (puede ser normal si ya existe): {e}")

            # 2. Obtener productos específicos (ej. 3 productos distintos)
            # Usaremos los productos de alto, medio y bajo precio para un buen resumen.
            try:
                prod_alto = Producto.objects.get(nombre="Eheim Filtro canister 2213") # $158.38
                prod_medio = Producto.objects.get(nombre="Ferplast Igloo Cama Gato")  # $39.89
                prod_bajo = Producto.objects.get(nombre="Vitakraft Snack Conejo Zanahoria 100g") # $1.90
                
                productos_a_incluir_con_qty = [
                    (prod_alto, 1),
                    (prod_medio, 2), # 2 unidades
                    (prod_bajo, 4)  # 4 unidades
                ]
                
            except Producto.DoesNotExist as e:
                self.stderr.write(f"❌ Producto del seeder no encontrado. Asegúrate de que los nombres son exactos: {e}")
                return


            # 3. Determinar el email y cliente (usamos el cliente1 del seeder)
            cliente = Cliente.objects.filter(username="cliente1").first()
            if email_override:
                email = email_override
            elif cliente:
                email = cliente.email
            else:
                email = "test@example.com"


            # 4. Crear el Pedido (Pedido principal)
            self.stdout.write(f"📝 Creando pedido de prueba para: {email}")
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"test_{uuid.uuid4().hex[:10]}",
                cantidad=Decimal("0"), # Se recalculará después
                divisa="USD", # Usamos USD, ya que es la moneda en create_checkout_session
                cliente_email=email,
                status="Paid",
            )

            total = TASA_FIJA_CHECKOUT # Inicializar con la tarifa fija de Stripe

            # 5. Añadir los ItemPedido
            for prod, qty in productos_a_incluir_con_qty:
                ItemPedido.objects.create(
                    pedido=pedido,
                    producto=prod,
                    cantidad=qty
                )

                # Siempre usamos el precio final (es precio normal o precio_oferta)
                precio_final = prod.precio_final 
                total += precio_final * qty

            # 6. Actualizar el total del Pedido
            pedido.cantidad = total.quantize(Decimal('0.01'))
            pedido.save()

            self.stdout.write(f"✅ Pedido de prueba #{pedido.pk} creado (Productos + Tarifa de {TASA_FIJA_CHECKOUT} USD). Total: ${pedido.cantidad}")


        else:
            self.stderr.write("❌ Debes usar **--create** o **--pedido-id <ID>**.")
            return

        # ----------------------------------------------------
        # 3) Enviar correo
        # ----------------------------------------------------
        self.stdout.write(f"📧 Enviando correo para pedido #{pedido.pk} a {pedido.cliente_email}...")

        try:
            enviar_correo(pedido) 
            self.stdout.write(self.style.SUCCESS("✅ Correo enviado correctamente."))
        except Exception as e:
            self.stderr.write(f"❌ Error al enviar correo: {e}")