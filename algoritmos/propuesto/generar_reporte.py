"""Crear gráficas, comparación con literatura y sección LaTeX sin ejecutar GA.

Desde raíz: python -m algoritmos.propuesto.generar_reporte
Dependencias de este módulo: numpy y matplotlib. Algoritmo: biblioteca estándar.
"""
import csv
import json
from pathlib import Path
import statistics as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun.instancias import leer, validar
from .ejecutar import guardar_csv


def orden(nombre):
    return (0, int(nombre[3:])) if nombre.startswith("CMT") else (1, nombre)


def main():
    base = Path("resultados/propuesto")
    resumen = list(csv.DictReader((base/"resumen.csv").open()))
    detalle = json.loads((base/"detalle_corridas.json").read_text())
    referencias = {r["instancia"]: r for r in csv.DictReader((base/"referencias_literatura.csv").open())}
    assert len(resumen) == 24 and len(detalle) == 72, "Se requieren las 72 corridas completas"
    assert all(int(r["factibles"]) == 3 for r in resumen)
    resumen.sort(key=lambda r: orden(r["instancia"]))
    for r in detalle:
        ins = leer(Path("instancias")/(r["instancia"]+".vrp"))
        v = validar(ins, r["rutas"])
        assert v["factible"] and abs(v["distancia"]-r["distancia"])<1e-6
        assert len(r["historia"]) == 151
        assert all(x >= y-1e-7 for x, y in zip(r["historia"], r["historia"][1:]))
    comparacion = []
    for r in resumen:
        ref = referencias[r["instancia"]]
        zref = float(ref["valor_referencia"])
        comparacion.append(dict(instancia=r["instancia"], referencia=zref,
                optimo_segun_cvrplib=ref["optimo_segun_cvrplib"],
                vehiculos_referencia=ref["vehiculos_referencia"],
                distancia_media=float(r["distancia_media"]),
                distancia_mejor=float(r["distancia_mejor"]),
                desviacion_media_pct=100*(float(r["distancia_media"])-zref)/zref,
                desviacion_mejor_pct=100*(float(r["distancia_mejor"])-zref)/zref,
                fuente=ref["fuente"], fecha_consulta=ref["fecha_consulta"],
                nota="Diferencia con referencia publicada; no GAP del modelo del equipo"))
    guardar_csv(base/"comparacion_literatura.csv", comparacion)
    filas_rutas = []
    for nombre in sorted({r["instancia"] for r in detalle}, key=orden):
        mejor_caso = min((r for r in detalle if r["instancia"] == nombre), key=lambda r: r["distancia"])
        ins_caso = leer(Path("instancias")/(nombre+".vrp"))
        for numero, ruta in enumerate(mejor_caso["rutas"], 1):
            filas_rutas.append(dict(instancia=nombre, semilla=mejor_caso["semilla"],
                    ruta=numero, nodos="-".join(map(str,[ins_caso.deposito,*ruta,ins_caso.deposito])),
                    clientes=len(ruta), carga=ins_caso.carga_ruta(ruta), capacidad=ins_caso.capacidad,
                    distancia=ins_caso.distancia_ruta(ruta),
                    duracion=ins_caso.duracion_ruta(ruta), duracion_maxima=ins_caso.duracion_maxima))
    guardar_csv(base/"rutas_mejores.csv", filas_rutas)
    figs = Path("graficas/propuesto")
    figs.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                         "axes.spines.top":False, "axes.spines.right":False})
    colores = {"CMT":"#176b87", "X":"#c16c35"}
    fig, ax = plt.subplots(figsize=(9.5,3.5), constrained_layout=True)
    for familia in ["CMT", "X"]:
        H = np.array([r["historia"] for r in detalle if r["instancia"].startswith(familia)])
        relativo = (H/H[:,[0]])*100
        media = relativo.mean(axis=0)
        q25, q75 = np.percentile(relativo,[25,75],axis=0)
        ax.plot(range(151), media, label=f"{familia}: media", color=colores[familia], lw=2)
        ax.fill_between(range(151), q25, q75, color=colores[familia],alpha=.13)
    ax.set(xlabel="Generación (0 = población inicial)", ylabel="Mejor distancia / distancia inicial (%)",
           title="Convergencia relativa por familia")
    ax.grid(alpha=.2); ax.legend()
    fig.savefig(figs/"convergencia.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9.5,3.4), constrained_layout=True)
    for familia in ["CMT","X"]:
        grupo = [r for r in resumen if r["instancia"].startswith(familia)]
        ax.scatter([int(r["clientes"]) for r in grupo], [float(r["tiempo_medio_s"]) for r in grupo],
                   c=colores[familia],label=familia,s=42)
    ax.set(xlabel="Número de clientes", ylabel="Tiempo medio por corrida (s)",
           title="Tiempo observado con 60 individuos y 150 generaciones")
    ax.grid(alpha=.2); ax.legend()
    fig.savefig(figs/"tiempos.png",dpi=180)
    plt.close(fig)
    mejor = min((r for r in detalle if r["instancia"]=="CMT1"),key=lambda r:r["distancia"])
    ins = leer("instancias/CMT1.vrp")
    fig, ax = plt.subplots(figsize=(8.7,4.7),constrained_layout=True)
    for k,ruta in enumerate(mejor["rutas"],1):
        camino = [ins.deposito,*ruta,ins.deposito]
        xy = np.array([ins.coordenadas[i] for i in camino])
        ax.plot(xy[:,0],xy[:,1],"-o",ms=3,lw=1.3,label=f"Ruta {k}: carga {ins.carga_ruta(ruta):g}")
    ax.scatter(*ins.coordenadas[ins.deposito],marker="s",c="#111111",s=70,zorder=10,label="Depósito")
    ax.set(xlabel="Coordenada X",ylabel="Coordenada Y",
           title=f"CMT1: mejor corrida, semilla {mejor['semilla']}, distancia {mejor['distancia']:.2f}")
    ax.legend(fontsize=8,loc="center left",bbox_to_anchor=(1.01,.5)); ax.grid(alpha=.15)
    fig.savefig(figs/"rutas_CMT1.png",dpi=180)
    plt.close(fig)

    tiempos = [r["tiempo_s"] for r in detalle]
    mejoras = [100*(r["historia"][0]-r["distancia"])/r["historia"][0] for r in detalle]
    cv = [100*float(r["distancia_desv_muestral"])/float(r["distancia_media"]) for r in resumen]
    minimo = min(comparacion,key=lambda r:r["desviacion_media_pct"])
    maximo = max(comparacion,key=lambda r:r["desviacion_media_pct"])
    gapc = st.mean(r["desviacion_media_pct"] for r in comparacion if r["instancia"].startswith("CMT"))
    gapx = st.mean(r["desviacion_media_pct"] for r in comparacion if r["instancia"].startswith("X"))
    resultados = "\n".join(
        f"{r['instancia']} & {r['clientes']} & {float(r['distancia_media']):.2f} & "
        f"{float(r['distancia_desv_muestral']):.2f} & {float(r['distancia_mejor']):.2f} & "
        f"{float(r['tiempo_medio_s']):.3f} & {float(r['vehiculos_media']):.2f} & "
        f"{float(r['iteracion_mejor_media']):.1f} \\\\" for r in resumen)
    literatura = "\n".join(
        f"{r['instancia']} & {r['referencia']:.2f} & "
        f"{'Sí' if r['optimo_segun_cvrplib']=='si' else 'No'} & "
        f"{r['desviacion_media_pct']:.2f} & {r['desviacion_mejor_pct']:.2f} \\\\" for r in comparacion)
    texto = r"""\section{Experimentación del algoritmo propuesto: genético con Split}
\subsection{Alcance y continuidad con las etapas anteriores}
Se tomó como algoritmo propuesto el genético con decodificación Split incluido en
el Anexo 3 del Entregable 1 del Equipo 5 \cite{equipo2026}. Esta identificación es un supuesto de
trabajo adoptado para avanzar con la experimentación: no representa un cuarto
método independiente del algoritmo genético. La comparación de cuatro métodos
debe aclarar esta coincidencia al integrar el reporte del equipo.

El cromosoma es una permutación de todos los clientes, llamada tour gigante.
Split encuentra la partición de menor distancia de ese orden en rutas factibles,
siguiendo la idea de decodificación por programación dinámica de Prins
\cite{prins2004}. La optimalidad del Split se limita a los cortes de una
permutación dada; no implica optimalidad global del CVRP. Los genéticos se han
estudiado para este problema \cite{baker2003}, pero esta implementación académica
no reproduce íntegramente esos algoritmos publicados.

\subsection{Configuración y protocolo experimental}
\begin{center}
\begin{tabular}{ll}\toprule
Elemento & Configuración fija de la etapa 1 \\\midrule
Población y generaciones & 60 individuos; 150 generaciones \\
Selección & Torneo de tamaño 3 \\
Cruce & Segmento de dos cortes, llenado lineal por orden \\
Probabilidad de cruce & 0.90 por hijo \\
Probabilidad de mutación & 0.25 por hijo \\
Mutación & Intercambio o inversión, 50\% cada una \\
Elitismo & 2 mejores individuos \\
Inicialización & Permutaciones completamente aleatorias \\
Paro & 150 generaciones, sin paro por estancamiento \\
Corridas & 3 por instancia; semillas 0, 1 y 2 \\\bottomrule
\end{tabular}
\end{center}
Se evaluaron 24 instancias (14 CMT y 10 X), para un total de 72 corridas.
Cada corrida realizó $60(150+1)=9060$ evaluaciones de individuos, incluyendo
la población inicial y la reevaluación de los élites. La reconstrucción final
se contabilizó por separado. Una generación evalúa 60 individuos; no equivale
a una iteración de ACO con 8 hormigas. No se añadió búsqueda local ni inicialización
heurística. El cruce conserva la variante de los anexos anteriores: copia un
segmento inclusivo y llena huecos de izquierda a derecha con el orden del
segundo padre; no se intercambió por otra variante circular de OX.

Las distancias se calcularon como euclidianas reales en CMT y como
$\lfloor d_{ij}+0.5\rfloor$ por arco en X. Se respetaron capacidad y cobertura
exacta. Para las instancias con duración máxima se verificó
$D_r+s|r|\leq L$, suponiendo velocidad unitaria y servicio únicamente en clientes.
El objetivo suma solo distancia, sin sumar servicio. No se impuso un límite
adicional de vehículos: los archivos no lo declaran y el algoritmo original
tampoco lo imponía. El sufijo $k$ de X se conservó como referencia del nombre.
\textbf{Si el equipo fija una flota máxima o exacta, estas corridas deben
repetirse bajo esa regla antes de compararlas.}

\clearpage
\subsection{Resultados en las 24 instancias}
Se obtuvieron soluciones factibles en las 72 corridas. La validación volvió a
calcular distancia, carga, duración y cobertura a partir de las rutas guardadas.
La tabla presenta la media, desviación estándar muestral, mejor distancia,
tiempo medio, vehículos medios y generación media de obtención del mejor valor.

\begin{center}\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrrrrrr}\toprule
Instancia & $n$ & $\bar Z$ & $s_Z$ & $Z_{\min}$ & $\bar t$ (s) & $\bar k$ & $\bar g^*$ \\\midrule
@@RESULTADOS@@
\bottomrule\end{tabular}
\end{center}
\noindent $n$: clientes, sin depósito; $\bar g^*$: generación del último descenso
estricto mayor que $10^{-8}$ en el mejor valor. Todas las corridas terminaron
en la generación 150. $\bar g^*$ no es el número total de generaciones ejecutadas.

El tiempo se midió con \texttt{perf\_counter}, en un proceso secuencial, incluyendo
inicialización de población, evolución y reconstrucción final. Se excluyeron
lectura, preparación de matriz, validación, escritura de archivos y figuras.
El total observado de tiempo de algoritmo fue @@TOTAL@@ s; las corridas
oscilaron entre @@TMIN@@ y @@TMAX@@ s. Estos tiempos corresponden al entorno de
ejecución descrito en \texttt{metadatos.json}; una comparación de velocidad con
otros métodos requiere ejecutarlos en la misma máquina y con igual alcance
del cronómetro.

La reducción media frente al mejor individuo inicial fue de @@MEJORA@@\%,
calculada sobre las 72 corridas. El coeficiente de variación por instancia
osciló entre @@CVMIN@@\% y @@CVMAX@@\%. Con solo tres repeticiones, estas
medidas son descriptivas y no demuestran superioridad estadística.

\clearpage
\subsection{Comparación con referencias de la literatura}
Se consultó la tabla de CVRPLIB \cite{cvrplib}, que reúne casos clásicos CMT y
la familia X de Uchoa y colaboradores \cite{uchoa2017}. Los valores se guardaron
con fuente y fecha de consulta. La diferencia relativa se calculó como:
\[
 \Delta_{\mathrm{ref}}(\%)=100\frac{Z-Z_{\mathrm{ref}}}{Z_{\mathrm{ref}}}.
\]
Se reporta como \emph{diferencia con referencia publicada}; no sustituye el
GAP respecto al modelo matemático del equipo. La columna ``Ópt. pub.'' reproduce
la clasificación de la fuente y no certifica optimalidad de nuestras corridas.
La comparación debe conservar convenciones equivalentes de distancia y flota.

\begin{center}\small
\begin{tabular}{lrrrr}\toprule
Instancia & $Z_{\mathrm{ref}}$ & Ópt. pub. & $\Delta_{\mathrm{media}}$ (\%) & $\Delta_{\mathrm{mejor}}$ (\%) \\\midrule
@@LITERATURA@@
\bottomrule\end{tabular}
\end{center}
La diferencia media no ponderada entre instancias fue de @@GAPC@@\% en CMT y
@@GAPX@@\% en X. La menor diferencia media se observó en @@MININST@@
(@@MINGAP@@\%) y la mayor en @@MAXINST@@ (@@MAXGAP@@\%). Los resultados muestran
que la configuración original produce soluciones factibles, pero su calidad
queda lejos de las referencias en buena parte de estas instancias. Se debe
reportar esta limitación, sin atribuirle al algoritmo un desempeño que no obtuvo.
Como detalle de trazabilidad, el archivo suministrado CMT11 tiene comentario
1042.11; para esta tabla se usó 1042.12, valor consultado en CVRPLIB.

\clearpage
\subsection{Convergencia y tiempo de cómputo}
\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{graficas/propuesto/convergencia.png}
\caption{Mejor distancia normalizada por la mejor distancia inicial de cada
corrida. Líneas: media de 42 corridas CMT y 30 X; bandas: percentiles 25 y 75,
no intervalos de confianza. Menor porcentaje indica mayor reducción relativa.}
\end{figure}
El elitismo conserva los mejores individuos y explica la trayectoria no
creciente del mejor costo. La normalización permite describir avance relativo
sin mezclar distancias absolutas de escalas distintas; no permite comparar
dificultad ni calidad final entre familias por sí sola.
\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{graficas/propuesto/tiempos.png}
\caption{Tiempo medio por instancia con una configuración fija. El número de
clientes no es el único factor: capacidad y duración cambian cuántos tramos
factibles evalúa Split.}
\end{figure}

\clearpage
\subsection{Ejemplo de solución y conclusiones de esta parte}
\begin{figure}[H]\centering
\includegraphics[width=0.98\linewidth]{graficas/propuesto/rutas_CMT1.png}
\caption{Mejor solución observada en CMT1. Cada color es una ruta que sale
y regresa al depósito; las cargas se verificaron contra la capacidad 160.}
\end{figure}
El algoritmo de la etapa 1 pudo adaptarse a las 24 instancias y generó soluciones
factibles en todas las corridas bajo las reglas declaradas. Sin embargo, el buen
resultado previo en un caso de 10 clientes no se trasladó automáticamente a
problemas de entre 50 y 458 clientes. La diferencia con las referencias muestra
que la factibilidad y el bajo tiempo no bastan para concluir que las soluciones
son competitivas.

Una explicación posible es el presupuesto fijo de población y generaciones,
combinado con inicialización aleatoria y ausencia de búsqueda local. Esta es una
interpretación del diseño, no una prueba causal: habría que experimentar con
esas variantes para comprobarla. En esta parte se conservaron los parámetros
anteriores para medir una línea base; no se hizo un estudio de sensibilidad
nuevo y por tanto no se identificaron niveles ``óptimos'' para instancias grandes.

El estudio factorial de cruce, mutación y selección corresponde a la parte del
genético asignada al otro integrante. Esta línea base puede incorporarse a esa
comparación, pero no debe contarse como un algoritmo independiente si ambos
usan el mismo método. La superioridad entre modelo, GA, ACO y otro método
distinto sigue pendiente de integrar los resultados del equipo con reglas iguales.

\clearpage
\subsection{Reproducibilidad e integración con el equipo}
Los resultados individuales se entregan en \texttt{corridas.csv}; el resumen
en \texttt{resumen.csv}; las rutas, semillas, historias y validaciones en
\texttt{detalle\_corridas.json}. Los metadatos incluyen versiones, plataforma,
configuración y huellas SHA-256 de datos y código. Las figuras se generan desde
estos resultados, sin repetir la optimización.

Desde la raíz del repositorio:
\begin{verbatim}
python -m algoritmos.propuesto.ejecutar
python -m algoritmos.propuesto.generar_reporte
python -m unittest discover -s tests -v
\end{verbatim}
El algoritmo requiere Python 3.10 o posterior y solo biblioteca estándar.
Las figuras requieren NumPy y Matplotlib. Con versiones distintas de Python,
los resultados de los operadores aleatorios pueden variar aun con igual semilla.
Los archivos entregados conservan las ejecuciones aquí descritas.

Antes de juntar tablas se deben confirmar la flota permitida, las distancias y
la duración. Si ACO ya se ejecutó con otra convención, no basta con cambiar el
nombre de la columna: es necesario recalcular o repetir la optimización según
el cambio. Para el GAP con el modelo, se requiere su objetivo y estado del solver:
\[
 \operatorname{GAP}_{\mathrm{modelo}}(\%)=
 100\frac{Z_{\mathrm{propuesto}}-Z^*_{\mathrm{modelo}}}{Z^*_{\mathrm{modelo}}},
\]
solo cuando el modelo certifica optimalidad bajo las mismas reglas. Con una
solución factible sin prueba de optimalidad, se reporta diferencia con el
incumbente; con una cota inferior válida se informa una brecha respecto a esa
cota. No se fabricaron objetivos, cotas ni estados del modelo que no se recibieron.

La validación de Split se contrastó con enumeración completa de particiones
de 120 tours pequeños en cuatro regímenes de restricciones (480 comparaciones).
Además se verificaron los operadores, reproducibilidad con semilla, elitismo
y lectura de los 24 archivos. Esto comprueba el comportamiento del código en
esos casos; no demuestra optimalidad global en las instancias experimentales.
"""
    cambios = {"RESULTADOS":resultados,"LITERATURA":literatura,"TOTAL":f"{sum(tiempos):.2f}",
               "TMIN":f"{min(tiempos):.3f}","TMAX":f"{max(tiempos):.3f}",
               "MEJORA":f"{st.mean(mejoras):.2f}","CVMIN":f"{min(cv):.2f}","CVMAX":f"{max(cv):.2f}",
               "GAPC":f"{gapc:.2f}","GAPX":f"{gapx:.2f}","MININST":minimo["instancia"],
               "MAXINST":maximo["instancia"],"MINGAP":f"{minimo['desviacion_media_pct']:.2f}",
               "MAXGAP":f"{maximo['desviacion_media_pct']:.2f}"}
    for clave, valor in cambios.items():
        texto = texto.replace("@@"+clave+"@@",valor)
    reporte = Path("reporte/propuesto")
    reporte.mkdir(parents=True,exist_ok=True)
    (reporte/"seccion_propuesto.tex").write_text(texto,encoding="utf-8")
    maintex = r"""\documentclass[10pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{babel}
\babelprovide[main,import]{spanish}
\usepackage[margin=2cm]{geometry}
\usepackage{lmodern,amsmath,booktabs,graphicx,float,xcolor,hyperref,fancyhdr}
\definecolor{azul}{HTML}{176B87}
\hypersetup{colorlinks=true,urlcolor=azul,citecolor=azul,linkcolor=azul}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small Equipo 5 | Entregable 3}
\fancyhead[R]{\small Algoritmo propuesto}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{14pt}
\begin{document}
{\Large\bfseries\color{azul} Experimentación y resultados}\par
{\large Algoritmo propuesto de la etapa 1}\par
Vanessa Alejandra Mecott Maldonado | Equipo 5\par
\textit{Sección individual para integrar al reporte del equipo.}
\input{reporte/propuesto/seccion_propuesto.tex}
\bibliographystyle{plain}
\bibliography{reporte/propuesto/referencias}
\end{document}
"""
    (reporte/"informe_propuesto.tex").write_text(maintex,encoding="utf-8")
    resumen_md = f"""# Mi parte: algoritmo propuesto de la etapa 1

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
- Tiempo total de algoritmo: {sum(tiempos):.2f} s.
- Reducción media frente al mejor individuo inicial: {st.mean(mejoras):.2f}%.
- Diferencia media no ponderada con referencias CVRPLIB: CMT {gapc:.2f}%; X {gapx:.2f}%.
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
o incluirlo con `\\input{{reporte/propuesto/seccion_propuesto.tex}}`.
Se requieren `amsmath`, `booktabs`, `graphicx`, `float`, `hyperref` y
compatibilidad con español. Agregar las entradas de `referencias.bib` a la
bibliografía del equipo. Los `\\clearpage` pueden retirarse al integrar.

## Repetir

Desde raíz, Python 3.10 o superior:

```bash
python -m algoritmos.propuesto.ejecutar
python -m algoritmos.propuesto.generar_reporte
```

El primer comando sobrescribe solo la carpeta de resultados del propuesto;
usar `--salida resultados/propuesto_nueva` para conservar las corridas entregadas.
No volver a medir tiempos en paralelo con otras optimizaciones.
"""
    (reporte/"LEEME_MI_PARTE.md").write_text(resumen_md,encoding="utf-8")
    print("Validación independiente: 72/72; generadas 3 figuras, CSV de literatura y LaTeX.")
    print(json.dumps(cambios,ensure_ascii=False))


if __name__ == "__main__":
    main()
