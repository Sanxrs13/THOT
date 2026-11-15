"""
Logica del sistema THOT (sin nada de web ni de consola).
Servidor.py solo traduce peticiones HTTP a llamadas de esta clase.
"""
import threading

from Parte_principal import (
    Usuario, Estudiante, Docente, Director, Presidente, Administrador,
    Facultad, Carrera, Materia, Curso, Horario, Aula, Laboratorio,
    subclases_concretas, normalizar_nivel,
)


class NoEncontrado(Exception):
    pass


def _entero(valor, campo):
    try:
        if isinstance(valor, bool):
            raise ValueError
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un numero entero")


def _texto(d, campo, etiqueta=None):
    valor = d.get(campo, "")
    if not isinstance(valor, str):
        raise ValueError(f"{etiqueta or campo} no es valido")
    return valor


class Sistema:
    def __init__(self, servicio, autenticador, lector, escritor):
        self.servicio = servicio
        self.autenticador = autenticador
        self.lector = lector
        self.escritor = escritor
        self.cerrojo = threading.RLock()     # el servidor atiende varias peticiones a la vez
        self.facultades, self.carreras, self.usuarios = [], [], []
        self.espacios, self.materias, self.cursos, self.horarios = [], [], [], []

    # ------------------------------------------------------------------ persistencia
    def _datos(self):
        return {"facultades": self.facultades, "carreras": self.carreras,
                "usuarios": self.usuarios, "espacios": self.espacios,
                "materias": self.materias, "cursos": self.cursos,
                "horarios": self.horarios, "asignaciones": self.servicio.asignaciones}

    def guardar(self):
        self.escritor.guardar(self._datos())

    def cargar(self):
        """True si habia datos guardados, False si el archivo no existe. ValueError si esta danado."""
        datos = self.lector.cargar()
        if datos is None:
            return False
        for nombre in ("facultades", "carreras", "usuarios", "espacios", "materias", "cursos", "horarios"):
            getattr(self, nombre)[:] = datos[nombre]
        self.servicio.asignaciones[:] = datos["asignaciones"]
        return True

    # ------------------------------------------------------------------ busquedas
    @staticmethod
    def _buscar(lista, atributo, valor, nombre):
        for x in lista:
            if getattr(x, atributo) == valor:
                return x
        raise NoEncontrado(f"{nombre} no encontrado")

    def facultad(self, codigo):
        return self._buscar(self.facultades, "codigo", codigo, "Facultad")

    def carrera(self, codigo):
        return self._buscar(self.carreras, "codigo", codigo, "Carrera")

    def usuario(self, cedula):
        return self._buscar(self.usuarios, "cedula", cedula, "Usuario")

    def materia(self, codigo):
        return self._buscar(self.materias, "codigo", codigo, "Materia")

    def espacio(self, id):
        return self._buscar(self.espacios, "id", id, "Espacio")

    @staticmethod
    def _codigo_libre(lista, codigo, actual=None):
        for x in lista:
            if x is not actual and x.codigo.lower() == codigo.lower():
                return False
        return True

    # ------------------------------------------------------------------ vistas (lo que ve la web)
    @staticmethod
    def v_facultad(f):
        return {"nombre": f.nombre, "codigo": f.codigo}

    @staticmethod
    def v_carrera(c):
        return {"nombre": c.nombre, "codigo": c.codigo,
                "facultadCodigo": c.facultad.codigo, "facultadNombre": c.facultad.nombre}

    @staticmethod
    def v_usuario(u):
        return {"nombre": u.nombre, "cedula": u.cedula, "correo": u.correo, "nivel": u.nivel,
                "rol": u.tipo,
                "facultadCodigo": u.facultad.codigo, "facultadNombre": u.facultad.nombre,
                "carreraCodigo": u.carrera.codigo, "carreraNombre": u.carrera.nombre}

    @staticmethod
    def v_materia(m):
        return {"nombre": m.nombre, "codigo": m.codigo, "creditos": m.creditos, "usarLab": m.usar_lab,
                "facultadCodigo": m.carrera.facultad.codigo, "facultadNombre": m.carrera.facultad.nombre,
                "carreraCodigo": m.carrera.codigo, "carreraNombre": m.carrera.nombre}

    @staticmethod
    def v_espacio(e):
        return {"id": e.id, "tipo": e.tipo, "codigoEdificio": e.codigo_edificio,
                "capacidad": e.capacidad, "codigoAula": e.codigo_aula,
                "numeroMaquinas": getattr(e, "numero_maquinas", None),
                "descripcion": e.descripcion()}

    @staticmethod
    def v_asignacion(a):
        return {"id": a.id,
                "docenteCedula": a.docente.cedula, "docenteNombre": a.docente.nombre,
                "materiaCodigo": a.materia.codigo, "materiaNombre": a.materia.nombre,
                "usarLab": a.materia.usar_lab,
                "facultadCodigo": a.curso.carrera.facultad.codigo,
                "carreraCodigo": a.curso.carrera.codigo, "carreraNombre": a.curso.carrera.nombre,
                "paralelo": a.curso.paralelo, "semestre": a.curso.semestre, "periodo": a.curso.periodo,
                "dia": a.horario.dia, "horaInicio": a.horario.hora_inicio, "horaFin": a.horario.hora_fin,
                "espacioId": a.espacio.id, "espacioTipo": a.espacio.tipo, "espacioDescripcion": a.espacio.descripcion()}

    # ------------------------------------------------------------------ facultades
    def crear_facultad(self, d):
        with self.cerrojo:
            f = Facultad(_texto(d, "nombre"), _texto(d, "codigo"))
            if not self._codigo_libre(self.facultades, f.codigo):
                raise ValueError("Ya existe una facultad con ese codigo")
            self.facultades.append(f)
            self.guardar()
            return f

    def editar_facultad(self, codigo, d):
        with self.cerrojo:
            actual = self.facultad(codigo)
            nueva = Facultad(_texto(d, "nombre"), _texto(d, "codigo"))
            if not self._codigo_libre(self.facultades, nueva.codigo, actual):
                raise ValueError("Ya existe una facultad con ese codigo")
            actual.nombre, actual.codigo = nueva.nombre, nueva.codigo
            self.guardar()
            return actual

    def eliminar_facultad(self, codigo):
        with self.cerrojo:
            f = self.facultad(codigo)
            if any(c.facultad is f for c in self.carreras):
                raise ValueError("No se puede eliminar: la facultad tiene carreras asociadas")
            self.facultades.remove(f)
            self.guardar()

    # ------------------------------------------------------------------ carreras
    def crear_carrera(self, d):
        with self.cerrojo:
            fac = self.facultad(_texto(d, "facultadCodigo"))
            c = Carrera(_texto(d, "nombre"), _texto(d, "codigo"), fac)
            if not self._codigo_libre(self.carreras, c.codigo):
                raise ValueError("Ya existe una carrera con ese codigo")
            self.carreras.append(c)
            self.guardar()
            return c

    def editar_carrera(self, codigo, d):
        with self.cerrojo:
            actual = self.carrera(codigo)
            fac = self.facultad(_texto(d, "facultadCodigo"))
            nueva = Carrera(_texto(d, "nombre"), _texto(d, "codigo"), fac)
            if not self._codigo_libre(self.carreras, nueva.codigo, actual):
                raise ValueError("Ya existe una carrera con ese codigo")
            actual.nombre, actual.codigo, actual.facultad = nueva.nombre, nueva.codigo, nueva.facultad
            self.guardar()
            return actual

    def eliminar_carrera(self, codigo):
        with self.cerrojo:
            c = self.carrera(codigo)
            if any(u.carrera is c for u in self.usuarios) or any(m.carrera is c for m in self.materias) \
                    or any(x.carrera is c for x in self.cursos):
                raise ValueError("No se puede eliminar: la carrera tiene usuarios, materias o cursos asociados")
            self.carreras.remove(c)
            self.guardar()

    # ------------------------------------------------------------------ usuarios
    @staticmethod
    def clase_de_rol(nombre):
        for clase in subclases_concretas(Usuario):
            if clase.__name__ == nombre:
                return clase
        raise ValueError("Rol no valido")

    def crear_usuario(self, d):
        with self.cerrojo:
            clase = self.clase_de_rol(_texto(d, "rol"))
            carrera = self.carrera(_texto(d, "carreraCodigo"))
            u = clase(_texto(d, "cedula"), _texto(d, "nombre"), _texto(d, "contrasena"),
                      _texto(d, "nivel"), carrera)
            if any(x.cedula == u.cedula for x in self.usuarios):
                raise ValueError("Ya existe un usuario con esa cedula")
            self.usuarios.append(u)
            self.guardar()
            return u

    def editar_usuario(self, cedula, d):
        with self.cerrojo:
            viejo = self.usuario(cedula)
            clase = self.clase_de_rol(_texto(d, "rol"))
            carrera = self.carrera(_texto(d, "carreraCodigo"))
            contrasena = _texto(d, "contrasena")
            # si no escribe contrasena nueva se conserva la anterior
            nuevo = clase(_texto(d, "cedula"), _texto(d, "nombre"), contrasena, _texto(d, "nivel"), carrera,
                          clave_hash=None if contrasena.strip() else viejo.clave_hash())
            if any(x is not viejo and x.cedula == nuevo.cedula for x in self.usuarios):
                raise ValueError("Ya existe un usuario con esa cedula")
            asignadas = [a for a in self.servicio.asignaciones if a.docente is viejo]
            if asignadas and not isinstance(nuevo, Docente):
                raise ValueError("No se puede cambiar el rol: el docente tiene materias asignadas")
            self.usuarios[self.usuarios.index(viejo)] = nuevo
            for a in asignadas:
                a.docente = nuevo
            self.guardar()
            return nuevo

    def eliminar_usuario(self, cedula):
        with self.cerrojo:
            u = self.usuario(cedula)
            if any(a.docente is u for a in self.servicio.asignaciones):
                raise ValueError("No se puede eliminar: el docente tiene materias asignadas")
            self.usuarios.remove(u)
            self.guardar()

    # ------------------------------------------------------------------ materias
    def _armar_materia(self, d):
        carrera = self.carrera(_texto(d, "carreraCodigo"))
        usar_lab = d.get("usarLab", False)
        if not isinstance(usar_lab, bool):
            raise ValueError("Valor de laboratorio no valido")
        return Materia(_texto(d, "nombre"), _texto(d, "codigo"), _entero(d.get("creditos"), "Los creditos"),
                       carrera, usar_lab)

    def crear_materia(self, d):
        with self.cerrojo:
            m = self._armar_materia(d)
            if not self._codigo_libre(self.materias, m.codigo):
                raise ValueError("Ya existe una materia con ese codigo")
            self.materias.append(m)
            self.guardar()
            return m

    def editar_materia(self, codigo, d):
        with self.cerrojo:
            actual = self.materia(codigo)
            nueva = self._armar_materia(d)
            if not self._codigo_libre(self.materias, nueva.codigo, actual):
                raise ValueError("Ya existe una materia con ese codigo")
            usada = [a for a in self.servicio.asignaciones if a.materia is actual]
            if usada and (nueva.carrera is not actual.carrera or (nueva.usar_lab and not actual.usar_lab)):
                raise ValueError("No se puede cambiar la carrera ni exigir laboratorio: la materia ya esta asignada")
            actual.nombre, actual.codigo, actual.creditos = nueva.nombre, nueva.codigo, nueva.creditos
            actual.carrera, actual.usar_lab = nueva.carrera, nueva.usar_lab
            self.guardar()
            return actual

    def eliminar_materia(self, codigo):
        with self.cerrojo:
            m = self.materia(codigo)
            if any(a.materia is m for a in self.servicio.asignaciones):
                raise ValueError("No se puede eliminar: la materia esta asignada en algun horario")
            self.materias.remove(m)
            self.guardar()

    # ------------------------------------------------------------------ espacios (aulas y laboratorios)
    def _armar_espacio(self, d):
        tipo = _texto(d, "tipo")
        edificio = _texto(d, "codigoEdificio")
        capacidad = _entero(d.get("capacidad"), "La capacidad")
        aula = _entero(d.get("codigoAula"), "El codigo del aula")
        if tipo == "Aula":
            return Aula(edificio, capacidad, aula)
        if tipo == "Laboratorio":
            return Laboratorio(edificio, capacidad, aula, _entero(d.get("numeroMaquinas"), "El numero de maquinas"))
        raise ValueError("Tipo de espacio no valido")

    def crear_espacio(self, d):
        with self.cerrojo:
            e = self._armar_espacio(d)
            if any(x.id.lower() == e.id.lower() for x in self.espacios):
                raise ValueError("Ya existe un espacio con ese edificio y codigo de aula")
            self.espacios.append(e)
            self.guardar()
            return e

    def editar_espacio(self, id, d):
        with self.cerrojo:
            viejo = self.espacio(id)
            nuevo = self._armar_espacio(d)
            if any(x is not viejo and x.id.lower() == nuevo.id.lower() for x in self.espacios):
                raise ValueError("Ya existe un espacio con ese edificio y codigo de aula")
            usadas = [a for a in self.servicio.asignaciones if a.espacio is viejo]
            for a in usadas:
                if not nuevo.admite(a.materia):
                    raise ValueError("No se puede cambiar: el espacio tiene materias que requieren laboratorio")
            self.espacios[self.espacios.index(viejo)] = nuevo
            for a in usadas:
                a.espacio = nuevo
            self.guardar()
            return nuevo

    def eliminar_espacio(self, id):
        with self.cerrojo:
            e = self.espacio(id)
            if any(a.espacio is e for a in self.servicio.asignaciones):
                raise ValueError("No se puede eliminar: el espacio esta usado en algun horario")
            self.espacios.remove(e)
            self.guardar()

    # ------------------------------------------------------------------ asignaciones
    def crear_asignacion(self, d):
        with self.cerrojo:
            docente = self.usuario(_texto(d, "docenteCedula"))
            materia = self.materia(_texto(d, "materiaCodigo"))
            espacio = self.espacio(_texto(d, "espacioId"))
            periodo = _texto(d, "periodo")
            # se reutilizan cursos y horarios iguales para que las reglas de cruce comparen los mismos objetos
            curso_n = Curso(materia.carrera, _texto(d, "paralelo"), _texto(d, "semestre"), periodo)
            horario_n = Horario(periodo, _texto(d, "dia"), _entero(d.get("horaInicio"), "La hora de inicio"),
                                _entero(d.get("horaFin"), "La hora de fin"))
            curso = next((c for c in self.cursos if c.clave() == curso_n.clave()), curso_n)
            horario = next((h for h in self.horarios if h.clave() == horario_n.clave()), horario_n)
            a = self.servicio.asignar(docente, materia, curso, horario, espacio)   # valida y notifica
            if curso not in self.cursos:
                self.cursos.append(curso)
            if horario not in self.horarios:
                self.horarios.append(horario)
            self.guardar()
            return a

    def eliminar_asignacion(self, id_asignacion):
        with self.cerrojo:
            a = self.servicio.eliminar(id_asignacion)
            if a is None:
                raise NoEncontrado("Asignacion no encontrada")
            usados_c = {id(x.curso) for x in self.servicio.asignaciones}
            usados_h = {id(x.horario) for x in self.servicio.asignaciones}
            self.cursos[:] = [c for c in self.cursos if id(c) in usados_c]
            self.horarios[:] = [h for h in self.horarios if id(h) in usados_h]
            self.guardar()

    def listar_asignaciones(self, facultad="", carrera="", periodo="", semestre="", paralelo="", docente=""):
        sem = normalizar_nivel(semestre) if semestre else ""
        res = []
        for a in self.servicio.asignaciones:
            if facultad and a.curso.carrera.facultad.codigo != facultad:
                continue
            if carrera and a.curso.carrera.codigo != carrera:
                continue
            if periodo and a.curso.periodo != periodo:
                continue
            if sem and a.curso.semestre != sem:
                continue
            if paralelo and a.curso.paralelo != paralelo.upper():
                continue
            if docente and a.docente.cedula != docente:
                continue
            res.append(a)
        res.sort(key=lambda a: (a.horario.dia, a.horario.hora_inicio))
        return res

    # ------------------------------------------------------------------ datos de ejemplo (primer arranque)
    def cargar_ejemplo(self, clave="Thot2026"):
        fcc = Facultad("Facultad de Ciencias de la Vida y Tecnologias", "FCVT")
        fing = Facultad("Facultad de Ingenieria", "FING")
        self.facultades[:] = [fcc, fing]
        isw = Carrera("Ingenieria en Software", "ISW01", fcc)
        iti = Carrera("Tecnologias de la Informacion", "TIC01", fcc)
        civ = Carrera("Ingenieria Civil", "CIV01", fing)
        self.carreras[:] = [isw, iti, civ]
        self.usuarios[:] = [
            Administrador("1300000001", "Administrador THOT", clave, "Primero", isw),
            Director("1300000002", "Diana Director", clave, "Primero", isw),
            Presidente("1300000003", "Carlos Presidente", clave, "Primero", isw),
            Docente("1300000004", "Luis Docente", clave, "Primero", isw),
            Docente("1300000006", "Marta Docente", clave, "Primero", isw),
            Estudiante("1300000005", "Ana Estudiante", clave, "Tercero", isw),
        ]
        self.espacios[:] = [Aula("A", 35, 101), Laboratorio("B", 40, 201, 25), Aula("A", 40, 102)]
        self.materias[:] = [
            Materia("Programacion Estructurada", "PRG-101", 4, isw, True),
            Materia("Base de Datos", "BDD-102", 4, isw, True),
            Materia("Redes de Computadoras", "RED-103", 3, isw, False),
        ]
        self.cursos[:] = []
        self.horarios[:] = []
        self.servicio.asignaciones[:] = []
        self.guardar()
