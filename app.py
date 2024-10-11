import requests
from bs4 import BeautifulSoup
import re, time
from lxml import etree
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import xmltodict 
from xml.sax.saxutils import escape


# URL base de la página
url_base = "https://xxxxxxxxxxxxxxxxxx"


# Lista donde almacenaremos todas las subcategorías
enlaces_categorias = []
todas_subcategorias = []
json_resultado = {}

archivo = "xxxxxxxxxxxxx.json"


def guardar_como_json():
    global json_resultado
    # Guardar el objeto json_resultado antes de salir
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(json_resultado, f, ensure_ascii=False, indent=4)
    

def guardar_como_xml():
    global json_resultado

    # Convertir el JSON a XML
    xml_data = xmltodict.unparse({"datos": json_resultado}, pretty=True)

    # Reemplazar las entidades escapadas manualmente
    reemplazos = {
        '&lt;![CDATA[': '<![CDATA[',   # CDATA apertura
        ']]&gt;': ']]>',               # CDATA cierre
        '&lt;': '<',                   # Menor que
        '&gt;': '>',                   # Mayor que
        '&amp;': '&',                  # Ampersand
        '&quot;': '"',                 # Comillas dobles
        '&#39;': "'",                  # Comillas simples/apóstrofes
        '&#x27;': "'",                 # Comillas simples/apóstrofes (otra codificación)
        '&#x2F;': '/',                 # Barra inclinada
        '&#x5C;': '\\',                # Barra invertida
        '&cent;': '¢',                 # Símbolo de centavo
        '&euro;': '€',                 # Símbolo de euro
        '&pound;': '£',                # Símbolo de libra
        '&yen;': '¥',                  # Símbolo de yen
        '&copy;': '©',                 # Símbolo de copyright
        '&reg;': '®'                   # Símbolo de marca registrada
    }

    # Aplicar todos los reemplazos
    for key, value in reemplazos.items():
        xml_data = xml_data.replace(key, value)

    # Escribir el XML a un archivo
    with open('xxxxxxxxxxxxx.xml', 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_data)




def agregar_categorias():
    global enlaces_categorias
    # Abrir y leer el archivo 'categorias.txt'
    with open('cat_base.txt', 'r') as file:
        nuevas_categorias = file.readlines()
    
    # Limpiar espacios en blanco y líneas vacías
    nuevas_categorias = [categoria.strip() for categoria in nuevas_categorias if categoria.strip()]
    
    # Agregar solo las categorías que no están ya en 'enlaces_categorias'
    for categoria in nuevas_categorias:
        if categoria not in enlaces_categorias:
            enlaces_categorias.append(categoria)


def peticion_inicial():
    global enlaces_categorias
    # Hacemos la solicitud a la página
    response = requests.get(url_base)
    
    
    
    
    # Verificamos que la solicitud fue exitosa
    if response.status_code == 200:
        # Analizamos el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        #print(soup)
        
        # Buscamos todos los enlaces <a> que sigan el patrón
        enlaces_categorias = []
        
        # Expresión regular para buscar los enlaces que inicien con número seguido de guion
        patron = re.compile(r'/\d+-')
    
        # Recorremos todos los enlaces <a> de la página
        for enlace in soup.find_all('a', href=True):
            href = enlace['href']
            
            # Si el enlace coincide con el patrón, lo agregamos a la lista
            if patron.match(href):
                # Nos aseguramos de que el enlace sea absoluto
                if not href.startswith('http'):
                    href = url_base + href
                enlaces_categorias.append(href)
                enlaces_categorias = list(set(enlaces_categorias))

        # Imprimimos los enlaces encontrados
        print("Enlaces de categorías únicas:")
        for enlace in enlaces_categorias:
            print(enlace)
            
            
    else:
        print(f"Error al acceder a la página: {response.status_code}")




