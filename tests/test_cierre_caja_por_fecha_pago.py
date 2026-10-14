from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from facturacion.modelos import Cliente, EstadoFactura, Factura, LineaFactura, MedioPago, Pago, Producto
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.reportes import cierre_de_caja


def _factura(
    folio: int,
    fecha_emision: datetime,
    pagos: list[Pago],
    estado: EstadoFactura = EstadoFactura.PAGADA,
) -> Factura:
    producto = Producto("A1", "Producto A1", Decimal("100.00"))
    cliente = Cliente(f"c{folio}", f"Cliente {folio}", f"90000000{folio}")
    factura = Factura(
        serie="FV",
        cliente=cliente,
        lineas=[LineaFactura(producto, 1)],
        folio=folio,
        estado=estado,
        fecha_emision=fecha_emision,
        pagos=pagos,
    )
    factura.subtotal = Decimal("100.00")
    factura.impuestos = Decimal("19.00")
    factura.total = Decimal("119.00")
    return factura


def test_cierre_de_caja_suma_por_fecha_real_del_pago_y_desglosa_por_medio() -> None:
    hoy = date(2026, 10, 14)
    ayer = hoy - timedelta(days=1)
    manana = hoy + timedelta(days=1)

    repo = RepositorioFacturas()
    repo.guardar_factura(
        _factura(
            1,
            datetime.combine(ayer, datetime.min.time()),
            [Pago(MedioPago.EFECTIVO, Decimal("10.00"), datetime.combine(hoy, datetime.min.time()))],
        )
    )
    repo.guardar_factura(
        _factura(
            2,
            datetime.combine(hoy, datetime.min.time()),
            [Pago(MedioPago.TARJETA, Decimal("20.00"), datetime.combine(manana, datetime.min.time()))],
        )
    )
    repo.guardar_factura(
        _factura(
            3,
            datetime.combine(hoy, datetime.min.time()),
            [Pago(MedioPago.TRANSFERENCIA, Decimal("30.00"), datetime.combine(hoy, datetime.min.time()))],
            estado=EstadoFactura.ANULADA,
        )
    )

    cierre_hoy = cierre_de_caja(repo, hoy)
    cierre_ayer = cierre_de_caja(repo, ayer)

    assert cierre_hoy == {
        "efectivo": Decimal("10.00"),
        "tarjeta": Decimal("0.00"),
        "transferencia": Decimal("0.00"),
    }
    assert cierre_ayer == {
        "efectivo": Decimal("0.00"),
        "tarjeta": Decimal("0.00"),
        "transferencia": Decimal("0.00"),
    }


def test_cierre_de_caja_con_repositorio_vacio_devuelve_ceros() -> None:
    cierre = cierre_de_caja(RepositorioFacturas(), date(2026, 10, 14))

    assert cierre == {
        "efectivo": Decimal("0.00"),
        "tarjeta": Decimal("0.00"),
        "transferencia": Decimal("0.00"),
    }


def test_cierre_de_caja_propagada_la_falla_del_repositorio() -> None:
    class RepositorioQueFalla:
        def listar(self) -> list[Factura]:
            raise RuntimeError("fallo de almacenamiento")

    with pytest.raises(RuntimeError, match="fallo de almacenamiento"):
        cierre_de_caja(RepositorioQueFalla(), date(2026, 10, 14))
