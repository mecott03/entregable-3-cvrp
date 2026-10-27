# Entregable 3 · CVRP · Equipo 5

Base compartida para experimentación y comparación del modelo matemático,
algoritmo propuesto, algoritmo genético y colonia de hormigas.

## Estado real del proyecto

- Incluidas las **24 instancias originales**, sin modificaciones.
- Listos: lector común, validador de rutas, inventario CSV y pruebas.
- **Todavía no se incluyen ejecuciones ni resultados de los cuatro métodos.**
- En la etapa 1, el anexo llamado «Código del algoritmo» contiene un **genético
  con Split**. La etapa 2 desarrolla ese genético y ACO. Ninguna de las dos
  identifica un tercer algoritmo distinto. El equipo debe aclarar qué método
  corresponde al «algoritmo propuesto» antes de implementar esa parte.
- Alternativa para discutir: ahorros de Clarke–Wright + mejora 2-opt. Es una
  propuesta nueva, no un método que se haya identificado en las etapas previas.

## Estructura

| Carpeta | Contenido |
|---|---|
| `instancias/` | 14 CMT y 10 X en formato `.vrp` |
| `comun/` | Lectura y validación compartidas |
| `algoritmos/propuesto/` | Parte de Vanessa, pendiente de aclarar el método |
| `algoritmos/genetico/` | Integrar implementación y estudio de 12 configuraciones |
| `algoritmos/aco/` | Integrar código y resultados existentes del equipo |
| `algoritmos/modelo/` | Modelo, parámetros del solver y estados |
| `resultados/` | Inventario y formato CSV común |
| `graficas/` | Figuras que generen las ejecuciones |
| `reporte/` | Notas para integrar al documento LaTeX |
| `tests/` | Verificación de lectura, distancias y restricciones |

## Ejecutar la base

Python 3.10 o posterior. Estos módulos solo usan la biblioteca estándar.
Desde la raíz del proyecto:

```bash
python -m comun.instancias
python -m unittest discover -s tests -v
```

El primer comando regenera `resultados/inventario_instancias.csv`; no resuelve
el CVRP. El segundo verifica las 24 lecturas y el comportamiento del validador.

## Acuerdos para comparar métodos

1. Objetivo: suma de distancias, incluyendo salida y regreso al depósito.
2. Cada cliente se visita exactamente una vez; no se divide su demanda.
3. Capacidad por ruta y, cuando existe `DISTANCE`, duración por ruta:
   distancia + `SERVICE_TIME` × número de clientes. Se asume velocidad unitaria
   y servicio cero en el depósito; todos deben usar la misma interpretación.
4. Convención de benchmark propuesta: CMT, distancia euclidiana real;
   X, distancia redondeada por arco con `floor(d+0.5)`. Confirmar que coincide
   con las ejecuciones ya realizadas; no redondear solo el total al final.
5. Ninguno de los 24 archivos declara flota máxima. Se conserva el sufijo
   `k` de X como referencia del nombre. **El equipo debe acordar si impone una
   flota máxima o exacta adicional.** `validar(..., max_vehiculos=k)` permite
   comprobar un máximo explícito; el lector no lo impone por su cuenta.
6. Tres corridas independientes por configuración estocástica; guardar semillas.
   Un método determinista no necesita semillas: las repeticiones sirven para
   medir tiempo, no para presentar diversidad artificial en soluciones.
7. Medir tiempo de algoritmo con `time.perf_counter()`, dejando lectura y gráficos
   fuera. Registrar máquina, versión de Python y versiones de dependencias.
8. No comparar «una iteración» como trabajo equivalente: ACO usa 8 hormigas por
   iteración según el equipo; una generación del GA procesa una población.
   Reportar también evaluaciones si están disponibles.
9. No promediar soluciones inválidas o ausentes como si fueran factibles.

## Usar el validador

Las rutas contienen solo clientes, sin el depósito al principio o al final:

```python
from comun.instancias import leer, validar
instancia = leer("instancias/CMT1.vrp")
# rutas = salida de tu algoritmo: [[cliente1, cliente2, ...], ...]
# comprobacion = validar(instancia, rutas, max_vehiculos=None)
# assert comprobacion["factible"], comprobacion["errores"]
```

Guardar las rutas completas en JSON para verificar resultados después.

## CSV y GAP

Usar las columnas de `resultados/formato_corridas.csv`. La fila de encabezados
es una plantilla vacía; no contiene resultados. `iteraciones` es el total
ejecutado, y `iteracion_mejor` indica cuándo se obtuvo la mejor solución.
`factible` solo debe ser verdadero tras validar la solución completa.

Si el modelo demuestra optimalidad y usa idénticas restricciones y distancias:

`GAP_optimo_pct = 100 * (Z_metodo - Z_optimo) / Z_optimo`.

Si solo hay solución factible del solver, la diferencia relativa con ella es
una comparación con incumbente, no un GAP al óptimo. Si se dispone de cota
inferior válida, reportar por separado la brecha respecto a esa cota.
Los números en `COMMENT` de CMT se conservan como comentarios del archivo;
no se han certificado aquí como óptimos actuales. No generar GAP con ellos
sin verificar procedencia y convención.

## Qué debe aportar cada integrante

- Código, instrucciones de ejecución y dependencias.
- CSV por corrida, rutas JSON y resumen de promedios/desviaciones.
- Configuración, criterio de paro y definición de iteración/evaluación.
- En el modelo: estado, incumbente, cota, límite de tiempo y solver.
- En GA: 2 cruces × 3 probabilidades de mutación × 2 métodos de selección
  = 12 configuraciones por instancia; con 3 corridas, 864 ejecuciones.
- En ACO: aclarar con el profesor el bloque de tres factores sin nombres.
  No asumir cuáles eran los hiperparámetros omitidos.

ACO existente: 8 hormigas, hasta 30 iteraciones o 12 consecutivas sin mejorar.
Eso describe lo comunicado por el equipo, no una ejecución verificada aquí.

## Compartir por GitHub

Crear un repositorio privado con README y compartir el enlace para subir esta
base. Invitar al equipo en Settings → Collaborators. Cada persona integra su
método en una rama y propone cambios con un pull request. No sobrescribir
resultados de otra persona; indicar configuración y corrida en los nombres.

No subir credenciales, tokens, entornos virtuales ni ejecutables generados.
Los documentos anteriores contienen nombres y matrículas: no se incluyen en
esta base para compartir. Las instancias se usan para la actividad académica;
no se les atribuye una licencia nueva.
