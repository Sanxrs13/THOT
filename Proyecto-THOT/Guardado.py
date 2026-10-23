import json
import os

from Parte_principal import (
    Estudiante, Docente, Director, Coordinador, Admin,
    Aula, Laboratorio, Materia, Curso, Horario, Asignacion,
)

CLASES_USUARIO = {c.__name__: c for c in (Estudiante, Docente, Director, Coordinador, Admin)}


# ---------- objeto -> diccionario ----------
def _espacio_a_dict(e):
    d = {"tipo": type(e).__name__, "codigo_edificio": e.codigo_edificio,
         "capacidad": e.capacidad, "codigo_aula": e.codigo_aula}
    if isinstance(e, Laboratorio):
        d["numero_maquinas"] = e.numero_maquinas
    return d


def _materia_a_dict(m):
    return {"nombre": m.nombre, "carrera": m.carrera, "codigo": m.codigo, "usar_lab": m.usar_lab}


def _curso_a_dict(c):
    return {"paralelo": c.paralelo, "semestre": c.semestre, "periodo": c.periodo}


def _horario_a_dict(h):
    return {"periodo": h.periodo, "hora_inicio": h.hora_inicio, "hora_fin": h.hora_fin}


# ---------- diccionario -> objeto ----------
def _dict_a_usuario(d):
    return CLASES_USUARIO[d["tipo"]](d["correo"], d["nombre"], d["contrasena"])


def _dict_a_espacio(d):
    if d["tipo"] == "Laboratorio":
        return Laboratorio(d["codigo_edificio"], d["capacidad"], d["codigo_aula"], d["numero_maquinas"])
    return Aula(d["codigo_edificio"], d["capacidad"], d["codigo_aula"])


def guardar(ruta, usuarios, espacios, materias, cursos, horarios, asignaciones):
    """Guarda todo en un json. Las asignaciones se guardan por posicion en las listas."""
    datos = {
        "usuarios": [u.datos() for u in usuarios],
        "espacios": [_espacio_a_dict(e) for e in espacios],
        "materias": [_materia_a_dict(m) for m in materias],
        "cursos": [_curso_a_dict(c) for c in cursos],
        "horarios": [_horario_a_dict(h) for h in horarios],
        "asignaciones": [
            {"docente": usuarios.index(a.docente), "materia": materias.index(a.materia),
             "curso": cursos.index(a.curso), "horario": horarios.index(a.horario),
             "espacio": espacios.index(a.espacio)}
            for a in asignaciones
        ],
    }
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)  # asi nunca queda un archivo a medias


def cargar(ruta):
    """Devuelve un diccionario de listas con objetos, o None si no hay archivo."""
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        usuarios = [_dict_a_usuario(x) for x in d["usuarios"]]
        espacios = [_dict_a_espacio(x) for x in d["espacios"]]
        materias = [Materia(**x) for x in d["materias"]]
        cursos = [Curso(x["paralelo"], x["semestre"], x["periodo"]) for x in d["cursos"]]
        horarios = [Horario(x["periodo"], x["hora_inicio"], x["hora_fin"]) for x in d["horarios"]]
        asignaciones = [
            Asignacion(usuarios[a["docente"]], materias[a["materia"]], cursos[a["curso"]],
                       horarios[a["horario"]], espacios[a["espacio"]])
            for a in d["asignaciones"]
        ]
    except (KeyError, TypeError, IndexError) as e:
        raise ValueError(f"el archivo json esta incompleto o danado ({e!r})")
    return {"usuarios": usuarios, "espacios": espacios, "materias": materias,
            "cursos": cursos, "horarios": horarios, "asignaciones": asignaciones}