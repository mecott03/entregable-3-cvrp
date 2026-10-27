"""Adaptación del GA con Split presentado en el Entregable 1.

Conserva inicialización aleatoria, OX de llenado lineal, torneo k=3,
mutación swap/inversión equiprobable y elitismo. No añade búsqueda local.
Split verifica capacidad y duración. No limita flota si no se especifica.
"""
from dataclasses import asdict, dataclass
import math
import random
from time import perf_counter


@dataclass(frozen=True)
class Config:
    poblacion: int = 60
    generaciones: int = 150
    prob_cruce: float = 0.9
    prob_mutacion: float = 0.25
    elite: int = 2
    torneo: int = 3
    max_vehiculos: int | None = None


class Decodificador:
    def __init__(self, instancia, max_vehiculos=None):
        self.ins = instancia
        self.max_vehiculos = max_vehiculos
        self.ids = sorted(instancia.coordenadas)
        self.indices = {node: i for i, node in enumerate(self.ids)}
        self.depot = self.indices[instancia.deposito]
        self.clientes = [self.indices[i] for i in self.ids if i != instancia.deposito]
        self.q = [instancia.demandas[i] for i in self.ids]
        self.d = [[instancia.distancias[a, b] for b in self.ids] for a in self.ids]
        self.a_depot = self.d[self.depot]

    def split(self, perm, reconstruir=False):
        """Camino mínimo en DAG sobre posiciones del tour gigante.

        Un arco i -> j representa una ruta de clientes consecutivos [i:j].
        Si se especifica flota, usa un estado extra: número de rutas usadas.
        Costo incremental O(1) por tramo en lugar de sumar cada ruta de cero.
        """
        n = len(perm)
        d, q, depot, Q = self.d, self.q, self.a_depot, self.ins.capacidad
        limite = self.ins.duracion_maxima
        servicio = self.ins.servicio
        if self.max_vehiculos is not None:
            return self._split_flota(perm, reconstruir)
        valores = [0.0] + [math.inf] * n
        prev = [-1] * (n + 1)
        for i in range(n):
            if not math.isfinite(valores[i]):
                continue
            carga = interno = 0.0
            inicio = depot[perm[i]]
            base = valores[i]
            for j in range(i, n):
                cliente = perm[j]
                carga += q[cliente]
                if carga > Q + 1e-8:
                    break
                if j > i:
                    interno += d[perm[j-1]][cliente]
                costo = inicio + interno + depot[cliente]
                if limite is not None and costo + servicio*(j-i+1) > limite + 1e-8:
                    # No hacer break: con distancias redondeadas puede fallar
                    # desigualdad triangular; conservar exactitud del Split.
                    continue
                candidato = base + costo
                if candidato < valores[j+1]:
                    valores[j+1], prev[j+1] = candidato, i
        if not reconstruir:
            return valores[n]
        if not math.isfinite(valores[n]):
            return valores[n], []
        rutas, j = [], n
        while j:
            i = prev[j]
            rutas.append([self.ids[v] for v in perm[i:j]])
            j = i
        return valores[n], rutas[::-1]

    def _split_flota(self, perm, reconstruir):
        """Mejor partición del tour en a lo sumo K rutas; no garantiza
        que cualquier permutación admita una partición factible con ese K.
        """
        n, K = len(perm), self.max_vehiculos
        arcos = [[] for _ in range(n)]
        for i in range(n):
            carga = interno = 0.0
            for j in range(i, n):
                c = perm[j]
                carga += self.q[c]
                if carga > self.ins.capacidad + 1e-8:
                    break
                if j > i:
                    interno += self.d[perm[j-1]][c]
                costo = self.a_depot[perm[i]] + interno + self.a_depot[c]
                if (self.ins.duracion_maxima is None or
                    costo + self.ins.servicio*(j-i+1) <= self.ins.duracion_maxima + 1e-8):
                    arcos[i].append((j+1, costo))
        V = [[math.inf]*(n+1) for _ in range(K+1)]
        P = [[-1]*(n+1) for _ in range(K+1)]
        V[0][0] = 0.0
        for k in range(1, K+1):
            for i in range(n):
                if not math.isfinite(V[k-1][i]):
                    continue
                for j, costo in arcos[i]:
                    cand = V[k-1][i] + costo
                    if cand < V[k][j]:
                        V[k][j], P[k][j] = cand, i
        k = min(range(1, K+1), key=lambda k: V[k][n])
        z = V[k][n]
        if not reconstruir:
            return z
        if not math.isfinite(z):
            return z, []
        rutas, j = [], n
        while j:
            i = P[k][j]
            rutas.append([self.ids[v] for v in perm[i:j]])
            j, k = i, k-1
        return z, rutas[::-1]