# Función para obtener subcategorías de una categoría
def obtener_subcategorias(url_categoria):
    # Hacemos la solicitud a la página de la categoría
    response = requests.get(url_categoria)

    # Verificamos que la solicitud fue exitosa
    if response.status_code == 200:
        # Analizamos el contenido HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscamos el bloque que contiene las subcategorías
        bloque_subcategorias = soup.find('div', class_='block-categories hidden-sm-down')

        # Si existe el bloque, buscamos todos los enlaces a subcategorías
        if bloque_subcategorias:
            subcategorias = []
            for enlace in bloque_subcategorias.find_all('a', href=True):
                href = enlace['href']
                # Nos aseguramos de que el enlace sea absoluto
                if not href.startswith('http'):
                    href = url_base + href
                subcategorias.append(href)
            
            return subcategorias
        else:
            print(f"No se encontraron subcategorías en {url_categoria}")
            return []
    else:
        print(f"Error al acceder a la categoría: {url_categoria}")
        return []


def integrar_subcategorias():
    global todas_subcategorias
    # Recorremos cada enlace de categoría que obtuviste en la fase anterior
    for enlace_categoria in enlaces_categorias:
        print(f"Buscando subcategorías en {enlace_categoria}...")
        
        # Obtenemos las subcategorías de la categoría actual
        subcategorias = obtener_subcategorias(enlace_categoria)
        
        # Agregamos las subcategorías encontradas a la lista general
        todas_subcategorias.extend(subcategorias)

    # Eliminar duplicados de las subcategorías
    todas_subcategorias = list(set(todas_subcategorias))
    
    
    #validar dentro de json resultados que si se encuentra una categoria ya registrada en json_resultado["categorias_url"], se elimine de toda_subcategorias
    todas_subcategorias = [subcat for subcat in todas_subcategorias if subcat not in json_resultado["categorias_url"]]
    
    
    # Imprimir todas las subcategorías encontradas
    print("Subcategorías encontradas:")
    for subcategoria in todas_subcategorias:
        print(subcategoria)


# Función para obtener los productos de cada subcategoría
def obtener_productos(subcategoria: str):
    # Hacemos la solicitud a la página de la subcategoría
    response = requests.get(subcategoria+"?resultsPerPage=1777")
    
    # Verificamos que la solicitud fue exitosa
    if response.status_code == 200:
        # Analizamos el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos todos los productos en la subcategoría
        productos = soup.find_all('article', class_='product-miniature js-product-miniature')
        
        # Extraemos las URL de los productos
        urls_productos = []
        for producto in productos:
            enlace = producto.find('a', class_='thumbnail product-thumbnail')
            if enlace and 'href' in enlace.attrs:
                urls_productos.append(enlace['href'])
                
        
        return urls_productos
    else:
        print(f"Error en la solicitud para {subcategoria} ({response.status_code})")
        return []

def extraer_tabla(tabla):
    datos_tabla = []
    for fila in tabla.find_all('tr'):
        celdas = fila.find_all('td')
        if len(celdas) == 2:
            clave = celdas[0].get_text(strip=True)
            valor = celdas[1].get_text(strip=True)
            datos_tabla.append(f"{clave}: {valor}")
    return datos_tabla


def crear_objeto_anidado(categorias,caracteristicas, datos_producto, json_resultado):
    

    if "document" not in json_resultado:
        json_resultado["document"] = {"product": []}

    producto_woocommerce = {
        "title": datos_producto["nombre"],
        "group_id": datos_producto["referencia"].split(": ")[-1],
        "price": datos_producto["precio_normal"].split(" ")[0],
        "categories": {"category": categorias},
        "description": "\n".join(datos_producto["descripcion"]),
        "images": datos_producto["imagenes"],
        "caracteristics": "\n".join(caracteristicas),
    }
   #print("Producto WooCommerce creado:", producto_woocommerce)  # Añadir esta línea para depuración

    json_resultado["document"]["product"].append(producto_woocommerce)

    return json_resultado


