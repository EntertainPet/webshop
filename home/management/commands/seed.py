from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import uuid

from home.models import (
    Categoria, Marca, Producto, ImagenProducto,
    TallaProducto, Carrito, ItemCarrito,
    Pedido, ItemPedido
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with realistic pet-store sample data"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Iniciando seeder de EntertainPet...")

        # --------------------------
        # 0. Limpiar datos anteriores
        # --------------------------
        ItemPedido.objects.all().delete()
        Pedido.objects.all().delete()
        ItemCarrito.objects.all().delete()
        Carrito.objects.all().delete()
        TallaProducto.objects.all().delete()
        ImagenProducto.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Marca.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write("✔ Datos anteriores eliminados")

        # --------------------------
        # 1. Crear usuarios
        # --------------------------
        user1 = User.objects.create_user(
            username="cliente1",
            password="cliente1",
            email="cliente1@mail.com",
            telefono="600123456",
            direccion="Calle Mascotas 10",
            ciudad="Barcelona",
            codigo_postal="08001"
        )
        user2 = User.objects.create_user(
            username="cliente2",
            password="cliente2",
            email="cliente2@mail.com",
            telefono="600654321",
            direccion="Avenida Peludos 20",
            ciudad="Valencia",
            codigo_postal="46001"
        )

        self.stdout.write("✔ Usuarios creados")

        # --------------------------
        # 2. Categorías
        # --------------------------
        categorias_data = [
            ("Perros", "Productos para perros"),
            ("Gatos", "Productos para gatos"),
            ("Pájaros", "Artículos para aves"),
            ("Peces", "Acuarios, alimento y accesorios"),
            ("Roedores", "Todo para hámsters, conejos y más"),
            ("Reptiles", "Terrarios, sustratos, alimento"),
            ("Ropa", "Ropa y accesorios para mascotas"),
        ]
        categorias = {nombre: Categoria.objects.create(nombre=nombre, descripcion=desc) for nombre, desc in categorias_data}
        self.stdout.write("✔ Categorías creadas")

        # --------------------------
        # 3. Marcas
        # --------------------------
        marcas_nombres = [
            "Purina", "Royal Canin", "Pedigree", "Whiskas",
            "Kong", "Tetra", "Ferplast", "Hill's",
            "Beaphar", "Savic", "Vitakraft", "Eheim"
        ]
        marcas = {nombre: Marca.objects.create(nombre=nombre) for nombre in marcas_nombres}
        self.stdout.write("✔ Marcas creadas")

        # --------------------------
        # 4. Productos 
        # --------------------------
        productos_data = [
            ("Nike Pro Max", "Zapatillas deportivas diseñadas para perros activos, resistentes al agua y con suela antideslizante que protege las patas durante cualquier terreno.", "Ropa", "Kong", Decimal("34.99"), "https://s.alicdn.com/@sc04/kf/Hcb31b84cf15f41a1b92db766fe68106aY/Customized-Pet-Dog-Shoes-High-End-Materials-Waterproof-AJ-Shoes-4PCS-Set-Dog-Nikedog-Shoes.png_300x300.jpg", ["XS", "S", "M", "L"], True),
            ("Purina ONE Mini Adulto 1.5 kg", "Alimento completo y equilibrado para perros adultos de razas pequeñas, formulado con ingredientes de alta calidad para mantener huesos y dientes sanos.", "Perros", "Purina", Decimal("8.09"), "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dwc7c35208/images/nuevo_pienso_perros_purina_one_adult_mini_buey_arroz_ONE12211962_M_ind.jpg?sw=500&sh=500&sm=fit", [], False),
            ("Whiskas Adult 1+ Pescado 4 kg", "Alimento seco para gatos adultos, con sabor a pescado, que contribuye a una digestión sana y al mantenimiento de un pelaje brillante y saludable.", "Gatos", "Whiskas", Decimal("69.30"), "https://m.media-amazon.com/images/I/71ThhXSJ1PL._AC_UF1000,1000_QL80_.jpg", [], True),
            ("Ferplast Casita Roedor Natura", "Casita de madera natural para hámsters y otros roedores, ideal para dormir, esconderse y explorar, aportando un espacio seguro y acogedor.", "Roedores", "Ferplast", Decimal("14.99"), "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dwcc6a95ed/images/caseta_roedores_ferplast_sin_4645_FER84645099_4.jpg.jpg?sw=500&sh=500&sm=fit", [], False),
            ("Camiseta Básica", "Camiseta cómoda de algodón para perros, ligera y transpirable, perfecta para mantenerlos abrigados sin limitar sus movimientos.", "Ropa", "Kong", Decimal("6.99"), "https://ae-pic-a1.aliexpress-media.com/kf/Se38ee0b713e04364a10a941d19c7d9e2x.jpg_720x720q75.jpg_.avif", ["XS", "S", "M", "L"], True),
            ("Royal Canin Mini Adult 3 kg", "Pienso formulado para perros adultos de razas pequeñas, contribuye a la salud digestiva y mantiene la vitalidad gracias a su mezcla de nutrientes.", "Perros", "Royal Canin", Decimal("37.39"), "https://piensoseloina.com/wp-content/uploads/2023/11/mini-ad-pack.png", [], False),
            ("Purina ONE Indoor Mature 1.5 kg", "Alimento completo para gatos mayores de interior, ayuda a reducir las bolas de pelo y a mantener un peso saludable gracias a su fórmula adaptada.", "Gatos", "Purina", Decimal("9.99"), "https://yumbiltong.com/cdn/shop/products/8143.jpg?v=1708312360&width=1920", [], False),
            ("Tetra Roedor Sleep'n Play", "Rueda ultra silenciosa y segura para roedores nocturnos, diseñada para mantenerlos activos sin molestar a los dueños.", "Roedores", "Tetra", Decimal("17.49"), "https://m.media-amazon.com/images/I/61rAmOph3KL._AC_UF1000,1000_QL80_.jpg", [], True),
            ("Suéter Navideño", "Suéter cálido y decorativo para mascotas, ideal para las fiestas y mantener a tu mascota abrigada con estilo.", "Ropa", "Kong", Decimal("14.99"), "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw9d92b8ef/images/large/ce6b2870f8934a69b0ae5d3d8626e8b2.jpg?sw=780&sh=780&sm=fit&q=85", ["XS", "S", "M", "L"], True),
            ("Pedigree Dentastix perro grande 28 U", "Palitos masticables para higiene dental diaria, ayudan a reducir la placa y el sarro, mientras disfrutan de un sabor irresistible.", "Perros", "Pedigree", Decimal("12.99"), "https://www.albet.es/cdnassets/dentastix-pack-28-perros-grandes_l.png", [], False),
            ("Royal Canin Scratch & Play", "Rascador con poste de sisal para gatos, promueve el ejercicio, reduce el estrés y protege los muebles de los arañazos.", "Gatos", "Royal Canin", Decimal("45.50"), "https://m.media-amazon.com/images/I/611vVt+xQxL.jpg", [], False),
            ("Vitakraft Corredor Hamster Tunnel", "Túnel de plástico seguro y divertido para hámsters y ratones, fomenta el ejercicio y el entretenimiento diario.", "Roedores", "Vitakraft", Decimal("10.95"), "https://m.media-amazon.com/images/I/51fd8tRCfcL._AC_UF894,1000_QL80_.jpg", [], False),
            ("Sudadera Ligera", "Sudadera ligera para perros, transpirable y cómoda, ideal para paseos en climas templados.", "Ropa", "Beaphar", Decimal("19.99"), "https://m.media-amazon.com/images/I/61THZMLidoL._AC_UF350,350_QL80_.jpg", ["XS", "S", "M", "L"], False),
            ("Kong Classic Juguete (M)", "Juguete de caucho duradero que se puede rellenar con golosinas, ideal para mantener a los perros entretenidos y estimular su inteligencia.", "Perros", "Kong", Decimal("5.60"), "https://www.superpet.club/19724-large_default/kong-classic-red.jpg", [], True),
            ("Ferplast Igloo Cama Gato", "Cama tipo iglú para gatos, cerrada y acogedora, que proporciona un refugio cálido y seguro para descansar.", "Gatos", "Ferplast", Decimal("39.89"), "https://www.ferplast.es/cdn/shop/files/3-0190010033_1800x1800.jpg?v=1728903644", [], False),
            ("Vitakraft Snack Conejo Zanahoria 100g", "Snack saludable y natural para conejos y roedores, con sabor a zanahoria, ideal para premiar y complementar su dieta.", "Roedores", "Vitakraft", Decimal("1.90"), "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXHFOy2En3gUZQHahiFBvbRPJIrkd8rG3ypQ&s", [], False),
            ("Impermeable", "Prenda impermeable ligera para perros, perfecta para mantenerlos secos durante la lluvia y al aire libre.", "Ropa", "Beaphar", Decimal("12.99"), "https://m.media-amazon.com/images/I/61KNLVjoopL.jpg", ["XS", "S", "M", "L"], False),
            ("Hill's Science Plan Puppy Medium 12 kg", "Pienso de alta calidad para cachorros de tamaño mediano, que apoya un crecimiento saludable y desarrollo óptimo de sus defensas.", "Perros", "Hill's", Decimal("51.19"), "https://agromascotas.es/6189-large_default/hills-sp-canine-puppy-healthy-development-cordero-y-arroz.jpg", [], False),
            ("Kong Naturals Alimentador Lento Gato", "Comedero lento con diseño natural, que ayuda a los gatos a comer despacio, reduciendo problemas digestivos.", "Gatos", "Kong", Decimal("14.99"), "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw43f38aaa/images/comedero_perros_outech_eco_kenia_OUT40595.jpg?sw=780&sh=780&sm=fit&q=85", [], False),
            ("TetraMin Flakes 1L", "Alimento completo en escamas para peces de acuario, garantiza vitalidad y colorido óptimo de los peces.", "Peces", "Tetra", Decimal("15.99"), "https://m.media-amazon.com/images/I/71eqp+Qt-wL.jpg", [], False),
            ("Arnés Evolutive", "Arnés de seguridad ajustable para perros, proporciona control y comodidad durante los paseos, con diseño ergonómico y seguro.", "Ropa", "Kong", Decimal("29.99"), "https://www.aresbaby.com/wp-content/uploads/2022/08/evolutive-safety-harness-1.jpg", ["XS", "S", "M", "L"], True),
            ("Beaphar Calm & Relax Gotas 30 ml", "Suplemento líquido para perros ansiosos, que ayuda a reducir el estrés y mejora su bienestar durante situaciones difíciles.", "Perros", "Beaphar", Decimal("8.49"), "https://www.mvgarden.com/6394-superlarge_default/beaphar-calming-no-stress-perro-recambio-30ml.jpg", [], False),
            ("Beaphar Hairball Pasta 100 g", "Pasta especialmente formulada para ayudar a los gatos a eliminar las bolas de pelo y mantener un sistema digestivo saludable.", "Gatos", "Beaphar", Decimal("11.99"), "https://m.media-amazon.com/images/I/61gKfknVR0L.jpg", [], False),
            ("Ferplast Terrario Reptiles 45x45x60", "Terrario ventilado de cristal ideal para reptiles, con espacio suficiente para moverse y accesorios para simular su hábitat natural.", "Reptiles", "Ferplast", Decimal("109.99"), "https://confortanimal.es/wp-content/uploads/2025/09/Pro-Terrarium-Small-Tall-Exo-Terra-45%C3%9745%C3%9760-cm-%E2%80%93-Terrario-Alto-para-Repteis.jpg", [], False),
            ("Chaleco Reflectante", "Chaleco reflectante para paseos nocturnos, mejora la visibilidad de tu mascota y aporta seguridad en entornos urbanos.", "Ropa", "Beaphar", Decimal("18.99"), "https://m.media-amazon.com/images/I/61BaG8m-8OL._AC_UF1000,1000_QL80_.jpg", ["XS", "S", "M", "L"], False),
            ("Pedigree Markies Galletas para perros", "Snack en forma de galleta delicioso que cuida los dientes de los perros mientras disfrutan de un premio saludable.", "Perros", "Pedigree", Decimal("8.58"), "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw1770b9cd/images/pedigree_galletas_perros_PED104560_1.jpg?sw=500&sh=500&sm=fit", [], False),
            ("Royal Canin Baby Cat 2 kg", "Pienso para gatitos muy pequeños, proporciona todos los nutrientes esenciales para un desarrollo óptimo en las primeras etapas de vida.", "Gatos", "Royal Canin", Decimal("28.99"), "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw92e6cd5c/images/new_royal_canin_mother_babycat_gato_ROY310715_M_1.jpg?sw=780&sh=780&sm=fit&q=85", [], False),
            ("Vitakraft Jelly Perlas Gato", "Snack en gelatina para gatos, delicioso y divertido, con sabor a atún que encantará a tu felino.", "Gatos", "Vitakraft", Decimal("3.79"), "https://www.mascotasavila.com/cdn/shop/products/98114.png", [], False),
            ("Hill's Science Plan Mature Adult 7+ 5 kg", "Pienso específico para perros senior, que ayuda a mantener articulaciones sanas y vitalidad general en la edad avanzada.", "Perros", "Hill's", Decimal("59.85"), "https://www.piensosraposo.es/1837-large_default/hill-s-mature-adult-7-medium-science-plan-con-pollo.jpg", [], False),
            ("Tetra Reptomin Plus 250 ml", "Alimento granulado especialmente diseñado para reptiles, con vitaminas y minerales esenciales para un desarrollo saludable.", "Reptiles", "Tetra", Decimal("8.99"), "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPNgOJtohQILiP9VsIjXzoAsU-OAxK1DDbsA&s", [], False),
            ("Kong Flyer Disco Volador", "Disco volador de goma resistente, ideal para juegos al aire libre y para mantener activo a tu perro durante horas de diversión.", "Perros", "Kong", Decimal("9.99"), "https://media.zooplus.com/bilder/6/400/417796_pla_kong_flyer_hundefrisbee_hs_01_6.jpg?width=400&format=webp", [], False),
            ("Ferplast Fuente automática Fontanella 1.5L", "Fuente de agua automática con filtro que mantiene el agua limpia y fresca para perros y gatos, fomentando la hidratación constante.", "Perros", "Ferplast", Decimal("34.99"), "https://m.media-amazon.com/images/I/61jHplX8zyS._AC_UF894,1000_QL80_.jpg", [], False),
            ("Beaphar Shampoo Perros Aloe Vera 200 ml", "Champú suave con aloe vera, ideal para perros con piel sensible, mantiene el pelaje limpio, hidratado y brillante.", "Perros", "Beaphar", Decimal("10.99"), "https://riovet.es/wp-content/uploads/2022/05/Beaphar-Champu-Bio-Pieles-Sensibles-Perro.jpg", [], False),
            ("Ferplast Plato SlowBowl 500ml", "Comedero lento para perros, reduce la ingestión rápida de alimento y ayuda a la digestión, evitando problemas gastrointestinales.", "Perros", "Ferplast", Decimal("9.90"), "https://m.media-amazon.com/images/I/51fMtk5wKZL._AC_UF350,350_QL80_.jpg", [], False),
            ("Tetra AquaSafe Plus 250 ml", "Acondicionador de agua para acuarios nuevos, elimina cloro y metales pesados, preparando un ambiente saludable para los peces.", "Peces", "Tetra", Decimal("15.09"), "https://m.media-amazon.com/images/I/61dpFEj4G7L.jpg", [], False),
            ("Eheim Filtro canister 2213", "Filtro externo de alto rendimiento para acuarios, asegura una limpieza eficiente del agua y un entorno saludable para tus peces.", "Peces", "Eheim", Decimal("158.38"), "https://m.media-amazon.com/images/I/716-CXv4HvL.jpg", [], False),
            ("Tetra EasyBalance Test Kit", "Kit completo para medir pH, nitritos y nitratos en acuarios, permitiendo mantener un agua equilibrada y saludable para los peces.", "Peces", "Tetra", Decimal("23.01"), "https://m.media-amazon.com/images/I/616+XyhivhL.jpg", [], False),
            ("Tetra SafeStart 250 ml", "Inoculante biológico que ayuda a establecer colonias de bacterias beneficiosas en acuarios nuevos, asegurando un ecosistema estable y saludable.", "Peces", "Tetra", Decimal("16.89"), "https://m.media-amazon.com/images/I/81H2ThiOgJL.jpg", [], False),
            ("Jaula para transporte Savic Dog Residence con cojín", "Jaula portátil y cómoda para transportar perros de manera segura, con acolchado suave y ventilación adecuada.", "Perros", "Savic", Decimal("134.99"), "https://media.zooplus.com/bilder/1/400/76342_pla_3294_4007_dr_107ht_1.jpg?width=400&format=webp", [], False),
            ("Gorro", "Gorro suave y cálido para perros, protege la cabeza del frío y añade estilo durante los paseos.", "Ropa", "Beaphar", Decimal("12.99"), "https://www.sparkpaws.es/cdn/shop/files/20230917SP19926_600x.jpg?v=1758241855", ["XS", "S", "M", "L"], False)
        ]

        productos = []

        for nombre, desc, cat_nombre, marca_nombre, precio, img_url, tallas_data, es_destacado in productos_data:
            categoria = Categoria.objects.get(nombre=cat_nombre)
            marca = Marca.objects.get(nombre=marca_nombre)

            producto_stock_general = 0
            if cat_nombre != "Ropa":
                producto_stock_general = random.randint(5, 15)

            prod = Producto.objects.create(
                nombre=nombre,
                descripcion=desc,
                precio=precio,
                stock=producto_stock_general, 
                categoria=categoria,
                marca=marca,
                es_destacado=es_destacado
            )

            ImagenProducto.objects.create(
                producto=prod,
                imagen=img_url,
                es_principal=True
            )
            
            if cat_nombre == "Ropa" and tallas_data:
                total_stock_tallas = 0
                for talla in tallas_data:
                    stock_talla = random.randint(2, 8)
                    TallaProducto.objects.create(
                        producto=prod, 
                        talla=talla,
                        stock=stock_talla 
                    )
                    total_stock_tallas += stock_talla 
                prod.stock = total_stock_tallas
                prod.save()
            else:
                TallaProducto.objects.create(
                    producto=prod, 
                    talla="Única",
                    stock=producto_stock_general
                )
            
            productos.append(prod)

        self.stdout.write(f"✔ {len(productos)} productos creados")

        # --------------------------
        # 5. Crear carritos con items (ACTUALIZADO)
        # --------------------------
        # Carrito para user1
        carrito1 = Carrito.objects.create(cliente=user1)
        for _ in range(random.randint(2, 4)):
            producto_random = random.choice(productos)
            talla_random = producto_random.tallas.filter(stock__gt=0).first()
            if talla_random:
                ItemCarrito.objects.create(
                    carrito=carrito1,
                    producto=producto_random,
                    talla_producto=talla_random,
                    cantidad=random.randint(1, 2)
                )

        # Carrito para user2
        carrito2 = Carrito.objects.create(cliente=user2)
        for _ in range(random.randint(2, 4)):
            producto_random = random.choice(productos)
            talla_random = producto_random.tallas.filter(stock__gt=0).first()
            if talla_random:
                ItemCarrito.objects.create(
                    carrito=carrito2,
                    producto=producto_random,
                    talla_producto=talla_random,
                    cantidad=random.randint(1, 2)
                )

        self.stdout.write("✔ Carritos con items creados")

        # --------------------------
        # 6. Crear pedidos (ACTUALIZADO)
        # --------------------------
        pedidos_user1 = [
            [(productos[0], 2, "M"), (productos[1], 1, "Única")], 
            [(productos[2], 1, "Única"), (productos[3], 3, "Única")], 
        ]

        for i, items in enumerate(pedidos_user1, start=1):
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"seed_checkout_user1_{i}",
                cantidad=Decimal("0.00"),
                divisa="EUR",
                cliente_email=user1.email,
                status="Paid",
                codigo_seguimiento=f"TRACK-{uuid.uuid4().hex[:8].upper()}"
            )
            total = Decimal("0.00")
            for prod, qty, talla in items:
                ItemPedido.objects.create(
                    pedido=pedido, 
                    producto=prod, 
                    cantidad=qty,
                    talla=talla
                )
                total += prod.precio * qty
            pedido.cantidad = total
            pedido.save()

        pedidos_user2 = [
            [(productos[4], 1, "S"), (productos[5], 2, "Única")], 
            [(productos[6], 2, "Única")], 
            [(productos[7], 1, "Única"), (productos[8], 1, "L")], 
        ]

        for i, items in enumerate(pedidos_user2, start=1):
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"seed_checkout_user2_{i}",
                cantidad=Decimal("0.00"),
                divisa="EUR",
                cliente_email=user2.email,
                status="Paid",
                codigo_seguimiento=f"TRACK-{uuid.uuid4().hex[:8].upper()}"
            )
            total = Decimal("0.00")
            for prod, qty, talla in items:
                ItemPedido.objects.create(
                    pedido=pedido, 
                    producto=prod, 
                    cantidad=qty,
                    talla=talla
                )
                total += prod.precio * qty
            pedido.cantidad = total
            pedido.save()

        self.stdout.write(self.style.SUCCESS("✅ Datos generados correctamente"))