def ox(p1, p2, rng):
    """Variante exacta de los anexos: copia segmento inclusivo y llena
    huecos de izquierda a derecha según orden lineal del segundo padre.
    No se afirma que sea la variante OX circular de otros autores.
    """
    if len(p1) < 2:
        return p1[:]
    a, b = sorted(rng.sample(range(len(p1)), 2))
    hijo = [None] * len(p1)
    hijo[a:b+1] = p1[a:b+1]
    segmento = set(p1[a:b+1])
    faltantes = iter(g for g in p2 if g not in segmento)
    return [next(faltantes) if g is None else g for g in hijo]


def mutar(perm, rng):
    hijo = perm[:]
    if len(hijo) < 2:
        return hijo
    # Conservar orden de consumo aleatorio del código anterior.
    if rng.random() < 0.5:
        i, j = rng.sample(range(len(hijo)), 2)
        hijo[i], hijo[j] = hijo[j], hijo[i]
    else:
        i, j = sorted(rng.sample(range(len(hijo)), 2))
        hijo[i:j+1] = hijo[i:j+1][::-1]
    return hijo


def resolver(instancia, semilla, config=Config()):
    if not (config.poblacion >= config.torneo >= 1 and
            1 <= config.elite < config.poblacion and config.generaciones >= 0):
        raise ValueError("Población, torneo, elitismo o generaciones inválidos")
    if not (0 <= config.prob_cruce <= 1 and 0 <= config.prob_mutacion <= 1):
        raise ValueError("Probabilidades fuera de [0,1]")
    if config.max_vehiculos is not None and config.max_vehiculos < 1:
        raise ValueError("Flota máxima debe ser positiva")
    # Leer datos, construir matrices y validar resultados quedan fuera del
    # cronómetro. Se incluye inicialización de población y Split final.
    dec = Decodificador(instancia, config.max_vehiculos)
    rng = random.Random(semilla)
    t0 = perf_counter()
    poblacion = [rng.sample(dec.clientes, len(dec.clientes)) for _ in range(config.poblacion)]
    fitness = [dec.split(p) for p in poblacion]
    mejor = min(fitness)
    historia = [mejor]
    primera_mejor = 0
    for generacion in range(1, config.generaciones+1):
        indices = sorted(range(config.poblacion), key=lambda i: fitness[i])
        nueva = [poblacion[i][:] for i in indices[:config.elite]]
        while len(nueva) < config.poblacion:
            def elegir():
                return min(rng.sample(range(config.poblacion), config.torneo),
                           key=lambda i: fitness[i])
            p1, p2 = poblacion[elegir()], poblacion[elegir()]
            h = ox(p1, p2, rng) if rng.random() < config.prob_cruce else p1[:]
            if rng.random() < config.prob_mutacion:
                h = mutar(h, rng)
            nueva.append(h)
        poblacion = nueva
        # Reevaluar incluso élites: conserva la contabilidad de la etapa 1.
        fitness = [dec.split(p) for p in poblacion]
        actual = min(fitness)
        if actual < mejor - 1e-8:
            primera_mejor = generacion
        mejor = min(mejor, actual)
        historia.append(mejor)
    indice = min(range(config.poblacion), key=lambda i: fitness[i])
    z, rutas = dec.split(poblacion[indice], reconstruir=True)
    tiempo = perf_counter() - t0
    return dict(distancia=z if math.isfinite(z) else None, rutas=rutas,
                tiempo_s=tiempo, iteraciones=config.generaciones,
                iteracion_mejor=primera_mejor,
                evaluaciones=config.poblacion*(config.generaciones+1),
                # La reconstrucción final se informa aparte: no es un candidato nuevo.
                reconstrucciones_finales=1,
                historia=[v if math.isfinite(v) else None for v in historia],
                semilla=semilla, parametros=asdict(config))