# Función para obtener datos de un producto y construir la estructura de categorías
def obtener_datos_del_producto(url):
    
    global json_resultado
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Obtener categorías
    breadcrumb = soup.find('nav', class_='breadcrumb')
    categorias = []
    if breadcrumb:
        categorias = [categoria.get_text(strip=True) for categoria in breadcrumb.find('ol').find_all('li')]
    
    # Obtener datos específicos del producto
    nombre_producto = soup.select_one('.ce-product-name.elementor-heading-title')
    nombre_producto = nombre_producto.get_text(strip=True) if nombre_producto else ''
    
    # Obtener todas las imágenes del producto
    imagenes_producto = []
    
    # Obtener la imagen principal
    imagen_principal = soup.select_one('img.elementor-carousel-image')
    if imagen_principal and 'src' in imagen_principal.attrs:
        imagenes_producto.append(imagen_principal['src'])
    
    # Obtener todas las imágenes del carrusel
    carrusel = soup.find('div', class_='swiper-wrapper')
    if carrusel:
        slides = carrusel.find_all('div', class_='swiper-slide')
        for slide in slides:
            img = slide.find('img', class_='elementor-carousel-image')
            if img and 'src' in img.attrs:
                src = img['src']
                if src.startswith('https://xxxxxxxxxxxxxxxxxx/') and src not in imagenes_producto:
                    imagenes_producto.append(src)
    
    referencia_label = soup.select_one('.ce-product-meta__label')
    referencia_label = referencia_label.get_text(strip=True) if referencia_label else ''
    
    referencia_valor = soup.select_one('.ce-product-meta__value')
    referencia_valor = referencia_valor.get_text(strip=True) if referencia_valor else ''
    
    precio_normal = soup.select_one('span[aria-label="{l s=\'Price\' d=\'Shop.Theme.Catalog\'}"]')
    precio_normal = precio_normal.get_text(strip=True) if precio_normal else ''
    
    precio_iva = soup.select_one('div.elementor-element-bdc2f0f span.price_iva_incluido')
    precio_iva = precio_iva.get_text(strip=True) if precio_iva else ''
        
    # Obtener descripción completa
    descripcion_div = soup.select_one('div.ce-product-description')
    if descripcion_div:
        descripcion = ['<![CDATA[<B><FONT SIZE=1><SPAN LANG="ES-MODERN">']
        for element in descripcion_div.children:
            if element.name == 'p':
                texto = element.get_text(strip=True)
                if texto:
                    if element.find(['strong', 'b']):
                        descripcion.append(f"<P><B>{escape(texto)}: </B></P>")
                    else:
                        descripcion.append(f"<P>{escape(texto)}</P>")
            elif element.name == 'table':
                descripcion.append("<P><B>Tabla de características:</B></P>")
                tabla_contenido = extraer_tabla(element)
                for fila in tabla_contenido:
                    descripcion.append(f"<P>{escape(fila)}</P>")
            elif element.name in ['ul', 'ol']:
                for item in element.find_all('li'):
                    descripcion.append(f"<P>{escape(item.get_text(strip=True))}</P>")
        descripcion.append("</SPAN></FONT>]]>")
    else:
        descripcion = []
    
    
    
    # Obtener características del producto
    caracteristicas = ['<![CDATA[<B><FONT SIZE=1><SPAN LANG="ES-MODERN">']
    tabla_caracteristicas = soup.find('table', class_='ce-product-features')
    if tabla_caracteristicas:
        caracteristicas.append("<P><B>Características del producto:</B></P>")
        filas = tabla_caracteristicas.find_all('tr', class_='ce-product-features__row')
        for fila in filas:
            etiqueta = fila.find('th', class_='ce-product-features__label')
            valor = fila.find('td', class_='ce-product-features__value')
            if etiqueta and valor:
                etiqueta_texto = etiqueta.get_text(strip=True)
                valor_texto = valor.get_text(strip=True)
                caracteristica = f"<P><B>{escape(etiqueta_texto)}:</B> {escape(valor_texto)}</P>"
                caracteristicas.append(caracteristica)
    caracteristicas.append("</SPAN></FONT>]]>")

    

    
    datos_producto = {
        "nombre": nombre_producto,
        "imagenes": imagenes_producto,
        "referencia": referencia_label + ": " + referencia_valor,
        "precio_normal": precio_normal,
        "precio_con_iva": precio_iva.replace("IVA incl.","").replace("(","").replace(")",""),
        "descripcion": descripcion
    }

    
    # Crear objeto anidado
    json_resultado = crear_objeto_anidado(categorias,caracteristicas, datos_producto,json_resultado)
    

    
    return json_resultado


