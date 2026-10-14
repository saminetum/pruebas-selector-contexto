from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from facturacion.modelos import Cliente, EstadoFactura, Factura, MedioPago, Pago
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.reportes import cierre_de_caja


@pytest.fixture
def cliente() -> Cliente:
    return Cliente(id="cli-1", nombre="Cliente prueba", nit="900123456")


@pytest.fixture
def hoy() -> date:
    return date(2026, 10, 14)


@pytest.fixture
def ayer() -> date:
    return date(2026, 10, 13)


@pytest.fixture
def manana() -> date:
    return date(2026, 10, 15)


def _factura_emitida(
    cliente: Cliente,
    *,
    serie: str = "FV",
    folio: int = 1,
    fecha_emision: datetime,
    estado: EstadoFactura = EstadoFactura.PAGADA,
    pagos: list[Pago] | None = None,
) -> Factura:
    factura = Factura(serie=serie, cliente=cliente, folio=folio)
    factura.estado = estado
    factura.fecha_emision = fecha_emision
    factura.total = Decimal("100.00")
    factura.subtotal = Decimal("84.03")
    factura.impuestos = Decimal("15.97")
    factura.pagos = list(pagos or [])
    return factura


def test_C1_suma_pagos_por_fecha_de_pago_y_no_por_fecha_de_emision(cliente, hoy, ayer):
    repo = RepositorioFacturas()
    pago_hoy = Pago(medio=MedioPago.EFECTIVO, monto=Decimal("50.00"), fecha=datetime(2026, 10, 14, 9, 30))
    factura_ayer = _factura_emitida(
        cliente,
        folio=10,
        fecha_emision=datetime(2026, 10, 13, 18, 0),
        pagos=[pago_hoy],
    )
    repo.guardar_factura(factura_ayer)

    cierre_hoy = cierre_de_caja(repo, hoy)
    cierre_ayer = cierre_de_caja(repo, ayer)

    assert cierre_hoy["efectivo"] == Decimal("50.00")
    assert cierre_ayer["efectivo"] == Decimal("0.00")


def test_C2_no_incluye_un_pago_de_otro_dia_ni_siendo_factura_del_dia(cliente, hoy, manana):
    repo = RepositorioFacturas()
    pago_manana = Pago(
        medio=MedioPago.TARJETA,
        monto=Decimal("75.25"),
        fecha=datetime(2026, 10, 15, 10, 0),
    )
    factura_hoy = _factura_emitida(
        cliente,
        folio=11,
        fecha_emision=datetime(2026, 10, 14, 12, 0),
        pagos=[pago_manana],
    )
    repo.guardar_factura(factura_hoy)

    cierre_hoy = cierre_de_caja(repo, hoy)

    assert cierre_hoy["tarjeta"] == Decimal("0.00")
    assert cierre_hoy["efectivo"] == Decimal("0.00")
    assert cierre_hoy["transferencia"] == Decimal("0.00")


def test_C3_excluye_facturas_anuladas_aunque_tengan_pagos_del_dia(cliente, hoy):
    repo = RepositorioFacturas()
    pago_hoy = Pago(
        medio=MedioPago.TRANSFERENCIA,
        monto=Decimal("120.00"),
        fecha=datetime(2026, 10, 14, 8, 15),
    )
    factura_anulada = _factura_emitida(
        cliente,
        folio=12,
        fecha_emision=datetime(2026, 10, 14, 8, 0),
        estado=EstadoFactura.ANULADA,
        pagos=[pago_hoy],
    )
    repo.guardar_factura(factura_anulada)

    cierre = cierre_de_caja(repo, hoy)

    assert cierre["transferencia"] == Decimal("0.00")
    assert cierre["efectivo"] == Decimal("0.00")
    assert cierre["tarjeta"] == Decimal("0.00")


def test_C4_mantiene_el_desglose_por_medio_de_pago(cliente, hoy):
    repo = RepositorioFacturas()
    repo.guardar_factura(
        _factura_emitida(
            cliente,
            folio=13,
            fecha_emision=datetime(2026, 10, 14, 9, 0),
            pagos=[Pago(MedioPago.EFECTIVO, Decimal("10.00"), datetime(2026, 10, 14, 9, 5))],
        )
    )
    repo.guardar_factura(
        _factura_emitida(
            cliente,
            folio=14,
            fecha_emision=datetime(2026, 10, 14, 10, 0),
            pagos=[Pago(MedioPago.TARJETA, Decimal("20.00"), datetime(2026, 10, 14, 10, 10))],
        )
    )
    repo.guardar_factura(
        _factura_emitida(
            cliente,
            folio=15,
            fecha_emision=datetime(2026, 10, 14, 11, 0),
            pagos=[Pago(MedioPago.TRANSFERENCIA, Decimal("30.00"), datetime(2026, 10, 14, 11, 15))],
        )
    )

    cierre = cierre_de_caja(repo, hoy)

    assert cierre["efectivo"] == Decimal("10.00")
    assert cierre["tarjeta"] == Decimal("20.00")
    assert cierre["transferencia"] == Decimal("30.00")
