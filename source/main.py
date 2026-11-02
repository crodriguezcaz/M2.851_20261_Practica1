import time
from pathlib import Path
from scraper import extract_data, get_regions, save_dataset

# Calcula de forma dinámica la raíz del proyecto subiendo un nivel desde source/
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Define la salida exactamente en la carpeta /dataset requerida por la UOC
OUTPUT_PATH = (
    RAIZ_PROYECTO / "dataset" / "precios_vivienda_comarcas_catalunya.csv"
)


def main():
    print("=== INICIANDO PROCESO DE EXTRACCIÓN DE DATOS ===")
    print(f"Ruta de destino configurada: {OUTPUT_PATH}\n")

    regions = get_regions()
    print(f"Se han identificado {len(regions)} territorios/comarcas.")

    all_logs = []

    for idx, region in enumerate(regions, start=1):
        print(
            f"[{idx}/{len(regions)}] Descargando: {region['region_name']} (Código: {region['region_code']})..."
        )
        data = extract_data(region["region_code"], region["region_name"])
        all_logs.extend(data)
        time.sleep(1)  # Pausa responsable de 1 segundo

    print(f"\nProceso finalizado. Registros totales extraídos: {len(all_logs)}")
    print("Generando archivo CSV...")
    save_dataset(all_logs, OUTPUT_PATH)


if __name__ == "__main__":
    main()



