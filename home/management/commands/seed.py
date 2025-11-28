from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import uuid

from home.models import (
    Categoria, Marca, Producto, ImagenProducto,
    TallaProducto, Carrito, ItemCarrito,
    Color, Pedido, ItemPedido
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
        ItemCarrito.objects.all().delete()
        ImagenProducto.objects.all().delete()
        Pedido.objects.all().delete()
        Carrito.objects.all().delete()
        TallaProducto.objects.all().delete()
        Color.objects.all().delete()
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
            first_name="María",
            last_name="García",
            direccion="Calle Mascotas 10",
            ciudad="Barcelona",
            codigo_postal="08001"
        )
        user2 = User.objects.create_user(
            username="cliente2",
            password="cliente2",
            email="cliente2@mail.com",
            telefono="600654321",
            first_name="Carlos",
            last_name="Martínez",
            direccion="Avenida Peludos 20",
            ciudad="Valencia",
            codigo_postal="46001"
        )

        self.stdout.write("✔ Usuarios creados")

        # --------------------------
        # 2. Categorías 
        # --------------------------
        categorias_data = [
            ("Ropa", "Ropa y accesorios para mascotas"),
            ("Alimentación", "Pienso, comida húmeda y snacks para mascotas"),
            ("Juguetes", "Accesorios para la diversión y el entrenamiento"),
            ("Otros", "Artículos de cuidado, hábitat y salud (camas, filtros, etc.)"),
        ]
        categorias = {nombre: Categoria.objects.create(nombre=nombre, descripcion=desc) for nombre, desc in categorias_data}
        self.stdout.write("✔ Categorías creadas")

        # --------------------------
        # 3. Marcas
        # --------------------------
        marcas_nombres = [
            "Purina", "Royal Canin", "Kong", "Tetra",
            "Ferplast", "Hill's", "Bugata Style"
        ]
        marcas = {nombre: Marca.objects.create(nombre=nombre) for nombre in marcas_nombres}
        self.stdout.write("✔ Marcas creadas")

        #--------------------------
        # 4. Colores
        # --------------------------
        colores_data = [
            ("Rojo", "#FF0000"), ("Azul", "#0000FF"),
            ("Verde", "#008000"), ("Negro", "#000000"),
            ("Blanco", "#FFFFFF"), ("Amarillo", "#FFFF00"),
            ("Gris", "#808080"), ("Naranja", "#FFA500"),
            ("Rosa", "#FFC0CB"),
        ]
        colores_map = {}
        for nombre, hex_code in colores_data:
            colores_map[nombre] = Color.objects.create(nombre=nombre, codigo_hex=hex_code)

        colores_list = list(colores_map.values())
        self.stdout.write("✔ Colores creados")

        # --------------------------
        # 5. Productos 
        # --------------------------
        productos_data = [
        ("Nike Pro Max", "Zapatillas protectoras para mascotas confeccionadas con materiales resistentes al agua y costuras reforzadas. Suela antideslizante que ofrece tracción en superficies húmedas y urbanas; diseño ergonómico que protege las almohadillas y evita rozaduras. Ideales para paseos largos y condiciones meteorológicas adversas, fáciles de limpiar y con cierre ajustable para un calce seguro. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("29.99"), 
        "https://s.alicdn.com/@sc04/kf/Hcb31b84cf15f41a1b92db766fe68106aY/Customized-Pet-Dog-Shoes-High-End-Materials-Waterproof-AJ-Shoes-4PCS-Set-Dog-Nikedog-Shoes.png_300x300.jpg\n", ["XS", "S", "M", "L"], ["Rojo", "Negro", "Blanco"],"Cuero sintético"),

        ("Purina ONE Mini Adulto 1.5 kg", "Pienso completo pensado para perros de razas pequeñas, formulado para aportar energía sostenida y mantener la salud dental. Contiene nutrientes esenciales para la piel y el pelaje, con fibras específicas que favorecen la digestión. Ideal como parte de una dieta equilibrada, recomendado para mantenimiento diario y control de peso en perros activos.", "Alimentación", "Purina", Decimal("7.99"), 
        "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dwc7c35208/images/nuevo_pienso_perros_purina_one_adult_mini_buey_arroz_ONE12211962_M_ind.jpg?sw=500&sh=500&sm=fit\n", [], [],None),

        ("Kong Classic Juguete (M)", "Juguete de caucho natural resistente, ideal para masticación intensa y entrenamiento. Rellenable para premios, ayuda a estimular la actividad mental y física; diseño flotante apto para juegos acuáticos y muy duradero frente a mordiscos repetidos.", "Juguetes", "Kong", Decimal("6.50"),
        "https://www.superpet.club/19724-large_default/kong-classic-red.jpg\n", [], [], "Plástico"),

        ("Ferplast Casita Roedor Natura", "Refugio de madera natural diseñado para roedores pequeños, con tratamiento seguro para animales y acabados lisos que evitan astillas. Proporciona aislamiento térmico y un espacio recogido para dormir, jugar y esconderse; fácil de limpiar y de integrar en jaulas modulares.", "Otros", "Ferplast", Decimal("12.99"), 
        "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dwcc6a95ed/images/caseta_roedores_ferplast_sin_4645_FER84645099_4.jpg.jpg?sw=500&sh=500&sm=fit\n", [], [], "Madera"),

        ("Camiseta Básica", "Camiseta ligera de algodón para mascotas, transpirable y suave al tacto. Costuras planas para mayor confort, diseño atemporal apto para uso diario y lavable a máquina. Perfecta para ir de paseo y para proteger ligeramente del sol en climas templados. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast", Decimal("5.99"), 
        "https://ae-pic-a1.aliexpress-media.com/kf/Se38ee0b713e04364a10a941d19c7d9e2x.jpg_720x720q75.jpg_.avif\n", ["XS", "S", "M", "L"], ["Negro", "Blanco", "Azul", "Gris"],"Algodón"), 

        ("Royal Canin Adult 1+ Pescado 4 kg", "Pienso completo para gatos adultos con sabor a pescado, formulado para favorecer la digestión, el brillo del pelaje y el mantenimiento del peso ideal. Incluye vitaminas y minerales esenciales que contribuyen al bienestar general; textura pensada para fomentar la masticación y la limpieza dental.", "Alimentación", "Royal Canin", Decimal("34.50"),
        "https://m.media-amazon.com/images/I/71ThhXSJ1PL._AC_UF1000,1000_QL80_.jpg\n", [], [],None), 

        ("TetraMin Flakes 1L", "Escamas nutritivas para peces de acuario que ayudan a mantener color y vitalidad; fórmula equilibrada con vitaminas esenciales. Fácil de dosificar y adecuada para una amplia variedad de especies tropicales de agua dulce.", "Otros", "Tetra", Decimal("7.99"),
        "https://m.media-amazon.com/images/I/71eqp+Qt-wL.jpg\n", [], [],None),

        ("Hill's Science Plan Puppy Medium 12 kg", "Pienso formulado para cachorros de tamaño mediano, con nutrientes específicos para apoyar el crecimiento de huesos y músculos, además de defensas naturales. Textura adaptada para fomentar la masticación y la aceptación durante las etapas de destete y crecimiento.", "Alimentación", "Hill's", Decimal("48.50"),
        "https://agromascotas.es/6189-large_default/hills-sp-canine-puppy-healthy-development-cordero-y-arroz.jpg\n", [], [],None),

        ("Suéter Navideño", "Suéter festivo y cálido para mascotas, confeccionado con fibra acrílica suave y estampado estacional. Proporciona abrigo en días fríos y es un complemento decorativo para celebraciones; cierres elásticos para facilitar el ajuste sin causar molestias. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("11.99"),
        "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw9d92b8ef/images/large/ce6b2870f8934a69b0ae5d3d8626e8b2.jpg?sw=780&sh=780&sm=fit&q=85\n", ["XS", "S", "M", "L"], ["Verde", "Rojo"],"Algodón"),

        ("Ferplast Corredor Hamster Tunnel", "Túnel modular de plástico seguro para hámsters y pequeños roedores, fomenta la exploración y el ejercicio. Diseño ventilado y fácil de limpiar; compatible con accesorios adicionales para crear circuitos y enriquecimiento ambiental.", "Juguetes", "Ferplast", Decimal("8.95"),
        "https://m.media-amazon.com/images/I/51fd8tRCfcL._AC_UF894,1000_QL80_.jpg\n", [], [], "Madera"), 

        ("Ferplast Igloo Cama Gato", "Cama tipo iglú que proporciona calor y privacidad, fabricada con materiales aislantes y base estable. Estructura fácil de desmontar para limpieza y cojín interior lavable; ideal para gatos que buscan un refugio acogedor y seguro.", "Otros", "Ferplast", Decimal("34.99"),
        "https://www.ferplast.es/cdn/shop/files/3-0190010033_1800x1800.jpg?v=1728903644\n", [], [], "Algodón"),

        ("Purina Dentastix perro grande 28 U", "Palitos de higiene dental para perros grandes que ayudan a reducir placa y sarro con uso diario. Textura y forma especialmente diseñadas para favorecer la limpieza mecánica de los dientes durante la masticación; complemento para una rutina de cuidado oral.", "Alimentación", "Purina", Decimal("10.99"),
        "https://www.albet.es/cdnassets/dentastix-pack-28-perros-grandes_l.png\n", [], [],None), 

        ("Sudadera Ligera", "Sudadera transpirable para mascotas, con tejido técnico que regula la temperatura corporal en climas suaves. Costuras reforzadas y detalle reflectante para mayor visibilidad; fácil de poner y apta para lavado frecuente sin perder forma. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Kong", Decimal("16.99"), 
        "https://m.media-amazon.com/images/I/61THZMLidoL._AC_UF350,350_QL80_.jpg\n", ["XS", "S", "M", "L"], ["Negro", "Azul", "Gris", "Blanco", "Rojo", "Verde"],"Algodón"),

        ("Tetra Filtro canister 2213", "Filtro externo de alto rendimiento para acuarios, diseñado para proporcionar filtración mecánica, biológica y química eficiente. Funcionamiento silencioso y bajo consumo, con fácil mantenimiento y cartuchos accesibles.", "Otros", "Tetra", Decimal("148.00"),
        "https://m.media-amazon.com/images/I/71TkqB7OMML.jpg", [], [],None), 

        ("Royal Canin Scratch & Play", "Rascador con poste de sisal natural pensado para cubrir las necesidades de rascado de los gatos, alargando el tiempo de juego y protegiendo muebles. Base estable y materiales duraderos, además de zonas para esconder juguetes y descansar.", "Juguetes", "Royal Canin", Decimal("39.99"),
        "https://m.media-amazon.com/images/I/611vVt+xQxL.jpg\n", [], [], "Sintético"),

        ("Royal Canin Mini Adult 3 kg", "Pienso específico para perros pequeños, formulado para apoyar la digestión, la salud oral y la vitalidad diaria. Contiene equilibradas combinaciones de proteínas y ácidos grasos esenciales para un pelaje brillante; pensado para perros con actividad moderada.", "Alimentación", "Royal Canin", Decimal("33.50"),
        "https://piensoseloina.com/wp-content/uploads/2023/11/mini-ad-pack.png\n", [], [],None),

        ("Impermeable", "Chaqueta impermeable para mascotas, ligera y con interior de malla para cómoda transpiración. Costuras selladas y cierre rápido que protege del viento y la lluvia; fácil de secar y de almacenar en plegado compacto. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast", Decimal("11.99"),
        "https://m.media-amazon.com/images/I/61KNLVjoopL.jpg\n", ["XS", "S", "M", "L"], ["Verde", "Negro"],"Sintético"), 

        ("Kong Naturals Alimentador Lento Gato", "Comedero diseñado para ralentizar la ingesta y fomentar el enriquecimiento alimentario; reduce atragantamientos y mejora la digestión felina. Superficie texturizada y cavidades distribuidas para que el gato explore y consuma más despacio.", "Otros", "Kong", Decimal("12.99"),
        "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw43f38aaa/images/comedero_perros_outech_eco_kenia_OUT40595.jpg?sw=780&sh=780&sm=fit&q=85\n", [], [], "Plástico"),
        
        ("Purina ONE Indoor Mature 1.5 kg", "Pienso diseñado para gatos de interior de edad avanzada, ayuda a reducir la formación de bolas de pelo y a mantener un peso saludable. Enriquecido con nutrientes que favorecen la salud digestiva y la vitalidad, con croquetas adaptadas a la dentición del gato adulto.", "Alimentación", "Purina", Decimal("9.49"),
        "https://yumbiltong.com/cdn/shop/products/8143.jpg?v=1708312360&width=1920\n", [], [],None),

        ("Ferplast Roedor Sleep`n Play", "Rueda silenciosa y segura para roedores, fabricada con plástico no tóxico y diseño cerrado que reduce el riesgo de lesiones. Promueve el ejercicio nocturno sin generar ruidos molestos; fácil montaje y compatible con la mayoría de jaulas estándar.", "Juguetes", "Ferplast", Decimal("14.99"),
        "https://m.media-amazon.com/images/I/61rAmOph3KL._AC_UF1000,1000_QL80_.jpg\n", [], [], "Plástico"),
 
        ("Arnés Evolutive", "Arnés ajustable con distribución de presión para paseos seguros; material resistente y cierres reforzados que evitan torsiones. Diseño ergonómico para comodidad del animal y del usuario, con puntos reflectantes para visibilidad nocturna. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast", Decimal("24.99"), 
        "https://www.aresbaby.com/wp-content/uploads/2022/08/evolutive-safety-harness-1.jpg\n", ["XS", "S", "M", "L"], ["Gris"],"Nylon"),

        ("Tetra EasyBalance Test Kit", "Kit básico de pruebas para pH, nitritos y nitratos que facilita el mantenimiento del acuario doméstico. Incluye reactivos y manual de uso, ideal para diagnóstico rápido y toma de decisiones en el cuidado del agua.", "Otros", "Tetra", Decimal("19.99"),
        "https://m.media-amazon.com/images/I/616+XyhivhL.jpg\n", [], [],None),

        ("Royal Canin Baby Cat 2 kg", "Pienso formulado para gatitos en etapas tempranas de desarrollo, favorece un correcto aporte de nutrientes para crecimiento y desarrollo inmunológico. Textura y tamaño de croqueta adaptados al régimen de lactancia y destete, con antioxidantes seleccionados.", "Alimentación", "Royal Canin", Decimal("25.99"),
        "https://www.tiendanimal.es/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw92e6cd5c/images/new_royal_canin_mother_babycat_gato_ROY310715_M_1.jpg?sw=780&sh=780&sm=fit&q=85\n", [], [],None),

        ("Chaleco Reflectante", "Chaleco con bandas reflectantes de alta visibilidad para paseos nocturnos; material ligero y cierre ajustable. Mejora la seguridad del animal en zonas urbanas con baja iluminación y es fácil de poner y quitar sin molestias. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("14.99"),
        "https://m.media-amazon.com/images/I/61BaG8m-8OL._AC_UF1000,1000_QL80_.jpg\n", ["XS", "S", "M", "L"], ["Naranja", "Amarillo", "Verde"],"Poliéster"),

        ("Ferplast Plato SlowBowl 500ml", "Comedero antivelocidad con diseño que obliga a masticar más despacio y mejora la digestión; base estable y material resistente a mordiscos. Ideal para perros que comen rápido y sufren regurgitaciones o problemas digestivos leves.", "Otros", "Ferplast", Decimal("8.90"),
        "https://m.media-amazon.com/images/I/51fMtk5wKZL._AC_UF350,350_QL80_.jpg\n", [], [], "Plástico"),

        ("Hill's Science Plan Mature Adult 7+ 5 kg", "Pienso específico para perros senior que cuida articulaciones y energía diaria; contiene nutrientes que favorecen movilidad y salud cognitiva. Fórmula equilibrada para ayudar a mantener la masa muscular y la condición corporal en la tercera edad.", "Alimentación", "Hill's", Decimal("54.99"),
        "https://www.piensosraposo.es/1837-large_default/hill-s-mature-adult-7-medium-science-plan-con-pollo.jpg\n", [], [],None),

        ("Gorro", "Gorro cálido para proteger la cabeza y las orejas de tu mascota en climas fríos; tejido suave y costuras internas que evitan rozaduras. Diseño cómodo con ajuste para no restringir la visión ni el movimiento. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("9.99"),
        "https://www.sparkpaws.es/cdn/shop/files/20230917SP19926_600x.jpg?v=1758241855\n", ["XS", "S", "M", "L"], ["Rojo"],"Lana"),

        ("Kong Flyer Disco Volador", "Disco de goma flexible y resistente para juegos al aire libre; diseño pensado para un vuelo estable y agarre cómodo. Material duradero y seguro para masticación, apto para entrenamiento de lanzamiento y recuperación en perros activos.", "Juguetes", "Kong", Decimal("8.99"),
        "https://media.zooplus.com/bilder/6/400/417796_pla_kong_flyer_hundefrisbee_hs_01_6.jpg?width=400&format=webp\n", [], [], "Plástico"),

        ("Tetra SafeStart 250 ml", "Inoculante biológico que acelera el ciclado del acuario y estabiliza la población bacteriana beneficiosa, reduciendo riesgos de pérdidas de peces. Útil en instalaciones nuevas o tras limpiezas profundas para recuperar equilibrio biológico.", "Otros", "Tetra", Decimal("14.49"),
        "https://m.media-amazon.com/images/I/81H2ThiOgJL.jpg\n", [], [],None),

        ("Ferplast Snack Conejo Zanahoria 100g", "Snack natural en formato comprimido para conejos y roedores como complemento ocasional; elaborado con ingredientes de origen vegetal que favorecen el desgaste dental y la actividad digestiva. Ideal para premios puntuales y entrenamiento.", "Alimentación", "Ferplast", Decimal("1.79"),
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXHFOy2En3gUZQHahiFBvbRPJIrkd8rG3ypQ&s\n", [], [],None), 

        ("Jersey de lana", "Jersey de punto cálido y suave para mantener a tu mascota abrigada durante el invierno; corte adaptado para libertad de movimiento y facilidad de puesta. Materiales tratados para disminuir la formación de bolas y facilitar el lavado. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast",
        Decimal("18.99"), "https://www.paraperrosygatos.es/cdn/shop/files/JERSEY_PERRO_ANTRACITA_TRIXIE.png?v=1731318156\n", ["XS", "S", "M", "L"], ["Gris", "Negro", "Rojo", "Blanco", "Azul"],"Lana"), 

        ("Ferplast Fuente automática Fontanella 1.5L", "Fuente con filtro para mantener el agua fresca y en circulación, fomentando la hidratación constante. Capacidad de 1.5L, sistema silencioso y piezas desmontables para limpieza y mantenimiento; indicado para gatos y perros de tamaño pequeño a mediano.", "Otros", "Ferplast", Decimal("29.99"),
        "https://m.media-amazon.com/images/I/61jHplX8zyS._AC_UF894,1000_QL80_.jpg\n", [], [],None),

        ("Purina Markies Galletas para perros", "Snack crujiente pensado para premios y refuerzo positivo durante el adiestramiento; textura endurecida que favorece la limpieza dental leve durante la masticación. Formulado para ser sabroso y aceptado por perros de distintas edades.", "Alimentación", "Purina", Decimal("6.49"),
        "https://www.kiwoko.com/dw/image/v2/BDLQ_PRD/on/demandware.static/-/Sites-kiwoko-master-catalog/default/dw1770b9cd/images/pedigree_galletas_perros_PED104560_1.jpg?sw=500&sh=500&sm=fit\n", [], [],None), 

        ("Esmoquin", "Traje elegante para ocasiones especiales, con corte cómodo y tejido que no oprime. Incluye detalles prácticos para sujetar correa y acabados pensados para sesiones de fotos y eventos sin renunciar al confort del animal. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("22.99"), 
        "https://m.media-amazon.com/images/I/51PW4hzwWlL.jpg\n", ["XS", "S", "M", "L"], ["Negro"],"Algodón"),

        ("Corbata", "Accesorio decorativo fácil de poner para eventos y sesiones fotográficas; cierre seguro y diseño cómodo que no limita el movimiento. Ideal como complemento temporal para looks formales o festivos. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast", Decimal("6.99"), 
        "https://m.media-amazon.com/images/I/71gWM8c2ybL.jpg\n", ["XS", "S", "M", "L"], ["Negro"],"Poliéster"),

        ("Ferplast Jelly Perlas Gato", "Premio en gelatina con sabor a atún, diseñado como snack ocasional para gatos; textura blanda adecuada para denticiones sensibles. Presentado en porciones individuales para control de la ingesta y como complemento apetecible en dietas variadas.", "Alimentación", "Ferplast", Decimal("3.49"),
        "https://www.mascotasavila.com/cdn/shop/products/98114.png\n", [], [],None),

        ("Pijama", "Pijama suave y cálido para dormir, confeccionado con telas agradables que proporcionan confort nocturno. Ajuste pensado para que la mascota se mueva con libertad y mantenga el calor corporal durante la noche. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("15.99"),
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSM-JQoMcRbHA4NzLRUHNMXcxQSuuZ__LU15g&s\n", ["XS", "S", "M", "L"], ["Azul", "Rosa"],"Algodón"),

        ("Flotador", "Chaleco flotador para mascotas diseñado para mejorar la seguridad en actividades acuáticas; materiales flotantes y sistema de ajuste firme. Costuras y hebillas reforzadas, ideal para entrenamiento en agua y rescates recreativos. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Kong", Decimal("24.99"), 
        "https://media.adeo.com/mkp/7cd776bd670a0b63dfdd340aeebfd723/media.jpeg\n", ["XS", "S", "M", "L"], ["Naranja", "Amarillo"],"Sintético"),

        ("Bañador", "Bañador para mascotas en tejido de secado rápido, con patrón anatómico que no limita el movimiento al nadar. Ofrece protección frente al sol y es muy fácil de lavar; perfecto para días de playa y piscina. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Ferplast", Decimal("11.99"), 
        "https://m.media-amazon.com/images/I/61QmiNqohUL._AC_UF1000,1000_QL80_.jpg\n", ["XS", "S", "M", "L"], ["Verde", "Azul", "Amarillo"],"Poliéster"),

        ("Pañuelo", "Pañuelo de tela suave y transpirable para looks diarios; fácil de colocar y con múltiples estampados disponibles. Funciona como accesorio estético y ligera protección contra el frío en paseos cortos. Producto válido para todo tipo de mascotas, se muestra un perro porque el proveedor nos proporciona así las fotografías", "Ropa", "Bugata Style", Decimal("4.99"), 
        "https://m.media-amazon.com/images/I/61Y08VU-m3L._AC_UF894,1000_QL80_.jpg\n", ["XS", "S", "M", "L"], ["Rojo", "Gris", "Verde", "Blanco"],"Algodón"), 
        ]
        
        productos = []

        for idx, (nombre, desc, cat_nombre, marca_nombre, precio, img_url, tallas, color_nombres, material) in enumerate(productos_data):
            prod = Producto.objects.create(
                nombre=nombre,
                descripcion=desc,
                precio=precio,
                stock=0 if cat_nombre == "Ropa" else random.randint(0, 10),
                categoria=categorias[cat_nombre],
                marca=marcas[marca_nombre],
                es_destacado=10 < idx < 25,
                material=material or "Otros"
            )

            # Si hay colores, guardar el primero como valor representativo en el campo `color`
            if color_nombres:
                prod.color = color_nombres[0]
                prod.save()

            ImagenProducto.objects.create(producto=prod, imagen=img_url, es_principal=True)

            if cat_nombre == "Ropa" and tallas:
                total_stock = 0
                for talla in tallas:
                    stock_talla = random.randint(0, 5)
                    TallaProducto.objects.create(producto=prod, talla=talla, stock=stock_talla)
                    total_stock += stock_talla
                prod.stock = total_stock
                prod.save()
            else:
                TallaProducto.objects.create(producto=prod, talla="Única", stock=prod.stock)

            productos.append(prod)

        # --------------------------
        # 6. Crear carritos con items (carritos genéricos)
        # --------------------------
        for i in range(2):
            carrito = Carrito.objects.create(codigo_carrito=f"CRT-{i+1:03d}")
            for _ in range(random.randint(1, 5)):
                producto_choice = random.choice(productos)
                talla_choice = producto_choice.tallas.first()
                if not talla_choice:
                    talla_choice = TallaProducto.objects.create(producto=producto_choice, talla="Única", stock=producto_choice.stock)
                ItemCarrito.objects.create(
                    carrito=carrito,
                    producto=producto_choice,
                    talla_producto=talla_choice,
                    cantidad=random.randint(1, 3)
                )
        self.stdout.write("✔ Carritos creados")

        # --------------------------
        # 7. Crear pedidos para usuarios (simplificado y compatible con modelos actuales)
        # --------------------------
        def crear_pedidos_para_usuario(usuario, n=3):
            for i in range(1, n + 1):
                seleccion = [random.choice(productos) for _ in range(random.randint(1, 4))]
                total = Decimal("0.00")
                pedido = Pedido.objects.create(
                    stripe_checkout_id=f"seed_{usuario.username}_{i}_{uuid.uuid4().hex[:6]}",
                    cantidad=total,
                    divisa="EUR",
                    cliente_email=usuario.email,
                    status=random.choice(["Paid", "Pending"]),
                )
                for prod in seleccion:
                    qty = random.randint(1, 3)
                    ItemPedido.objects.create(pedido=pedido, producto=prod, cantidad=qty)
                    total += prod.precio * qty
                pedido.cantidad = total
                pedido.save()

        crear_pedidos_para_usuario(user1, n=3)
        crear_pedidos_para_usuario(user2, n=3)

        # --------------------------
        # 8. Carritos asociados a usuarios (no existe relación en modelo Carrito, crear carritos identificados por usuario)
        # --------------------------
        for u in (user1, user2):
            cart_code = f"CRT-{u.username}-{uuid.uuid4().hex[:6].upper()}"
            carrito = Carrito.objects.create(codigo_carrito=cart_code)
            for _ in range(random.randint(1, 4)):
                producto_choice = random.choice(productos)
                talla_choice = producto_choice.tallas.first()
                if not talla_choice:
                    talla_choice = TallaProducto.objects.create(producto=producto_choice, talla="Única", stock=producto_choice.stock)
                ItemCarrito.objects.create(
                    carrito=carrito,
                    producto=producto_choice,
                    talla_producto=talla_choice,
                    cantidad=random.randint(1, 2),
                )

        self.stdout.write("✔ Carritos con items creados")

        # --------------------------
        # 6. Crear pedidos
        #    (combina versión antigua + versión por estados)
        # --------------------------

        # Versión nueva: lista de estados y helper
        estados_envio = [
            "Preparing",
            "On the way", 
            "Delivered",
        ]

        def crear_pedidos_por_estados(usuario, prefix):
            """
            Crea un pedido por cada estado de envío, con productos aleatorios.
            """
            for idx, estado in enumerate(estados_envio, start=1):
                items = []
                for _ in range(random.randint(2, 3)):
                    prod = random.choice(productos)
                    qty = random.randint(1, 3)
                    talla_random = prod.tallas.filter(stock__gt=0).first()
                    talla_value = talla_random.talla if talla_random else "Única"
                    items.append((prod, qty, talla_value))

                total = Decimal("0.00")
                pedido = Pedido.objects.create(
                    stripe_checkout_id=f"seed_checkout_states_{prefix}_{idx}",
                    cantidad=total,
                    divisa="EUR",
                    cliente_email=usuario.email,
                    status="Paid",
                    estado_envio=estado,
                    codigo_seguimiento=f"TRACK-{uuid.uuid4().hex[:8].upper()}",
                )

                for prod, qty, talla in items:
                    ItemPedido.objects.create(
                        pedido=pedido,
                        producto=prod,
                        cantidad=qty,
                        talla=talla,
                    )
                    total += prod.precio * qty

                pedido.cantidad = total
                pedido.save()

        # Versión antigua: pedidos fijos de ejemplo
        pedidos_user1 = [
            [(productos[0], 2, "M"), (productos[1], 1, "Única")],
            [(productos[2], 1, "Única"), (productos[3], 3, "Única")],
        ]

        for i, items in enumerate(pedidos_user1, start=1):
            total = Decimal("0.00")
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"seed_checkout_user1_{i}",
                cantidad=total,
                divisa="EUR",
                cliente_email=user1.email,
                status="Paid",
                estado_envio="Delivered",
                codigo_seguimiento=f"TRACK-{uuid.uuid4().hex[:8].upper()}"
            )
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
            [(productos[6], 1), (productos[12], 2)], 
            [(productos[15], 2)], 					
            [(productos[18], 1), (productos[19], 1)], 
        ]

        for i, items in enumerate(pedidos_user2, start=1):
            pedido = Pedido.objects.create(
                stripe_checkout_id=f"seed_checkout_user2_{i}",
                cantidad=total,
                divisa="EUR",
                cliente_email=user2.email,
                status="Paid",
                estado_envio="On the way",
                codigo_seguimiento=f"TRACK-{uuid.uuid4().hex[:8].upper()}"
            )
            total = Decimal("0.00")
            for prod, qty in items:
                ItemPedido.objects.create(pedido=pedido, producto=prod, cantidad=qty, talla=talla)
                total += prod.precio * qty
            pedido.cantidad = total
            pedido.save()

        # Llamar también a la versión genérica por estados
        crear_pedidos_por_estados(user1, "user1")
        crear_pedidos_por_estados(user2, "user2")

        self.stdout.write("✔ Pedidos fijos de ejemplo creados")
        self.stdout.write("✔ Pedidos por estados creados para cada usuario")
        self.stdout.write(self.style.SUCCESS("✅ Datos generados correctamente"))
