from decimal import Decimal

import pytest

from facturacion.aplicacion import construir_aplicacion
from facturacion.errores import ErrorCorreo
from facturacion.modelos import Cliente, EstadoFactura, Factura, LineaFactura, MedioPago, Producto


class CorreoFallido:
    def enviar(self, *, remitente, destinatario, asunto, cuerpo, adjuntos):
        raise ErrorCorreo("fallo simulado")


class CorreoInerte:
    def __init__(self) -> None:
        self.llamadas = []

    def enviar(self, *, remitente, destinatario, asunto, cuerpo, adjuntos):
        self.llamadas.append((remitente, destinatario, asunto, cuerpo, dict(adjuntos)))


def _factura_pendiente() -> Factura:
    cliente = Cliente(id="cli-2", nombre="Cliente", nit="900123457", correo="cliente@ejemplo.com")
    producto = Producto(codigo="SKU-2", descripcion="Producto prueba 2", precio_unitario=Decimal("100.00"))
    return Factura(
        serie="FV",
        cliente=cliente,
        lineas=[LineaFactura(producto=producto, cantidad=1)],
        folio=2,
        estado=EstadoFactura.TIMBRADA,
        subtotal=Decimal("100.00"),
        descuentos=Decimal("0"),
        impuestos=Decimal("19.00"),
        total=Decimal("119.00"),
    )


def _factura_paga_para_registrar() -> Factura:
    factura = _factura_pendiente()
    factura.total = Decimal("119.00")
    return factura


def test_C3_si_falla_el_correo_el_pago_no_se_revierte_y_la_factura_queda_pagada():
    app = construir_aplicacion(correo=CorreoFallido())
    factura = _factura_pendiente()
    app.facturas.guardar_factura(factura)

    with pytest.raises(ErrorCorreo):
        app.pagos.registrar_pago("FV-2", MedioPago.EFECTIVO, Decimal("119.00"))

    guardada = app.facturas.obtener_factura("FV-2")
    assert guardada.estado == EstadoFactura.PAGADA
    assert guardada.saldo == Decimal("0")


def test_C4_un_pago_parcial_no_dispara_notificacion_y_la_factura_no_queda_pagada():
    app = construir_aplicacion(correo=CorreoInerte())
    factura = _factura_pendiente()
    app.facturas.guardar_factura(factura)

    _, cambio = app.pagos.registrar_pago("FV-2", MedioPago.EFECTIVO, Decimal("50.00"))

    guardada = app.facturas.obtener_factura("FV-2")
    assert cambio == Decimal("0")
    assert guardada.estado != EstadoFactura.PAGADA
    assert guardada.saldo == Decimal("69.00")
    assert app.notificaciones._correo.llamadas == []
