from decimal import Decimal

import pytest

from facturacion.config import Configuracion
from facturacion.errores import FacturaInvalida
from facturacion.modelos import Cliente, LineaFactura, Producto
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.emision import DESCUENTO_FRECUENTE, ServicioEmision
from facturacion.servicios.fidelizacion import (
    ID_CONSUMIDOR_FINAL,
    UMBRAL_CLIENTE_FRECUENTE,
    ProgramaPuntos,
)


class GeneradorFoliosFake:
    def __init__(self) -> None:
        self._siguiente = 1

    def siguiente(self) -> int:
        folio = self._siguiente
        self._siguiente += 1
        return folio


class InventarioFake:
    def __init__(self) -> None:
        self.reservas = []

    def reservar(self, lineas) -> None:
        self.reservas.append(list(lineas))


@pytest.fixture()
def auditoria() -> RegistroAuditoria:
    return RegistroAuditoria()


@pytest.fixture()
def programa_puntos(auditoria: RegistroAuditoria) -> ProgramaPuntos:
    return ProgramaPuntos(auditoria)


@pytest.fixture()
def cliente_frecuente() -> Cliente:
    return Cliente(id="cliente-frecuente", nombre="Cliente Frecuente", nit="900123456")


@pytest.fixture()
def cliente_no_frecuente() -> Cliente:
    return Cliente(id="cliente-normal", nombre="Cliente Normal", nit="900123457")


@pytest.fixture()
def producto() -> Producto:
    return Producto(codigo="P001", descripcion="Producto 1", precio_unitario=Decimal("1000"))


@pytest.fixture()
def linea(producto: Producto) -> LineaFactura:
    return LineaFactura(producto=producto, cantidad=1)


@pytest.fixture()
def servicio_emision(programa_puntos: ProgramaPuntos, auditoria: RegistroAuditoria) -> ServicioEmision:
    return ServicioEmision(
        RepositorioFacturas(),
        GeneradorFoliosFake(),
        InventarioFake(),
        auditoria,
        Configuracion(),
        programa_puntos,
    )


def test_programa_puntos_es_frecuente_por_umbral_y_excluye_consumidor_final(programa_puntos: ProgramaPuntos) -> None:
    programa_puntos._saldos["casi"] = UMBRAL_CLIENTE_FRECUENTE - 1
    programa_puntos._saldos["justo"] = UMBRAL_CLIENTE_FRECUENTE
    programa_puntos._saldos[ID_CONSUMIDOR_FINAL] = 9999

    assert programa_puntos.es_frecuente("casi") is False
    assert programa_puntos.es_frecuente("justo") is True
    assert programa_puntos.es_frecuente(ID_CONSUMIDOR_FINAL) is False


def test_crear_borrador_aplica_descuento_por_linea_a_cliente_frecuente(servicio_emision: ServicioEmision, programa_puntos: ProgramaPuntos, cliente_frecuente: Cliente, linea: LineaFactura) -> None:
    programa_puntos._saldos[cliente_frecuente.id] = UMBRAL_CLIENTE_FRECUENTE

    factura = servicio_emision.crear_borrador(cliente_frecuente, [linea])

    assert factura.lineas[0].descuento == Decimal("50.00")
    assert factura.descuentos == Decimal("50.00")
    assert factura.subtotal == Decimal("1000.00")
    assert factura.impuestos == Decimal("180.50")
    assert factura.total == Decimal("1130.50")
    assert factura.lineas[0].producto.codigo == "P001"


def test_crear_borrador_sin_descuento_para_cliente_no_frecuente(servicio_emision: ServicioEmision, cliente_no_frecuente: Cliente, linea: LineaFactura) -> None:
    factura = servicio_emision.crear_borrador(cliente_no_frecuente, [linea])

    assert factura.lineas[0].descuento == Decimal("0")
    assert factura.descuentos == Decimal("0")
    assert factura.subtotal == Decimal("1000.00")
    assert factura.impuestos == Decimal("190.00")
    assert factura.total == Decimal("1190.00")


def test_crear_borrador_rechaza_cantidad_invalida(servicio_emision: ServicioEmision, cliente_no_frecuente: Cliente, producto: Producto) -> None:
    with pytest.raises(FacturaInvalida):
        servicio_emision.crear_borrador(cliente_no_frecuente, [LineaFactura(producto=producto, cantidad=0)])
