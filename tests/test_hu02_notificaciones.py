from decimal import Decimal

import pytest

from facturacion.aplicacion import construir_aplicacion
from facturacion.config import Configuracion
from facturacion.errores import ErrorCorreo
from facturacion.modelos import Cliente, EstadoFactura, Factura, LineaFactura, MedioPago, Producto
from facturacion.servicios.notificaciones import ServicioNotificaciones


class CorreoDoble:
    def __init__(self) -> None:
        self.llamadas = []

    def enviar(self, *, remitente, destinatario, asunto, cuerpo, adjuntos):
        self.llamadas.append(
            {
                "remitente": remitente,
                "destinatario": destinatario,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "adjuntos": dict(adjuntos),
            }
        )


class CorreoDobleFallido(CorreoDoble):
    def enviar(self, *, remitente, destinatario, asunto, cuerpo, adjuntos):
        raise ErrorCorreo("fallo simulado")


def _factura_pagada(con_correo: str | None = "comprador@ejemplo.com") -> Factura:
    cliente = Cliente(id="cli-1", nombre="Comprador", nit="900123456", correo=con_correo)
    producto = Producto(codigo="SKU-1", descripcion="Producto prueba", precio_unitario=Decimal("100.00"))
    factura = Factura(
        serie="FV",
        cliente=cliente,
        lineas=[LineaFactura(producto=producto, cantidad=1)],
        folio=1,
        estado=EstadoFactura.PAGADA,
        subtotal=Decimal("100.00"),
        descuentos=Decimal("0"),
        impuestos=Decimal("19.00"),
        total=Decimal("119.00"),
    )
    return factura


def test_C1_enviar_comprobante_adjunta_pdf_y_xml_al_correo_del_comprador():
    correo = CorreoDoble()
    servicio = ServicioNotificaciones(correo, Configuracion())
    factura = _factura_pagada("comprador@ejemplo.com")

    resultado = servicio.enviar_comprobante(factura)

    assert resultado is True
    assert len(correo.llamadas) == 1
    llamada = correo.llamadas[0]
    assert llamada["destinatario"] == "comprador@ejemplo.com"
    assert set(llamada["adjuntos"].keys()) == {"pdf", "xml"}
    assert isinstance(llamada["adjuntos"]["pdf"], (bytes, bytearray))
    assert isinstance(llamada["adjuntos"]["xml"], (bytes, bytearray))
    assert llamada["adjuntos"]["pdf"]
    assert llamada["adjuntos"]["xml"]


def test_C2_enviar_comprobante_sin_correo_no_intenta_enviar_nada():
    correo = CorreoDoble()
    servicio = ServicioNotificaciones(correo, Configuracion())
    factura = _factura_pagada(None)

    resultado = servicio.enviar_comprobante(factura)

    assert resultado is False
    assert correo.llamadas == []
