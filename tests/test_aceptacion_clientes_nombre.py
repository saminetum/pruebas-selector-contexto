from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.servicios.clientes import ServicioClientes


class RepositorioClientesDoble:
    def __init__(self) -> None:
        self.guardados: dict[str, Cliente] = {}

    def guardar_cliente(self, cliente: Cliente) -> None:
        self.guardados[cliente.id] = cliente

    def obtener(self, cliente_id: str) -> Cliente | None:
        return self.guardados.get(cliente_id)

    def existe(self, cliente_id: str) -> bool:
        return cliente_id in self.guardados

    def por_nit(self, nit: str) -> Cliente | None:
        return next((cliente for cliente in self.guardados.values() if cliente.nit == nit), None)


def test_C1_registrar_recorta_espacios_y_guarda_el_nombre_normalizado() -> None:
    repositorio = RepositorioClientesDoble()
    servicio = ServicioClientes(repositorio)
    cliente = Cliente(id="cli-1", nombre="  Tienda La 14  ", nit="900123456", correo="cliente@ejemplo.com")

    resultado = servicio.registrar(cliente)

    assert resultado.nombre == "Tienda La 14"
    assert repositorio.guardados["cli-1"].nombre == "Tienda La 14"


def test_C2_registrar_rechaza_nombre_limpio_de_mas_de_120_caracteres_y_no_guarda_el_cliente() -> None:
    repositorio = RepositorioClientesDoble()
    servicio = ServicioClientes(repositorio)
    nombre_limpio = "X" * 135
    cliente = Cliente(id="cli-2", nombre=f"  {nombre_limpio}  ", nit="900123456", correo="cliente@ejemplo.com")

    with pytest.raises(ClienteInvalido, match=r"^El nombre del cliente no puede tener mas de 120 caracteres \(tiene 135\)\.$"):
        servicio.registrar(cliente)

    assert "cli-2" not in repositorio.guardados


def test_C3_registrar_acepta_nombre_limpio_de_exactamente_120_caracteres() -> None:
    repositorio = RepositorioClientesDoble()
    servicio = ServicioClientes(repositorio)
    nombre_limpio = "N" * 120
    cliente = Cliente(id="cli-3", nombre=f"  {nombre_limpio}  ", nit="900123456", correo="cliente@ejemplo.com")

    resultado = servicio.registrar(cliente)

    assert resultado.nombre == nombre_limpio
    assert repositorio.guardados["cli-3"].nombre == nombre_limpio
