"""
Permisos por rol de THOT.

Para cambiar lo que puede hacer cada rol solo hay que editar el diccionario PERMISOS.
Cada rol tiene, por modulo, un conjunto de acciones:
    "ver"       -> puede abrir la pagina y consultar la informacion
    "gestionar" -> puede crear, editar y eliminar registros
El servidor aplica estos permisos en cada peticion; el HTML solo oculta lo que no corresponde.
"""

MODULOS = ["horarios", "materias", "usuarios", "carreras", "facultades", "espacios", "asignadas"]

_TODO = {"ver", "gestionar"}
_VER = {"ver"}

PERMISOS = {
    # Administrador: acceso total
    "Administrador": {m: _TODO for m in MODULOS},

    # Director: gestiona horarios y materias; consulta el resto
    "Director": {
        "horarios": _TODO, "materias": _TODO, "usuarios": _VER, "carreras": _VER,
        "facultades": _VER, "espacios": _VER, "asignadas": _VER,
    },

    # Presidente: arma los horarios (asignaciones); consulta materias, usuarios y estructura
    "Presidente": {
        "horarios": _TODO, "materias": _VER, "usuarios": _VER, "carreras": _VER,
        "facultades": _VER, "espacios": _VER, "asignadas": _VER,
    },

    # Docente: ve horarios, materias y sus materias asignadas
    "Docente": {"horarios": _VER, "materias": _VER, "asignadas": _VER},

    # Estudiante: solo puede ver los horarios
    "Estudiante": {"horarios": _VER},
}


def permisos_de(rol: str) -> dict:
    return PERMISOS.get(rol, {})


def puede(rol: str, modulo: str, accion: str = "ver") -> bool:
    return accion in permisos_de(rol).get(modulo, set())
