import csv #guardar en csv
import re
import time #madnar búsquedas con tiempo de retardo
import requests #html
from bs4 import BeautifulSoup #localizar filas de las tablas
from pathlib import Path #Clase Path para manejar rutas de archivos


#Se crean variables globales para la URL, ID, número de tabla, cabeceras y ruta de salida
URL = "https://www.idescat.cat/indicadors/"
ID = "aec"
TABLA_NUM = "15707"  # Precio de vivienda de segunda mano
HEADERS = {
    "User-Agent": "UOC-Vivienda/0.1 (proyecto academico: balcarazl@uoc.edu & crodriguezcaz@uoc.edu)"
}
OUTPUT_PATH = Path("data/precios_vivienda_comarcas_catalunya.csv")


def get_soup(params: dict) -> BeautifulSoup:
    """
    Función para obtener el contenido HTML de la página y parsearlo con BeautifulSoup.
    params: Diccionario con los parámetros de la consulta.
    return: Objeto BeautifulSoup con el contenido parseado.
    """
    response = requests.get(URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()  # Lanza una excepción si la respuesta no es 200
    return BeautifulSoup(response.content, "html.parser")

def  get_regions () -> list:
    """
    Función para extraer los territorios disponibles en el selector de la página.
    soup: Objeto BeautifulSoup con el contenido parseado.
    return: Lista de diccionarios con los códigos y nombres de los territorios.
    """
    params = {"id": ID, "n": TABLA_NUM, "lang": "ca", "fil": "14"}  # Filtra por comarcas
    soup = get_soup(params)

    selector = soup.select_one('select[name="fil"]')
    if selector is None:
        raise ValueError("No se ha encontrado el selector de territorios")

    regions = []
    for opcion in selector.select("option[value]"):
        if opcion["value"].strip():
            regions.append({
                "region_code": opcion["value"],
                "region_name": opcion.get_text(" ", strip=True),
            })

    return regions


def extract_data(region_code: str, region_name: str) -> list:
    """
    Función para extraer los datos de la tabla de precios de vivienda.
    soup: Objeto BeautifulSoup con el contenido parseado.
    region_code: Código del territorio actual.
    region_name: Nombre del territorio actual.
    return: Lista de diccionarios con los registros extraídos.
    """
    params = {"id": ID, "n": TABLA_NUM, "lang": "ca", "region_code": region_code}
    soup = get_soup(params)

    tabla = soup.select_one("table.ApartNum")
    if tabla is None:
        raise ValueError("No se ha encontrado la tabla de datos")
    
    # Extraer el año del título/caption de la tabla (ej. '... 2023')
    caption_elem = tabla.find("caption")
    caption_text = caption_elem.get_text(" ", strip=True) if caption_elem else ""
    match_year = re.search(r"\b(20\d{2})\b", caption_text)
    anio_detectado = match_year.group(1) if match_year else "2023"

    log = []
    rows = tabla.select("tbody tr")
   
    for idx, row in enumerate(rows, start=1):
        celdas = row.find_all(["th", "td"])
        valores = [celda.get_text(" ", strip=True) for celda in celdas]

        if len(valores) != 3:
            raise ValueError(f"Fila con estructura inesperada: {valores}")
        else:
            log.append({
                "codigo_territorio": idx,
                "territorio": valores[0],
                "anio": anio_detectado,
                "precio_eur_m2": valores[1],
                "variacion_pct": valores[2],
                "url_fuente": f"{URL}?id={ID}&n={TABLA_NUM}&lang=ca",
            })

    return log


def save_dataset (log: list[dict], output_path: Path) -> None:
    """Crea la carpeta si no existe y guarda el archivo CSV detectando

    automáticamente los nombres de las columnas.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not log:
        print("La lista de registros está vacía. No se ha generado el archivo.")
        return

    # Extrae automáticamente los encabezados de las claves del primer registro
    fieldnames = list(log[0].keys())

    # 'utf-8-sig' añade la marca BOM necesaria para que Excel abra acentos y caracteres especiales correctamente
    with open(
        output_path, mode="w", newline="", encoding="utf-8-sig"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(log)

