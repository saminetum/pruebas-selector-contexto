"""Programa de puntos: el cliente acumula al pagar y se identifica como frecuente
cuando alcanza un saldo suficiente para recibir beneficios en facturación.

Un punto por cada 1.000 pesos pagados. Cada punto vale 10 pesos al redimir. Los
puntos se acumulan sobre lo pagado, no sobre lo facturado: una factura que no se
paga no da puntos.
"""

from __future__ import annotations

from decimal import Decimal

from facturacion.errores import ClienteInvalido, PagoRechazado
from facturacion.modelos import Factura
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.clientes import ID_CONSUMIDOR_FINAL
from facturacion.utilidades.dinero import redondear

PESOS_POR_PUNTO = Decimal("1000")
VALOR_PUNTO = Decimal("10")
UMBRAL_CLIENTE_FRECUENTE = 500


class ProgramaPuntos:
    def __init__(self, auditoria: RegistroAuditoria) -> None:
        self._auditoria = auditoria
        self._saldos: dict[str, int] = {}
        self._acreditadas: set[str] = set()

    def saldo(self, cliente_id: str) -> int:
        return self._saldos.get(cliente_id, 0)

    def es_frecuente(self, cliente_id: str) -> bool:
        """Devuelve True solo para clientes con al menos 500 puntos y no consumidor final."""
        if cliente_id == ID_CONSUMIDOR_FINAL:
            return False
        return self.saldo(cliente_id) >= UMBRAL_CLIENTE_FRECUENTE

    def acumular(self, factura: Factura) -> int:
        """Suma los puntos de lo pagado. Una factura acumula una sola vez."""
        if factura.identificador in self._acreditadas:
            return 0
        if factura.cliente.id == ID_CONSUMIDOR_FINAL:
            raise ClienteInvalido("Las ventas a consumidor final no acumulan puntos.")
        puntos = int(factura.total_pagado // PESOS_POR_PUNTO)
        self._saldos[factura.cliente.id] = self.saldo(factura.cliente.id) + puntos
        self._acreditadas.add(factura.identificador)
        self._auditoria.registrar("puntos_acumulados", cliente=factura.cliente.id, puntos=puntos)
        return puntos

    def redimir(self, cliente_id: str, puntos: int) -> Decimal:
        """Descuenta puntos del saldo y devuelve su valor en pesos."""
        if puntos <= 0:
            raise PagoRechazado("Hay que redimir al menos un punto.")
        if puntos > self.saldo(cliente_id):
            raise PagoRechazado(
                f"El cliente {cliente_id} tiene {self.saldo(cliente_id)} puntos y pidio {puntos}."
            )
        self._saldos[cliente_id] -= puntos
        valor = redondear(VALOR_PUNTO * puntos)
        self._auditoria.registrar("puntos_redimidos", cliente=cliente_id, puntos=puntos, valor=str(valor))
        return valor
