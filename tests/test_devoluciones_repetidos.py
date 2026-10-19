from decimal import Decimal

import pytest

from facturacion.errores import FacturaInvalida
from facturacion.modelos import Cliente, Factura, LineaFactura, Producto
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.devoluciones import ItemDevuelto, ServicioDevoluciones
from facturacion.utilidades.fechas import ahora


class InventarioFalso:
    def __init__(self) -> None:
        self.liberadas = []

    def liberar(self, lineas):
        self.liberadas.append(list(lineas))


class NotasCreditoFalsa:
    def __init__(self) -> None:
        self.llamadas = []
        self._siguiente = 1

    def emitir(self, factura, monto, motivo):
        self.llamadas.append((factura, monto, motivo))
        from facturacion.modelos import NotaCredito

        nota = NotaCredito(
            serie="NC",
            folio=self._siguiente,
            factura_origen=factura.identificador,
            monto=monto,
            motivo=motivo,
            fecha=ahora(),
        )
        self._siguiente += 1
        return nota


def _factura_base(cantidad=3):
    producto = Producto("CAFE", "Cafe", Decimal("10.00"), Decimal("0.19"))
    cliente = Cliente("cli-1", "Cliente", "900123456")
    factura = Factura("FV", cliente, [LineaFactura(producto, cantidad)])
    factura.folio = 1
    factura.fecha_emision = ahora()
    return factura


def _servicio_con_factura(factura):
    repo = RepositorioFacturas()
    repo.guardar_factura(factura)
    inventario = InventarioFalso()
    notas = NotasCreditoFalsa()
    auditoria = RegistroAuditoria()
    return ServicioDevoluciones(repo, inventario, notas, auditoria), inventario, notas


def test_devolucion_con_producto_repetido_suma_unidades_y_emite_una_sola_nota_credito():
    factura = _factura_base(3)
    servicio, inventario, notas = _servicio_con_factura(factura)

    nota = servicio.devolver(
        factura.identificador,
        [ItemDevuelto("CAFE", 2), ItemDevuelto("CAFE", 1)],
        "Producto devuelto",
    )

    assert nota.monto == Decimal("35.70")
    assert len(notas.llamadas) == 1
    assert len(inventario.liberadas) == 1
    assert [item.cantidad for item in inventario.liberadas[0]] == [2, 1]
    assert [item.codigo for item in inventario.liberadas[0]] == ["CAFE", "CAFE"]


def test_devolucion_con_producto_repetido_cuya_suma_supera_lo_vendido_se_rechaza():
    factura = _factura_base(3)
    servicio, inventario, notas = _servicio_con_factura(factura)

    with pytest.raises(FacturaInvalida, match="No se pueden devolver 4 de CAFE"):
        servicio.devolver(
            factura.identificador,
            [ItemDevuelto("CAFE", 2), ItemDevuelto("CAFE", 2)],
            "Producto devuelto",
        )

    assert notas.llamadas == []
    assert inventario.liberadas == []


def test_devolucion_con_cantidad_cero_en_un_item_rechaza_toda_la_operacion():
    factura = _factura_base(3)
    servicio, inventario, notas = _servicio_con_factura(factura)

    with pytest.raises(FacturaInvalida, match="la cantidad debe ser mayor que cero"):
        servicio.devolver(
            factura.identificador,
            [ItemDevuelto("CAFE", 2), ItemDevuelto("CAFE", 0)],
            "Producto devuelto",
        )

    assert notas.llamadas == []
    assert inventario.liberadas == []
