from __future__ import annotations

import pytest

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.repositorios.memoria import RepositorioClientes
from facturacion.servicios.clientes import MAXIMO_NOMBRE_CLIENTE, ServicioClientes


@pytest.fixture()
def servicio_clientes() -> ServicioClientes:
    return ServicioClientes(RepositorioClientes())


def test_registrar_recorta_espacios_y_guarda_el_nombre_limpio(servicio_clientes: ServicioClientes) -> None:
    cliente = Cliente(
        id="cli-1",
        nombre="  Tienda La 14  ",
        nit="900123456",
        correo="cliente@example.com",
    )

    registrado = servicio_clientes.registrar(cliente)

    assert registrado.nombre == "Tienda La 14"
    assert servicio_clientes.obtener("cli-1").nombre == "Tienda La 14"
    assert servicio_clientes.buscar_por_nit("900123456").nombre == "Tienda La 14"


def test_registrar_acepta_nombre_de_exactamente_120_caracteres(servicio_clientes: ServicioClientes) -> None:
    nombre = "X" * MAXIMO_NOMBRE_CLIENTE
    cliente = Cliente(id="cli-2", nombre=f"  {nombre}  ", nit="900123457")

    registrado = servicio_clientes.registrar(cliente)

    assert registrado.nombre == nombre
    assert servicio_clientes.obtener("cli-2").nombre == nombre


def test_registrar_rechaza_nombre_limpio_de_mas_de_120_caracteres_y_no_guarda(servicio_clientes: ServicioClientes) -> None:
    nombre = "X" * (MAXIMO_NOMBRE_CLIENTE + 1)
    cliente = Cliente(id="cli-3", nombre=f"  {nombre}  ", nit="900123458")

    with pytest.raises(ClienteInvalido, match=r"^El nombre del cliente no puede tener mas de 120 caracteres\. \(tiene 121\)\.$"):
        servicio_clientes.registrar(cliente)

    with pytest.raises(ClienteInvalido, match=r"^No existe el cliente cli-3\.$"):
        servicio_clientes.obtener("cli-3")


def test_registrar_rechaza_nombre_vacio_despues_de_recortar(servicio_clientes: ServicioClientes) -> None:
    cliente = Cliente(id="cli-4", nombre="   ", nit="900123459")

    with pytest.raises(ClienteInvalido, match=r"^El cliente necesita un nombre\.$"):
        servicio_clientes.registrar(cliente)


def test_registrar_rechaza_identificador_repetido(servicio_clientes: ServicioClientes) -> None:
    primero = Cliente(id="cli-5", nombre="Cliente Uno", nit="900123460")
    servicio_clientes.registrar(primero)
    duplicado = Cliente(id="cli-5", nombre="Cliente Dos", nit="900123461")

    with pytest.raises(ClienteInvalido, match=r"^Ya existe un cliente con id cli-5\.$"):
        servicio_clientes.registrar(duplicado)
