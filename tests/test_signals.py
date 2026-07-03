import unittest

from vigia import regime, signals
from vigia.demo import series_demo


class TestSenal(unittest.TestCase):
    def _senal(self, escenario):
        return signals.generar(regime.detectar(series_demo(escenario)))

    def test_risk_off_apunta_corto(self):
        self.assertEqual(self._senal("risk-off").direccion, "Corto / cobertura")

    def test_risk_on_apunta_largo(self):
        self.assertEqual(self._senal("risk-on").direccion, "Largo")

    def test_neutral_queda_fuera(self):
        self.assertEqual(self._senal("neutral").direccion, "Fuera del mercado")

    def test_neutral_sin_extremos_explica_el_gatillo(self):
        senal = self._senal("neutral")
        self.assertEqual(len(senal.gatillos), 1)
        self.assertIn("zona neutral", senal.gatillos[0])

    def test_formato_incluye_disclaimer_y_regimen(self):
        texto = signals.formatear_senal(self._senal("risk-off"))
        self.assertIn("RISK-OFF", texto)
        self.assertIn(signals.DISCLAIMER, texto)
        self.assertIn("<pre>", texto)

    def test_formato_escapa_html(self):
        texto = signals.formatear_senal(self._senal("risk-off"))
        self.assertIn("S&amp;P 500", texto)

    def test_estado_lista_los_cuatro_indicadores(self):
        regimen = regime.detectar(series_demo("neutral"))
        texto = signals.formatear_estado(regimen)
        for indicador in ("VIX", "10Y–2Y", "HY", "S&amp;P 500"):
            self.assertIn(indicador, texto)


if __name__ == "__main__":
    unittest.main()
