"""Registro y consulta de clientes, con sus datos fiscales validados."""

from __future__ import annotations

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.repositorios.memoria import RepositorioClientes
from facturacion.utilidades.validaciones import (
    NIT_CONSUMIDOR_FINAL,
    normalizar_nit,
    validar_correo,
    validar_nit,
)

ID_CONSUMIDOR_FINAL = "consumidor-final"


class ServicioClientes:
    def __init__(self, repositorio: RepositorioClientes) -> None:
        self._repo = repositorio

    def registrar(self, cliente: Cliente) -> Cliente:
        if not cliente.nombre.strip():
            raise ClienteInvalido("El cliente necesita un nombre.")
        if self._repo.existe(cliente.id):
            raise ClienteInvalido(f"Ya existe un cliente con id {cliente.id}.")

        existente = self.buscar_por_nit(cliente.nit)
        if existente is not None:
            raise ClienteInvalido(
                f"El NIT {cliente.nit} ya esta registrado y pertenece al cliente {existente.nombre} ({existente.id})."
            )
        if not validar_nit(cliente.nit):
            raise ClienteInvalido(f"El NIT {cliente.nit} no es valido.")
        if cliente.correo and not validar_correo(cliente.correo):
            raise ClienteInvalido(f"El correo {cliente.correo} no es valido.")

        self._repo.guardar_cliente(cliente)
        return cliente

    def obtener(self, cliente_id: str) -> Cliente:
        cliente = self._repo.obtener(cliente_id)
        if cliente is None:
            raise ClienteInvalido(f"No existe el cliente {cliente_id}.")
        return cliente

    def buscar_por_nit(self, nit: str) -> Cliente | None:
        nit_normalizado = normalizar_nit(nit)
        return self._repo.por_nit(nit_normalizado)

    def consumidor_final(self) -> Cliente:
        """El cliente generico para ventas sin datos del comprador."""
        cliente = self._repo.obtener(ID_CONSUMIDOR_FINAL)
        if cliente is None:
            cliente = Cliente(ID_CONSUMIDOR_FINAL, "Consumidor final", NIT_CONSUMIDOR_FINAL)
            self._repo.guardar_cliente(cliente)
        return cliente

    def actualizar_correo(self, cliente_id: str, correo: str) -> Cliente:
        if not validar_correo(correo):
            raise ClienteInvalido(f"El correo {correo} no es valido.")
        cliente = self.obtener(cliente_id)
        cliente.correo = correo
        return cliente
