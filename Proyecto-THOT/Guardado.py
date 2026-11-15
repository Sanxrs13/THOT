import json
import os
from abc import ABC, abstractmethod

from Parte_principal import (
    Usuario, EspacioEstudio, Facultad, Carrera, Materia, Curso, Horario, Asignacion,
    subclases_concretas, _buscar,
)


# [I]
class LectorDatos(ABC):
    @abstractmethod
    def cargar(self):
        pass


# [I]
class EscritorDatos(ABC):
    @abstractmethod
    def guardar(self, datos):
        pass

    @abstractmethod
    def borrar(self):
        pass


def _clase_por_nombre(base, nombre):
    # [O] se buscan las subclases: agregar un nuevo rol no obliga a tocar este archivo
    for clase in subclases_concretas(base):
        if clase.__name__ == nombre:
            return clase
    raise KeyError(f"tipo desconocido: {nombre}")


# Como reconstruir cada lista a partir del json.
# EL ORDEN IMPORTA: cada lista solo puede depender de las anteriores.
_FABRICAS = {
    "facultades": Facultad.desde_datos,
    "carreras": Carrera.desde_datos,
    "usuarios": lambda d, datos: _clase_por_nombre(Usuario, d["tipo"]).desde_datos(d, datos),
    "espacios": lambda d, datos: _clase_por_nombre(EspacioEstudio, d["tipo"]).desde_datos(d, datos),
    "materias": Materia.desde_datos,
    "cursos": Curso.desde_datos,
    "horarios": Horario.desde_datos,
}


class AlmacenJSON(LectorDatos, EscritorDatos):
    def __init__(self, ruta):
        self.ruta = ruta

    def guardar(self, datos):
        """Guarda todo en un json. Las referencias se guardan por codigo/cedula (cursos y horarios por posicion)."""
        salida = {nombre: [x.datos() for x in datos[nombre]] for nombre in _FABRICAS}
        salida["asignaciones"] = [
            {"id": a.id,
             "docente": a.docente.cedula,
             "materia": a.materia.codigo,
             "curso": datos["cursos"].index(a.curso),
             "horario": datos["horarios"].index(a.horario),
             "espacio": a.espacio.id}
            for a in datos["asignaciones"]
        ]
        temporal = self.ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=2)
        os.replace(temporal, self.ruta)   # escritura atomica: nunca queda un json a medias

    def cargar(self):
        """Devuelve un diccionario de listas con objetos, o None si no hay archivo."""
        if not os.path.exists(self.ruta):
            return None
        try:
            with open(self.ruta, encoding="utf-8") as f:
                d = json.load(f)
            datos = {}
            for nombre, fabrica in _FABRICAS.items():
                datos[nombre] = [fabrica(x, datos) for x in d[nombre]]
            datos["asignaciones"] = [
                Asignacion(_buscar(datos["usuarios"], "cedula", a["docente"]),
                           _buscar(datos["materias"], "codigo", a["materia"]),
                           datos["cursos"][a["curso"]],
                           datos["horarios"][a["horario"]],
                           _buscar(datos["espacios"], "id", a["espacio"]),
                           id=a["id"])
                for a in d["asignaciones"]
            ]
        except (KeyError, TypeError, IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"el archivo json esta incompleto, danado o tiene el formato antiguo ({e!r})")
        return datos

    def borrar(self):
        if os.path.exists(self.ruta):
            os.remove(self.ruta)
