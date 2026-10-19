from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from facturacion.errores import FacturaInvalida
from facturacion.modelos import Cliente, Factura, LineaFactura, NotaCredito, Producto
from facturacion.servicios.devoluciones import ItemDevuelto, ServicioDevoluciones


class RepositorioFacturasFake:
    def __init__(self, factura: Factura) -> None:
        self.factura = factura

    def obtener_factura(self, identificador: str) -> Factura:
        assert identificador == self.factura.identificador
        return self.factura


class InventarioFake:
    def __init__(self) -> None:
        self.liberaciones: list[list[LineaFactura]] = []

    def liberar(self, lineas: list[LineaFactura]) -> None:
        self.liberaciones.append(list(lineas))


class NotasCreditoFake:
    def __init__(self) -> None:
        self.emisiones: list[tuple[Factura, Decimal, str]] = []

    def emitir(self, factura: Factura, monto: Decimal, motivo: str) -> NotaCredito:
        self.emisiones.append((factura, monto, motivo))
        return NotaCredito(
            serie="NC",
            folio=len(self.emisiones),
            factura_origen=factura.identificador,
            monto=monto,
            motivo=motivo,
            fecha=factura.fecha_emision,
        )


class AuditoriaFake:
    def __init__(self) -> None:
        self.eventos: list[tuple[str, dict[str, object]]] = []

    def registrar(self, tipo: str, **datos: object) -> None:
        self.eventos.append((tipo, datos))


@pytest.fixture
def factura_con_cafe() -> Factura:
    cliente = Cliente(id="cli-1", nombre="Cliente prueba", nit="900000001")
    producto = Producto(codigo="CAFE", descripcion="Cafe", precio_unitario=Decimal("1000"))
    factura = Factura(serie="FV", cliente=cliente, lineas=[LineaFactura(producto, 3)])
    factura.folio = 10
    return factura


def test_C1_C3_devolucion_con_producto_repetido_suma_las_unidades_antes_de_validar_y_emite_una_sola_nota_credito_con_el_total_correcto(factura_con_cafe: Factura) -> None:
    facturas = RepositorioFacturasFake(factura_con_cafe)
    inventario = InventarioFake()
    notas_credito = NotasCreditoFake()
    auditoria = AuditoriaFake()
    servicio = ServicioDevoluciones(facturas, inventario, notas_credito, auditoria)

    nota = servicio.devolver(
        factura_con_cafe.identificador,
        [ItemDevuelto("CAFE", 2), ItemDevuelto("CAFE", 1)],
        "cliente devuelve parte del pedido",
    )

    assert nota.monto == Decimal("3570.00")
    assert nota.factura_origen == factura_con_cafe.identificador
    assert len(notas_credito.emisiones) == 1
    assert len(inventario.liberaciones) == 1
    assert [item.cantidad for item in inventario.liberaciones[0]] == [2, 1]


def test_C1_C2_devolucion_con_producto_repetido_que_supera_lo_vendido_se_rechaza_completa_sin_emitir_nota_credito_ni_reingresar_inventario(factura_con_cafe: Factura) -> None:
    facturas = RepositorioFacturasFake(factura_con_cafe)
    inventario = InventarioFake()
    notas_credito = NotasCreditoFake()
    auditoria = AuditoriaFake()
    servicio = ServicioDevoluciones(facturas, inventario, notas_credito, auditoria)

    with pytest.raises(FacturaInvalida):
        servicio.devolver(
            factura_con_cafe.identificador,
            [ItemDevuelto("CAFE", 2), ItemDevuelto("CAFE", 2)],
            "exceso de devolucion",
        )

    assert notas_credito.emisiones == []
    assert inventario.liberaciones == []
    assert auditoria.eventos == []
