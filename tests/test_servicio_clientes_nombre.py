from __future__ import annotations

from decimal import Decimal

import pytest

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.repositorios.memoria import RepositorioClientes
from facturacion.servicios.clientes import MAX_LARGO_NOMBRE, ServicioClientes


def servicio() -> ServicioClientes:
    return ServicioClientes(RepositorioClientes())


def cliente(
    cliente_id: str = "cli-1",
    nombre: str = "Cliente Demo",
    nit: str = "900123456",
    correo: str | None = None,
) -> Cliente:
    return Cliente(cliente_id, nombre, nit, correo)


def test_registrar_recorta_espacios_externos_y_conserva_los_internos() -> None:
    servicio_clientes = servicio()
    original = cliente(nombre="  Tienda La 14  ")

    registrado = servicio_clientes.registrar(original)

    assert registrado.nombre == "Tienda La 14"
    assert servicio_clientes.obtener("cli-1").nombre == "Tienda La 14"
    assert registrado is original


def test_registrar_rechaza_nombre_recortado_mayor_a_120_caracteres_y_no_lo_guarda() -> None:
    servicio_clientes = servicio()
    nombre = f"  {'a' * (MAX_LARGO_NOMBRE + 1)}  "

    with pytest.raises(ClienteInvalido, match="El nombre del cliente no puede tener mas de 120 caracteres."):
        servicio_clientes.registrar(cliente(nombre=nombre))

    with pytest.raises(ClienteInvalido, match="No existe el cliente cli-1."):
        servicio_clientes.obtener("cli-1")


def test_registrar_acepta_nombre_de_exactamente_120_caracteres() -> None:
    servicio_clientes = servicio()
    nombre = "x" * MAX_LARGO_NOMBRE

    registrado = servicio_clientes.registrar(cliente(nombre=nombre))

    assert registrado.nombre == nombre
    assert servicio_clientes.obtener("cli-1").nombre == nombre


def test_registrar_sigue_rechazando_nombre_vacio_despues_de_limpiar() -> None:
    servicio_clientes = servicio()

    with pytest.raises(ClienteInvalido, match="El cliente necesita un nombre."):
        servicio_clientes.registrar(cliente(nombre="   \t\n  "))


def test_registrar_sigue_rechazando_nit_correo_e_id_repetido() -> None:
    servicio_clientes = servicio()

    with pytest.raises(ClienteInvalido, match="El NIT 123 no es valido."):
        servicio_clientes.registrar(cliente(nit="123"))

    with pytest.raises(ClienteInvalido, match="El correo correo-invalido no es valido."):
        servicio_clientes.registrar(cliente(correo="correo-invalido"))

    primero = servicio_clientes.registrar(cliente(cliente_id="cli-duplicado", nombre="Uno"))
    assert primero.id == "cli-duplicado"

    with pytest.raises(ClienteInvalido, match="Ya existe un cliente con id cli-duplicado."):
        servicio_clientes.registrar(cliente(cliente_id="cli-duplicado", nombre="Dos"))
