# Mi parte: algoritmo propuesto de la etapa 1

Se tomó como supuesto que corresponde al genético con Split del Entregable 1.
Es el mismo tipo de método que el genético, no un cuarto algoritmo independiente.

- **72 corridas reales:** 24 instancias, semillas 0, 1 y 2.
- **72/72 factibles** bajo capacidad, cobertura y duración cuando corresponde.
- Parámetros: población 60, 150 generaciones, torneo 3, cruce 0.90,
  mutación 0.25 (swap/inversión 50/50), elitismo 2.
- 9060 evaluaciones por corrida; no se agregó búsqueda local.
- Distancias CMT reales; X redondeadas por arco.
- **Sin tope adicional de vehículos**, igual que el algoritmo de etapa 1.
  Si se acuerda un tope o flota exacta, hay que repetir bajo esa regla.
- Tiempo total de algoritmo: 543.20 s.
- Reducción media frente al mejor individuo inicial: 43.77%.
- Diferencia media no ponderada con referencias CVRPLIB: CMT 94.26%; X 206.48%.
  Esto muestra una línea base de calidad limitada, no una solución óptima.

## Archivos para integrar

- `reporte/propuesto/informe_propuesto.pdf`: lectura de mi sección completa.
- `reporte/propuesto/seccion_propuesto.tex`: sección editable para incluir en LaTeX.
- `reporte/propuesto/referencias.bib`: bibliografía de la sección.
- `resultados/propuesto/corridas.csv`: resultados individuales.
- `resultados/propuesto/resumen.csv`: media, desviación, mejor/peor, tiempo e iteraciones.
- `resultados/propuesto/detalle_corridas.json`: rutas e historias, con validación.
- `resultados/propuesto/rutas_mejores.csv`: rutas de la mejor corrida de cada caso, con carga y duración.
- `resultados/propuesto/comparacion_literatura.csv`: diferencia con referencias verificadas.
- `graficas/propuesto/`: tres figuras de convergencia, tiempo y rutas.
- `algoritmos/propuesto/`: código para repetir la parte.

## Qué queda para el reporte global

Comparar con los resultados reales de ACO, del modelo y del estudio factorial
del GA del otro integrante. No se hicieron sus partes ni se inventaron resultados.
La comparación con literatura no equivale al GAP contra el modelo del equipo.
Con un solo conjunto fijo de parámetros no se puede afirmar cuáles son los mejores niveles.

## Integrar en Overleaf

Subir las carpetas `reporte/propuesto/` y `graficas/propuesto/` conservando rutas.
El archivo principal autónomo es `reporte/propuesto/informe_propuesto.tex`.
Para un documento de equipo, copiar el contenido de `seccion_propuesto.tex`
o incluirlo con `\input{reporte/propuesto/seccion_propuesto.tex}`.
Se requieren `amsmath`, `booktabs`, `graphicx`, `float`, `hyperref` y
compatibilidad con español. Agregar las entradas de `referencias.bib` a la
bibliografía del equipo. Los `\clearpage` pueden retirarse al integrar.

## Repetir

Desde raíz, Python 3.10 o superior:

```bash
python -m algoritmos.propuesto.ejecutar
python -m algoritmos.propuesto.generar_reporte
```

El primer comando sobrescribe solo la carpeta de resultados del propuesto;
usar `--salida resultados/propuesto_nueva` para conservar las corridas entregadas.
No volver a medir tiempos en paralelo con otras optimizaciones.
