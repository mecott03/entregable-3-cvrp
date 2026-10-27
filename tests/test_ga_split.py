"""Split contrastado contra TODAS las particiones de tours pequeños."""
from dataclasses import replace
import itertools
import math
import random
import unittest
from algoritmos.propuesto.ga_split import Config, Decodificador, mutar, ox, resolver
from comun.instancias import Instancia, validar


def pequena():
    coords = {1: (0, 0), 2: (1, 3), 3: (4, 1), 4: (5, 5), 5: (8, 1), 6: (1, 8)}
    dist = {(i, j): math.dist(coords[i], coords[j]) for i in coords for j in coords}
    return Instancia("pequena", coords, {1: 0, 2: 2, 3: 2, 4: 3, 5: 2, 6: 1},
                     5, 1, None, 0, "real", dist, None, "")


def fuerza_bruta_particiones(ins, tour, k=None):
    mejor = math.inf
    for mascara in range(1 << (len(tour)-1)):
        rutas, inicio = [], 0
        for j in range(len(tour)-1):
            if mascara & (1 << j):
                rutas.append(tour[inicio:j+1])
                inicio = j+1
        rutas.append(tour[inicio:])
        check = validar(ins, rutas, k)
        if check["factible"]:
            mejor = min(mejor, check["distancia"])
    return mejor


class SplitTest(unittest.TestCase):
    def test_todos_los_tours_contra_enumeracion(self):
        base = pequena()
        # Capacidad sola, duración/servicio, flota sola y ambas.
        for ins, k in [(base, None), (replace(base, duracion_maxima=23, servicio=1), None),
                       (base, 2), (replace(base, duracion_maxima=23, servicio=1), 2)]:
            dec = Decodificador(ins, k)
            for tour in itertools.permutations([2, 3, 4, 5, 6]):
                perm = [dec.indices[i] for i in tour]
                z, rutas = dec.split(perm, True)
                esperado = fuerza_bruta_particiones(ins, list(tour), k)
                if math.isinf(esperado):
                    self.assertTrue(math.isinf(z))
                    self.assertEqual(rutas, [])
                else:
                    self.assertAlmostEqual(z, esperado)
                    self.assertTrue(validar(ins, rutas, k)["factible"])

    def test_operadores_conservan_permutaciones(self):
        rng = random.Random(123)
        for n in [1, 2, 5, 30]:
            for _ in range(20):
                a, b = rng.sample(range(n), n), rng.sample(range(n), n)
                self.assertEqual(sorted(ox(a, b, rng)), list(range(n)))
                self.assertEqual(sorted(mutar(a, rng)), list(range(n)))

    def test_ga_reproducible_y_elitista(self):
        ins = pequena()
        cfg = Config(poblacion=12, generaciones=10)
        a, b = resolver(ins, 13, cfg), resolver(ins, 13, cfg)
        self.assertEqual(a["historia"], b["historia"])
        self.assertEqual(a["rutas"], b["rutas"])
        self.assertTrue(validar(ins, a["rutas"])["factible"])
        self.assertTrue(all(x >= y-1e-8 for x, y in zip(a["historia"], a["historia"][1:])))
        self.assertEqual(a["evaluaciones"], 12*11)


if __name__ == "__main__":
    unittest.main()
