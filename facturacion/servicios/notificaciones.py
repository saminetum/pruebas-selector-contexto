"""Avisos por correo al cliente.

Hoy solo existe el aviso de factura anulada. El envio del comprobante (PDF y XML)
al comprador tambien forma parte del flujo de cobro cuando la factura queda
pagada.
"""

from __future__ import annotations

from facturacion.config import Configuracion
from facturacion.documentos.pdf import generar_pdf, nombre_archivo_pdf
from facturacion.documentos.xml import generar_xml, nombre_archivo_xml
from facturacion.errores import ErrorCorreo
from facturacion.integraciones.correo import ClienteCorreo
from facturacion.modelos import Factura
from facturacion.utilidades.validaciones import validar_correo


class ServicioNotificaciones:
    def __init__(self, correo: ClienteCorreo, config: Configuracion) -> None:
        self._correo = correo
        self._config = config

    def enviar(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        adjuntos: dict[str, bytes] | None = None,
    ) -> None:
        if not validar_correo(destinatario):
            raise ErrorCorreo(f"El destinatario {destinatario} no es un correo valido.")
        self._correo.enviar(
            remitente=self._config.remitente_correo,
            destinatario=destinatario,
            asunto=asunto,
            cuerpo=cuerpo,
            adjuntos=adjuntos or {},
        )

    def enviar_comprobante(self, factura: Factura) -> bool:
        """Envía al comprador el PDF y el XML de la factura ya pagada.

        Devuelve False si no hay correo registrado. Si el cliente de correo falla,
        la excepción se propaga para que el pago no se deshaga, pero la venta ya
        quedó registrada.
        """
        if not factura.cliente.correo:
            return False
        if not validar_correo(factura.cliente.correo):
            raise ErrorCorreo(
                f"El correo del comprador {factura.cliente.correo} no es valido."
            )
        adjuntos = {
            nombre_archivo_pdf(factura): generar_pdf(factura, self._config),
            nombre_archivo_xml(factura): generar_xml(factura, self._config).encode("utf-8"),
        }
        self.enviar(
            factura.cliente.correo,
            f"Comprobante de pago de factura {factura.identificador}",
            f"Hola {factura.cliente.nombre}: adjuntamos el PDF y el XML de su factura {factura.identificador}.",
            adjuntos=adjuntos,
        )
        return True

    def avisar_anulacion(self, factura: Factura) -> bool:
        """Avisa al cliente de que su factura se anulo. False si no tiene correo."""
        if not factura.cliente.correo:
            return False
        self.enviar(
            factura.cliente.correo,
            f"Factura {factura.identificador} anulada",
            f"Hola {factura.cliente.nombre}: su factura {factura.identificador} fue anulada. "
            f"Motivo: {factura.motivo_anulacion}.",
        )
        return True
