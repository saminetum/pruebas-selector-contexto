from decimal import Decimal

import pytest

from facturacion.config import Configuracion
from facturacion.modelos import Cliente, LineaFactura, Producto
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.emision import ServicioEmision
from facturacion.servicios.fidelizacion import ProgramaPuntos


class RepositorioFacturasFalso:
    def guardar_factura(self, factura):
        self.ultima_factura = factura


class GeneradorFoliosFalso:
    def __init__(self):
        self._siguiente = 1

    def siguiente(self):
        folio = self._siguiente
        self._siguiente += 1
        return folio


class InventarioFalso:
    def reservar(self, lineas):
        self.ultimas_lineas = list(lineas)


class ProgramaPuntosFalso:
    def __init__(self, frecuente=True):
        self.frecuente = frecuente

    def es_frecuente(self, cliente_id: str) -> bool:
        return self.frecuente


def test_C1_crear_borrador_aplica_descuento_del_5_por_ciento_a_cliente_frecuente():
    servicio = ServicioEmision(
        facturas=RepositorioFacturasFalso(),
        folios=GeneradorFoliosFalso(),
        inventario=InventarioFalso(),
        auditoria=RegistroAuditoria(),
        config=Configuracion(),
        programa_puntos=ProgramaPuntosFalso(frecuente=True),
    )
    cliente = Cliente(id="cli-1", nombre="Cliente frecuente", nit="900123456")
    linea = LineaFactura(
        Producto("P1", "Producto", Decimal("100.00"), Decimal("0.19")),
        2,
    )

    factura = servicio.crear_borrador(cliente, [linea])

    assert factura.lineas[0].descuento == Decimal("10.00")
    assert factura.subtotal == Decimal("200.00")
    assert factura.descuentos == Decimal("10.00")
    assert factura.total == Decimal("226.10")


def test_C2_programa_puntos_reconoce_frecuencia_desde_500_puntos_y_excluye_consumidor_final():
    programa = ProgramaPuntos(RegistroAuditoria())

    programa.saldo = lambda cliente_id: 499
    assert programa.es_frecuente("cli-1") is False

    programa.saldo = lambda cliente_id: 500
    assert programa.es_frecuente("cli-1") is True

    programa.saldo = lambda cliente_id: 1000
    assert programa.es_frecuente("consumidor-final") is False


def test_C3_la_factura_emitida_muestra_descuentos_en_sus_datos_visibles():
    servicio = ServicioEmision(
        facturas=RepositorioFacturasFalso(),
        folios=GeneradorFoliosFalso(),
        inventario=InventarioFalso(),
        auditoria=RegistroAuditoria(),
        config=Configuracion(),
        programa_puntos=ProgramaPuntosFalso(frecuente=True),
    )
    cliente = Cliente(id="cli-1", nombre="Cliente frecuente", nit="900123456")
    lineas = [
        LineaFactura(Producto("P1", "Producto A", Decimal("50.00"), Decimal("0.19")), 1),
        LineaFactura(Producto("P2", "Producto B", Decimal("150.00"), Decimal("0.19")), 1),
    ]

    factura = servicio.crear_borrador(cliente, lineas)

    assert any(linea.descuento > 0 for linea in factura.lineas)
    assert factura.descuentos == sum((linea.descuento for linea in factura.lineas), Decimal("0"))
    assert factura.descuentos != Decimal("0")
