"""Lector para las 24 instancias adjuntas, sin dependencias externas.

Los archivos no declaran una flota máxima. El sufijo k de X se conserva
como referencia del nombre; no se convierte silenciosamente en restricción.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import hashlib
import math
import re


@dataclass
class Instancia:
    nombre: str
    coordenadas: dict
    demandas: dict
    capacidad: float
    deposito: int
    duracion_maxima: float | None
    servicio: float
    convencion: str
    distancias: dict
    k_nombre: int | None
    comentario: str

    def distancia_ruta(self, ruta):
        camino = [self.deposito, *ruta, self.deposito]
        return sum(self.distancias[a, b] for a, b in zip(camino, camino[1:]))

    def carga_ruta(self, ruta):
        return sum(self.demandas[i] for i in ruta)

    def duracion_ruta(self, ruta):
        return self.distancia_ruta(ruta) + self.servicio * len(ruta)


def leer(path, convencion="auto"):
    """auto: CMT euclidiana real; X euclidiana redondeada floor(d+0.5).

    La duración se interpreta como distancia + servicio por cliente,
    suponiendo una unidad de tiempo por unidad de distancia.
    El depósito no recibe tiempo de servicio.
    """
    if convencion not in {"auto", "real", "entera"}:
        raise ValueError("Convención desconocida")
    meta, coords, demandas, depositos = {}, {}, {}, []
    seccion = None
    for raw in Path(path).read_text().splitlines():
        linea = raw.strip()
        if not linea or linea == "EOF":
            continue
        if linea.endswith("_SECTION"):
            seccion = linea
            continue
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            meta[clave.strip()] = valor.strip()
            seccion = None
        elif seccion == "NODE_COORD_SECTION":
            i, x, y = linea.split()
            coords[int(i)] = (float(x), float(y))
        elif seccion == "DEMAND_SECTION":
            i, q = linea.split()
            demandas[int(i)] = float(q)
        elif seccion == "DEPOT_SECTION":
            i = int(linea)
            if i != -1:
                depositos.append(i)
        else:
            raise ValueError(f"Línea no reconocida: {linea}")
    if meta.get("EDGE_WEIGHT_TYPE") != "EUC_2D":
        raise ValueError("Solo se admite EUC_2D")
    if len(depositos) != 1:
        raise ValueError("Se requiere un depósito explícito")
    if set(coords) != set(demandas) or len(coords) != int(meta["DIMENSION"]):
        raise ValueError("Coordenadas, demandas y DIMENSION no coinciden")
    deposito = depositos[0]
    capacidad = float(meta["CAPACITY"])
    if deposito not in coords or demandas[deposito] != 0 or capacidad <= 0:
        raise ValueError("Depósito/capacidad inválidos")
    if any(q < 0 or q > capacidad for q in demandas.values()):
        raise ValueError("Demanda inválida")
    nombre = meta.get("NAME", Path(path).stem)
    if convencion == "auto":
        if nombre.startswith("CMT"):
            convencion = "real"
        elif nombre.startswith("X-"):
            convencion = "entera"
        else:
            raise ValueError("Elegir real o entera para familias desconocidas")
    distancias = {}
    for i in coords:
        for j in coords:
            d = math.dist(coords[i], coords[j])
            distancias[i, j] = math.floor(d + 0.5) if convencion == "entera" else d
    k = re.search(r"-k(\d+)$", nombre)
    return Instancia(nombre, coords, demandas, capacidad, deposito,
                     float(meta["DISTANCE"]) if "DISTANCE" in meta else None,
                     float(meta.get("SERVICE_TIME", 0)), convencion,
                     distancias, int(k.group(1)) if k else None, meta.get("COMMENT", ""))


def validar(instancia, rutas, max_vehiculos=None):
    """Rutas = listas de CLIENTES, sin repetir depósito en los extremos.

    Valida cobertura exacta, capacidad, duración y flota si se especifica.
    Una ruta inválida no debe entrar en promedios de soluciones factibles.
    """
    from collections import Counter
    errores = []
    clientes = set(instancia.demandas) - {instancia.deposito}
    visitas = [i for ruta in rutas for i in ruta]
    if Counter(visitas) != Counter({i: 1 for i in clientes}):
        errores.append("Cobertura inválida: faltan, sobran o se repiten clientes")
    if any(not r for r in rutas):
        errores.append("Hay rutas vacías")
    if max_vehiculos is not None and len(rutas) > max_vehiculos:
        errores.append("Se excede la flota máxima acordada")
    if any(i not in clientes for i in visitas):
        return {"factible": False, "errores": errores, "distancia": None,
                "vehiculos": len(rutas)}
    for n, ruta in enumerate(rutas, 1):
        if instancia.carga_ruta(ruta) > instancia.capacidad + 1e-8:
            errores.append(f"Ruta {n}: capacidad excedida")
        if (instancia.duracion_maxima is not None and
                instancia.duracion_ruta(ruta) > instancia.duracion_maxima + 1e-8):
            errores.append(f"Ruta {n}: duración excedida")
    return {"factible": not errores, "errores": errores,
            "distancia": sum(instancia.distancia_ruta(r) for r in rutas),
            "vehiculos": len(rutas)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carpeta", default="instancias")
    parser.add_argument("--salida", default="resultados/inventario_instancias.csv")
    args = parser.parse_args()
    filas = []
    for path in sorted(Path(args.carpeta).glob("*.vrp")):
        ins = leer(path)
        filas.append(dict(instancia=ins.nombre, clientes=len(ins.demandas)-1,
                          capacidad=ins.capacidad, deposito=ins.deposito,
                          duracion_maxima=ins.duracion_maxima,
                          servicio_por_cliente=ins.servicio,
                          convencion_distancias=ins.convencion,
                          k_referencia_nombre=ins.k_nombre,
                          flota_maxima_archivo="no_declarada",
                          comentario_archivo=ins.comentario,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if not filas:
        raise ValueError("No se encontraron instancias")
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0]))
        writer.writeheader()
        writer.writerows(filas)
    print(f"{len(filas)} instancias leídas: {args.salida}")


if __name__ == "__main__":
    main()