def procesar_producto(url):
    
    while True:
        
        try:
            datos = obtener_datos_del_producto(url)
            return datos           
        except Exception as e:
            print(e)
            time.sleep(30)
    

    

# Función para validar las subcategorías usando XPath
def scrapear_subcategorias(lista_subcategorias: list):
    global json_resultado
    cantidad_c = str(len(lista_subcategorias))
    acum_cat = 0    
    
    for subcategoria in lista_subcategorias:
        # Hacemos la solicitud a la página de la subcategoría
        response = requests.get(subcategoria)
        acum_cat +=1
        
        # Verificamos que la solicitud fue exitosa
        if response.status_code == 200:
            # Convertimos el contenido a un árbol de elementos XML usando lxml
            tree = etree.HTML(response.text)
            
            # Usamos el selector XPath para buscar el producto
            productos = tree.xpath('//*[@id="js-product-list"]/div[1]/div[1]/article')
            
            # Si se encuentran productos, imprimimos OK, sino, imprimimos Error
            if productos:
                
                #obtiene el listado de productos en esa categoria
                urls_productos = obtener_productos(subcategoria)
                
                cantidad_p = str(len(urls_productos))
                acum = 1
                
                print("\n\niniciando scraping de la categoria: "  + subcategoria, 
                      "\n\nLa categoría tiene " + (cantidad_p) +" productos\n")
                
                
                
                
                # Usar ThreadPoolExecutor para procesar productos en paralelo
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # Crear un futuro para cada URL de producto
                    future_to_url = {executor.submit(procesar_producto, url): url for url in urls_productos}
                    
                    # Procesar los resultados a medida que se completan
                    for future in as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            print( "Categoría: ",  str(acum_cat) +"/"+ cantidad_c, "; Obteniendo artículo ---->" , " " ,  str(acum) +"/"+ cantidad_p)
                            future.result()
                            acum += 1
                            
                            # Aquí puedes hacer algo con los datos del producto si es necesario
                        except Exception as exc:
                            print(f"Error procesando {url}: {exc}")
            else:
                print(f"{subcategoria} - Error, categoría sin productos")
        else:
            print(f"{subcategoria} - Error en la solicitud ({response.status_code})")
        
        
        
        if "categorias_url" not in json_resultado:
            json_resultado["categorias_url"] = []
        json_resultado["categorias_url"].append(subcategoria)

        guardar_como_json()
        guardar_como_xml()



archivo = "xxxxxxxxxxxxx.json"

# Verificar si el archivo existe y no está vacío
if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
    with open(archivo, 'r', encoding='utf-8') as f:
        try:
            json_resultado = json.load(f)
        except json.JSONDecodeError:
            json_resultado = {}
else:
    json_resultado = {}
    json_resultado["categorias_url"] = []



try:
    
    peticion_inicial()
    agregar_categorias()
    integrar_subcategorias()
    scrapear_subcategorias(todas_subcategorias)


finally:

    guardar_como_json()
    guardar_como_xml()
    
    print("Datos guardados en el json y xml")

