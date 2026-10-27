import math
from pathlib import Path
import unittest
from comun.instancias import leer, validar


class InstanciasTest(unittest.TestCase):
    def test_archivos_y_metricas(self):
        archivos = list(Path("instancias").glob("*.vrp"))
        self.assertEqual(len(archivos), 24)
        for path in archivos:
            ins = leer(path)
            self.assertEqual(ins.demandas[ins.deposito], 0)
            for i in ins.coordenadas:
                self.assertEqual(ins.distancias[i, i], 0)
                for j in ins.coordenadas:
                    d = math.dist(ins.coordenadas[i], ins.coordenadas[j])
                    esperado = math.floor(d + 0.5) if ins.convencion == "entera" else d
                    self.assertEqual(ins.distancias[i, j], esperado)
                    self.assertEqual(ins.distancias[i, j], ins.distancias[j, i])

    def test_cobertura_y_deposito(self):
        ins = leer("instancias/CMT1.vrp")
        rutas = [[i] for i in ins.demandas if i != ins.deposito]
        self.assertTrue(validar(ins, rutas)["factible"])
        self.assertFalse(validar(ins, rutas[:-1])["factible"])
        self.assertFalse(validar(ins, rutas + [rutas[0]])["factible"])
        self.assertFalse(validar(ins, rutas + [[ins.deposito]])["factible"])
        self.assertFalse(validar(ins, rutas + [[99999]])["factible"])

    def test_capacidad_flota_y_duracion(self):
        ins = leer("instancias/CMT6.vrp")
        rutas = [[i] for i in ins.demandas if i != ins.deposito]
        self.assertTrue(validar(ins, rutas)["factible"])
        self.assertFalse(validar(ins, rutas, max_vehiculos=1)["factible"])
        self.assertFalse(validar(ins, [sum(rutas, [])])["factible"])
        i = rutas[0][0]
        self.assertAlmostEqual(ins.duracion_ruta([i]), 2*ins.distancias[ins.deposito, i]+10)
        ins.duracion_maxima = 0
        self.assertTrue(any("duración" in e for e in validar(ins, rutas)["errores"]))


if __name__ == "__main__":
    unittest.main()
