# Algoritmo propuesto: genético con Split de la etapa 1

Se adoptó el supuesto autorizado de que esta es la parte asignada. Es el
método del Anexo 3 del Entregable 1, no un algoritmo independiente del genético.

Desde raíz, Python 3.10 o superior:

```bash
python -m algoritmos.propuesto.ejecutar
python -m algoritmos.propuesto.generar_reporte
python -m unittest discover -s tests -v
```

El algoritmo no requiere dependencias externas. Para figuras, instalar
`requirements-figuras.txt`.

- `ga_split.py`: algoritmo y Split con capacidad, duración y flota máxima opcional.
- `ejecutar.py`: experimentos y exportación incremental CSV/JSON, sin gráficos.
- `generar_reporte.py`: valida rutas guardadas y genera figuras, comparación con
  literatura y LaTeX. No vuelve a ejecutar el algoritmo.

Parámetros originales: 60 individuos, 150 generaciones, torneo 3, cruce 0.9,
mutación 0.25, elitismo 2. Tres semillas: 0, 1, 2. Sin búsqueda local.

Las ejecuciones entregadas **no imponen límite adicional de flota**. El código
admite `--max-vehiculos K` para repetir con un máximo común; eso cambia el
problema. El modo con flota puede encontrar tours sin partición factible;
registra esa ausencia y no la transforma en una solución ficticia. No garantiza
que encontrará factibilidad para cualquier límite de flota.

Ejemplo para una instancia, conservando los resultados entregados:

```bash
python -m algoritmos.propuesto.ejecutar --patron CMT1.vrp --salida resultados/prueba_CMT1
```

`--distancias real` y `--distancias entera` permiten repetir bajo una convención
uniforme si lo acuerda el equipo. Por defecto: CMT real, X entera por arco.
`--generaciones` cambia el presupuesto; las corridas entregadas usan 150.
El generador del reporte está diseñado para las 72 corridas base.

Sección para compartir: `reporte/propuesto/LEEME_MI_PARTE.md`.
