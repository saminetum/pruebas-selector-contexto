"""Cobro de facturas timbradas: efectivo con cambio, tarjeta y transferencia.

Solo se cobra una factura timbrada: cobrar algo sin validez fiscal dejaria un
ingreso sin comprobante. En efectivo se puede entregar mas del saldo y se devuelve
el cambio; con tarjeta o transferencia el monto no puede superar el saldo y hace
falta la referencia de la operacion.
"""

from __future__ import annotations

from decimal import Decimal

from facturacion.errores import EstadoInvalido, PagoRechazado
from facturacion.modelos import EstadoFactura, Factura, MedioPago, Pago
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.notificaciones import ServicioNotificaciones
from facturacion.utilidades.dinero import a_decimal, redondear
from facturacion.utilidades.fechas import ahora


class ServicioPagos:
    def __init__(
        self,
        facturas: RepositorioFacturas,
        auditoria: RegistroAuditoria,
        notificaciones: ServicioNotificaciones | None = None,
    ) -> None:
        self._facturas = facturas
        self._auditoria = auditoria
        self._notificaciones = notificaciones

    def registrar_pago(
        self,
        identificador: str,
        medio: MedioPago,
        monto: object,
        referencia: str | None = None,
    ) -> tuple[Factura, Decimal]:
        """Aplica un pago y devuelve la factura y el cambio que hay que entregar."""
        factura = self._facturas.obtener_factura(identificador)
        if factura.estado != EstadoFactura.TIMBRADA:
            raise EstadoInvalido(
                f"Solo se cobra una factura timbrada y sin pagar; {identificador} esta "
                f"{factura.estado.value}."
            )
        valor = redondear(a_decimal(monto))
        if valor <= 0:
            raise PagoRechazado("El monto del pago debe ser mayor que cero.")
        if medio != MedioPago.EFECTIVO:
            if not referencia:
                raise PagoRechazado(
                    "Los pagos con tarjeta o transferencia necesitan la referencia de la operacion."
                )
            if valor > factura.saldo:
                raise PagoRechazado("Con tarjeta o transferencia no se puede pagar mas del saldo.")

        aplicado = min(valor, factura.saldo)
        cambio = redondear(valor - aplicado)
        factura.pagos.append(Pago(medio, aplicado, ahora(), referencia))
        if factura.saldo == 0:
            factura.estado = EstadoFactura.PAGADA
        self._facturas.guardar_factura(factura)
        self._auditoria.registrar(
            "pago_registrado", factura=identificador, medio=medio.value, monto=str(aplicado)
        )
        if factura.estado == EstadoFactura.PAGADA and self._notificaciones is not None:
            self._notificaciones.enviar_comprobante(factura)
        return factura, cambio
