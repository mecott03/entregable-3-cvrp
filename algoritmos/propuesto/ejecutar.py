"""Ejecutar desde raíz: python -m algoritmos.propuesto.ejecutar"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import platform
from pathlib import Path
import statistics
import sys

from comun.instancias import leer, validar
from .ga_split import Config, resolver


def guardar_csv(path, filas):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def ejecutar(args):
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    archivos = sorted(Path(args.instancias).glob(args.patron))
    if not archivos:
        raise ValueError("No se encontraron instancias")
    cfg = Config(generaciones=args.generaciones, max_vehiculos=args.max_vehiculos)
    semillas = [int(x) for x in args.semillas.split(",")]
    if len(semillas) != len(set(semillas)):
        raise ValueError("Se requieren semillas distintas")
    corridas, detalle, resumen = [], [], []
    inicio = datetime.now(timezone.utc).isoformat()
    for path in archivos:
        ins = leer(path, args.distancias)
        grupo = []
        for numero, seed in enumerate(semillas, 1):
            r = resolver(ins, seed, cfg)
            check = validar(ins, r["rutas"], cfg.max_vehiculos)
            if r["distancia"] is not None:
                if abs(check["distancia"]-r["distancia"]) > 1e-6:
                    raise AssertionError("Split y validador no coinciden en costo")
            fila = dict(instancia=ins.nombre, algoritmo="propuesto_GA_Split_etapa1",
                        configuracion="base_etapa1", corrida=numero, semilla=seed,
                        distancia=r["distancia"], tiempo_s=r["tiempo_s"],
                        iteraciones=r["iteraciones"], iteracion_mejor=r["iteracion_mejor"],
                        evaluaciones=r["evaluaciones"], vehiculos=check["vehiculos"],
                        factible=check["factible"] and r["distancia"] is not None,
                        estado_solver="no_aplica", cota_inferior="",
                        convencion_distancias=ins.convencion,
                        flota_maxima=cfg.max_vehiculos,
                        archivo_rutas="resultados/propuesto/detalle_corridas.json")
            corridas.append(fila)
            grupo.append(fila)
            detalle.append(dict(instancia=ins.nombre, corrida=numero,
                                validacion=check, **r))
            # Guardado incremental; interrupciones conservan corridas terminadas.
            guardar_csv(salida/"corridas.csv", corridas)
            (salida/"detalle_corridas.json").write_text(
                json.dumps(detalle, ensure_ascii=False, allow_nan=False), encoding="utf-8")
            print(f"{ins.nombre} semilla={seed}: Z={r['distancia']}, "
                  f"t={r['tiempo_s']:.3f}s, rutas={check['vehiculos']}, "
                  f"factible={fila['factible']}", flush=True)
        factibles = [r for r in grupo if r["factible"]]
        valores = [r["distancia"] for r in factibles]
        resumen.append(dict(instancia=ins.nombre, clientes=len(ins.demandas)-1,
                            corridas=len(grupo), factibles=len(factibles),
                            distancia_media=statistics.mean(valores) if valores else None,
                            distancia_desv_muestral=statistics.stdev(valores) if len(valores)>1 else None,
                            distancia_mejor=min(valores) if valores else None,
                            distancia_peor=max(valores) if valores else None,
                            tiempo_medio_s=statistics.mean(r["tiempo_s"] for r in grupo),
                            iteraciones_media=statistics.mean(r["iteraciones"] for r in grupo),
                            iteracion_mejor_media=statistics.mean(r["iteracion_mejor"] for r in factibles) if factibles else None,
                            evaluaciones_media=statistics.mean(r["evaluaciones"] for r in grupo),
                            vehiculos_media=statistics.mean(r["vehiculos"] for r in factibles) if factibles else None,
                            vehiculos_min=min((r["vehiculos"] for r in factibles), default=None),
                            vehiculos_max=max((r["vehiculos"] for r in factibles), default=None),
                            convencion_distancias=ins.convencion,
                            flota_maxima=cfg.max_vehiculos))
        guardar_csv(salida/"resumen.csv", resumen)
    metadatos = dict(inicio_utc=inicio, fin_utc=datetime.now(timezone.utc).isoformat(),
                     python=sys.version, plataforma=platform.platform(),
                     procesador=platform.processor(), ejecucion="secuencial_un_proceso",
                     parametros=asdict(cfg), semillas=semillas,
                     max_vehiculos="sin_limite_adicional" if cfg.max_vehiculos is None else cfg.max_vehiculos,
                     distancias="auto: CMT real; X floor(d+0.5)" if args.distancias=="auto" else args.distancias,
                     tiempo="perf_counter; excluye lectura, matriz, validación, CSV y figuras",
                     hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in archivos},
                     codigo_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [Path(__file__), Path(__file__).with_name("ga_split.py"), Path("comun/instancias.py")]})
    (salida/"metadatos.json").write_text(json.dumps(metadatos, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instancias", default="instancias")
    p.add_argument("--patron", default="*.vrp")
    p.add_argument("--salida", default="resultados/propuesto")
    p.add_argument("--semillas", default="0,1,2")
    p.add_argument("--generaciones", type=int, default=150)
    p.add_argument("--max-vehiculos", type=int, default=None)
    p.add_argument("--distancias", choices=["auto", "real", "entera"], default="auto")
    ejecutar(p.parse_args())


if __name__ == "__main__":
    main()
