import pytest

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.repositorios.memoria import RepositorioClientes
from facturacion.servicios.clientes import ServicioClientes


def test_C1_registra_cliente_con_nombre_sin_espacios_sobrantes():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    cliente = Cliente(id="c-1", nombre="  Tienda La 14  ", nit="900123456", correo="cliente@tienda.com")

    resultado = servicio.registrar(cliente)

    assert resultado.nombre == "Tienda La 14"
    assert repositorio.obtener("c-1").nombre == "Tienda La 14"


def test_C2_rechaza_nombre_con_mas_de_120_caracteres_despues_del_trim_y_no_guarda():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    nombre = "   " + ("a" * 121) + "   "
    cliente = Cliente(id="c-2", nombre=nombre, nit="900123456", correo="cliente@tienda.com")

    with pytest.raises(ClienteInvalido, match=r"^El nombre del cliente no puede tener mas de 120 caracteres\.$"):
        servicio.registrar(cliente)

    assert repositorio.obtener("c-2") is None


def test_C3_acepta_nombre_de_exactamente_120_caracteres_despues_del_trim():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    nombre = "  " + ("b" * 120) + "  "
    cliente = Cliente(id="c-3", nombre=nombre, nit="900123456", correo="cliente@tienda.com")

    resultado = servicio.registrar(cliente)

    assert resultado.nombre == "b" * 120
    assert repositorio.obtener("c-3").nombre == "b" * 120


def test_C4_sigue_rechazando_nombre_vacio():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    cliente = Cliente(id="c-4", nombre="   ", nit="900123456", correo="cliente@tienda.com")

    with pytest.raises(ClienteInvalido, match="El cliente necesita un nombre\\."):
        servicio.registrar(cliente)

    assert repositorio.obtener("c-4") is None


def test_C4_sigue_rechazando_nit_invalido():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    cliente = Cliente(id="c-5", nombre="Cliente", nit="nit-invalido", correo="cliente@tienda.com")

    with pytest.raises(ClienteInvalido, match=r"^El NIT nit-invalido no es valido\.$"):
        servicio.registrar(cliente)

    assert repositorio.obtener("c-5") is None


def test_C4_sigue_rechazando_correo_invalido():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    cliente = Cliente(id="c-6", nombre="Cliente", nit="900123456", correo="correo-invalido")

    with pytest.raises(ClienteInvalido, match=r"^El correo correo-invalido no es valido\.$"):
        servicio.registrar(cliente)

    assert repositorio.obtener("c-6") is None


def test_C4_sigue_rechazando_identificador_repetido():
    repositorio = RepositorioClientes()
    servicio = ServicioClientes(repositorio)
    primero = Cliente(id="c-7", nombre="Primero", nit="900123456", correo="primero@tienda.com")
    segundo = Cliente(id="c-7", nombre="Segundo", nit="900123457", correo="segundo@tienda.com")

    servicio.registrar(primero)

    with pytest.raises(ClienteInvalido, match=r"^Ya existe un cliente con id c-7\.$"):
        servicio.registrar(segundo)

    assert repositorio.obtener("c-7").nombre == "Primero"
