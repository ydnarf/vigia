import unittest

from vigia import regime
from vigia.demo import series_demo


class TestVotos(unittest.TestCase):
    def test_vix_estres_vota_risk_off(self):
        voto = regime.votar_vix([("2026-07-01", 27.3)])
        self.assertEqual(voto.voto, -1)

    def test_vix_calma_vota_risk_on(self):
        voto = regime.votar_vix([("2026-07-01", 12.8)])
        self.assertEqual(voto.voto, 1)

    def test_vix_intermedio_es_neutral(self):
        voto = regime.votar_vix([("2026-07-01", 19.0)])
        self.assertEqual(voto.voto, 0)

    def test_curva_invertida_vota_risk_off(self):
        voto = regime.votar_curva([("2026-07-01", -0.31)])
        self.assertEqual(voto.voto, -1)
        self.assertIn("invertida", voto.detalle)

    def test_credito_ancho_vota_risk_off(self):
        voto = regime.votar_credito([("2026-07-01", 5.4)])
        self.assertEqual(voto.voto, -1)

    def test_tendencia_bajo_media_vota_risk_off(self):
        serie = [("d", 5200.0)] * 49 + [("2026-07-01", 4800.0)]
        voto = regime.votar_tendencia(serie)
        self.assertEqual(voto.voto, -1)

    def test_tendencia_requiere_historia_minima(self):
        with self.assertRaises(ValueError):
            regime.votar_tendencia([("2026-07-01", 5200.0)] * 5)

    def test_serie_vacia_falla_claro(self):
        with self.assertRaises(ValueError):
            regime.votar_vix([])


class TestDetector(unittest.TestCase):
    def test_escenario_risk_off(self):
        regimen = regime.detectar(series_demo("risk-off"))
        self.assertEqual(regimen.nombre, regime.RISK_OFF)
        self.assertLessEqual(regimen.puntaje, -2)

    def test_escenario_risk_on(self):
        regimen = regime.detectar(series_demo("risk-on"))
        self.assertEqual(regimen.nombre, regime.RISK_ON)
        self.assertGreaterEqual(regimen.puntaje, 2)

    def test_escenario_neutral(self):
        regimen = regime.detectar(series_demo("neutral"))
        self.assertEqual(regimen.nombre, regime.NEUTRAL)

    def test_consenso_total_da_confianza_alta(self):
        regimen = regime.detectar(series_demo("risk-on"))
        self.assertEqual(regimen.confianza, "alta")

    def test_fecha_datos_es_la_mas_reciente(self):
        regimen = regime.detectar(series_demo("risk-off"))
        fechas = [v.fecha for v in regimen.votos]
        self.assertEqual(regimen.fecha_datos, max(fechas))


if __name__ == "__main__":
    unittest.main()
