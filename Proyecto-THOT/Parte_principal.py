from abc import ABC, abstractmethod
import hashlib
import hmac
import inspect
import os
import re
import uuid


# [O] busca todas las subclases concretas (no abstractas) de una clase base
def subclases_concretas(base):
    encontradas = []
    nivel = [base]
    while nivel:
        siguiente = []
        for clase in nivel:
            for sub in clase.__subclasses__():
                if sub not in encontradas and sub not in siguiente:
                    siguiente.append(sub)
        encontradas.extend(siguiente)
        nivel = siguiente
    return [c for c in encontradas if not inspect.isabstract(c)]


# ---------------------------------------------------------------------------
# Contrasenas: nunca se guardan en texto plano
# ---------------------------------------------------------------------------
def crear_hash(contrasena: str) -> str:
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, 120_000)
    return sal.hex() + "$" + h.hex()


def verificar_hash(contrasena: str, guardado: str) -> bool:
    try:
        sal_hex, h_hex = guardado.split("$")
        h = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), bytes.fromhex(sal_hex), 120_000)
        return hmac.compare_digest(h.hex(), h_hex)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Estructura academica: Facultad -> Carrera
# ---------------------------------------------------------------------------
class Facultad:
    def __init__(self, nombre: str, codigo: str):
        if not nombre.strip():
            raise ValueError("Debe ingresar el nombre de la facultad")
        if not codigo.strip():
            raise ValueError("Debe ingresar el codigo de la facultad")
        self.nombre = nombre.strip()
        self.codigo = codigo.strip()

    def datos(self):
        return {"nombre": self.nombre, "codigo": self.codigo}

    @classmethod
    def desde_datos(cls, d, datos=None):
        return cls(d["nombre"], d["codigo"])


class Carrera:
    def __init__(self, nombre: str, codigo: str, facultad: Facultad):
        if not nombre.strip():
            raise ValueError("Debe ingresar el nombre de la carrera")
        if not codigo.strip():
            raise ValueError("Debe ingresar el codigo de la carrera")
        if not isinstance(facultad, Facultad):
            raise ValueError("Debe seleccionar una facultad registrada")
        self.nombre = nombre.strip()
        self.codigo = codigo.strip()
        self.facultad = facultad

    def datos(self):
        return {"nombre": self.nombre, "codigo": self.codigo, "facultad": self.facultad.codigo}

    @classmethod
    def desde_datos(cls, d, datos=None):
        return cls(d["nombre"], d["codigo"], _buscar(datos["facultades"], "codigo", d["facultad"]))


def _buscar(lista, atributo, valor):
    for x in lista:
        if getattr(x, atributo) == valor:
            return x
    raise KeyError(f"{atributo}={valor!r} no existe")


# ---------------------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------------------
NIVELES = ["Primero", "Segundo", "Tercero", "Cuarto", "Quinto",
           "Sexto", "Séptimo", "Octavo", "Noveno", "Décimo"]
DOMINIO_CORREO = "uleam.com"


def _sin_tilde(texto: str) -> str:
    return texto.strip().lower().translate(str.maketrans("áéíóú", "aeiou"))


def normalizar_nivel(nivel: str) -> str:
    """Acepta 'Septimo' o 'séptimo' y devuelve la forma oficial ('Séptimo'); '' si no existe."""
    for n in NIVELES:
        if _sin_tilde(n) == _sin_tilde(nivel):
            return n
    return ""


# [S] Usuario solo guarda y valida los datos de una persona
class Usuario(ABC):
    def __init__(self, cedula: str, nombre: str, contrasena: str, nivel: str,
                 carrera: Carrera, clave_hash: str = None):
        cedula = str(cedula).strip()
        if not re.fullmatch(r"\d{10}", cedula):
            raise ValueError("La cedula debe tener exactamente 10 digitos")
        if not nombre.strip():
            raise ValueError("Debe ingresar un nombre")
        if not normalizar_nivel(nivel):
            raise ValueError("Nivel no valido")
        if not isinstance(carrera, Carrera):
            raise ValueError("Debe seleccionar una carrera registrada")
        if clave_hash is None:
            if len(contrasena.strip()) < 6:
                raise ValueError("La contrasena debe tener al menos 6 caracteres")
            clave_hash = crear_hash(contrasena.strip())
        self.cedula = cedula
        self.nombre = nombre.strip()
        self.nivel = normalizar_nivel(nivel)
        self.carrera = carrera
        self.__clave_hash = clave_hash

    # el correo se genera a partir de la cedula: 1315155661@uleam.com
    @property
    def correo(self):
        return f"{self.cedula}@{DOMINIO_CORREO}"

    @property
    def facultad(self):
        return self.carrera.facultad

    def validar_contrasena(self, contrasena):
        return verificar_hash(contrasena, self.__clave_hash)

    def clave_hash(self):
        return self.__clave_hash

    @property
    def tipo(self):
        return type(self).__name__

    # metodo abstracto: cada tipo de usuario define su rol
    @abstractmethod
    def rol(self) -> str:
        pass

    def __str__(self):
        return f"{self.nombre} ({self.rol()})"

    # [O][L]
    def datos(self):
        return {"tipo": self.tipo, "cedula": self.cedula, "nombre": self.nombre,
                "nivel": self.nivel, "carrera": self.carrera.codigo,
                "clave_hash": self.__clave_hash}

    @classmethod
    def desde_datos(cls, d, datos=None):
        carrera = _buscar(datos["carreras"], "codigo", d["carrera"])
        return cls(d["cedula"], d["nombre"], "", d["nivel"], carrera, clave_hash=d["clave_hash"])


class Estudiante(Usuario):
    def rol(self):
        return "estudiante"


class Docente(Usuario):
    def rol(self):
        return "docente"


class Director(Usuario):
    def rol(self):
        return "director"


class Presidente(Usuario):
    def rol(self):
        return "presidente"


# herencia multiple: el administrador reune lo de director y presidente
class Administrador(Director, Presidente):
    def rol(self):
        return f"administrador ({Director.rol(self)} y {Presidente.rol(self)})"


# [S]
class ServicioAutenticacion:
    def autenticar(self, usuarios, identificador, clave):
        """El usuario puede escribir su cedula o su correo institucional."""
        ident = identificador.strip().lower()
        for u in usuarios:
            if ident in (u.cedula, u.correo.lower()) and u.validar_contrasena(clave):
                return u
        return None


# ---------------------------------------------------------------------------
# Espacios de estudio
# ---------------------------------------------------------------------------
# [I]
class EspacioEstudio(ABC):
    def __init__(self, codigo_edificio: str, capacidad: int):
        if not codigo_edificio.strip():
            raise ValueError("Debe ingresar el codigo del edificio")
        if capacidad <= 29:
            raise ValueError("La capacidad debe ser mayor que 29")
        self.codigo_edificio = codigo_edificio.strip()
        self.capacidad = capacidad

    @abstractmethod
    def descripcion(self) -> str:
        pass

    @abstractmethod
    def admite(self, materia) -> bool:
        pass

    @property
    def tipo(self):
        return type(self).__name__

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    def datos(self):
        return {"tipo": self.tipo, "codigo_edificio": self.codigo_edificio,
                "capacidad": self.capacidad}

    @classmethod
    @abstractmethod
    def desde_datos(cls, d, datos=None):
        pass


class Aula(EspacioEstudio):
    def __init__(self, codigo_edificio, capacidad, codigo_aula: int):
        if not isinstance(codigo_aula, int) or codigo_aula <= 99:
            raise ValueError("El codigo del aula tiene que ser de 3 digitos")
        super().__init__(codigo_edificio, capacidad)
        self.codigo_aula = codigo_aula

    @property
    def id(self):
        return f"{self.codigo_edificio}-{self.codigo_aula}"

    def descripcion(self):
        return f"Aula {self.codigo_aula} del edificio {self.codigo_edificio} (capacidad {self.capacidad})"

    def admite(self, materia):
        return not materia.requiere_laboratorio()

    def datos(self):
        d = super().datos()
        d["codigo_aula"] = self.codigo_aula
        return d

    @classmethod
    def desde_datos(cls, d, datos=None):
        return cls(d["codigo_edificio"], d["capacidad"], d["codigo_aula"])


# [L]
class Laboratorio(Aula):
    def __init__(self, codigo_edificio, capacidad, codigo_aula, numero_maquinas: int):
        if numero_maquinas < (capacidad / 2):
            raise ValueError("Debe haber al menos la mitad de maquinas respecto a la capacidad")
        super().__init__(codigo_edificio, capacidad, codigo_aula)
        self.numero_maquinas = numero_maquinas

    def descripcion(self):
        return f"Laboratorio {self.codigo_aula} del edificio {self.codigo_edificio} ({self.numero_maquinas} maquinas)"

    def admite(self, materia):
        return True

    def datos(self):
        d = super().datos()
        d["numero_maquinas"] = self.numero_maquinas
        return d

    @classmethod
    def desde_datos(cls, d, datos=None):
        return cls(d["codigo_edificio"], d["capacidad"], d["codigo_aula"], d["numero_maquinas"])


# ---------------------------------------------------------------------------
# Materia, curso, horario
# ---------------------------------------------------------------------------
class Materia:
    def __init__(self, nombre: str, codigo: str, creditos: int, carrera: Carrera, usar_lab: bool = False):
        if not nombre.strip():
            raise ValueError("Debe ingresar un nombre")
        if not codigo.strip():
            raise ValueError("Debe ingresar un codigo")
        if not isinstance(creditos, int) or isinstance(creditos, bool) or not 1 <= creditos <= 20:
            raise ValueError("Los creditos deben ser un numero entre 1 y 20")
        if not isinstance(carrera, Carrera):
            raise ValueError("Debe seleccionar una carrera registrada")
        if not isinstance(usar_lab, bool):
            raise ValueError("Debe especificar si utiliza o no laboratorio")
        self.nombre = nombre.strip()
        self.codigo = codigo.strip()
        self.creditos = creditos
        self.carrera = carrera
        self.usar_lab = usar_lab

    def requiere_laboratorio(self):
        return self.usar_lab

    def datos(self):
        return {"nombre": self.nombre, "codigo": self.codigo, "creditos": self.creditos,
                "carrera": self.carrera.codigo, "usar_lab": self.usar_lab}

    @classmethod
    def desde_datos(cls, d, datos=None):
        carrera = _buscar(datos["carreras"], "codigo", d["carrera"])
        return cls(d["nombre"], d["codigo"], d["creditos"], carrera, d["usar_lab"])


PARALELOS = ["A", "B", "C"]


class Curso:
    def __init__(self, carrera: Carrera, paralelo: str, semestre: str, periodo: str):
        if not isinstance(carrera, Carrera):
            raise ValueError("Debe seleccionar una carrera")
        if not paralelo.strip():
            raise ValueError("Debe ingresar el paralelo")
        if not normalizar_nivel(semestre):
            raise ValueError("Semestre no valido")
        if not periodo.strip():
            raise ValueError("Debe ingresar el periodo")
        self.carrera = carrera
        self.paralelo = paralelo.strip().upper()
        self.semestre = normalizar_nivel(semestre)
        self.periodo = periodo.strip()

    def clave(self):
        return (self.carrera.codigo, self.paralelo, self.semestre, self.periodo)

    def datos(self):
        return {"carrera": self.carrera.codigo, "paralelo": self.paralelo,
                "semestre": self.semestre, "periodo": self.periodo}

    @classmethod
    def desde_datos(cls, d, datos=None):
        carrera = _buscar(datos["carreras"], "codigo", d["carrera"])
        return cls(carrera, d["paralelo"], d["semestre"], d["periodo"])


DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


class Horario:
    def __init__(self, periodo: str, dia: str, hora_inicio: int, hora_fin: int):
        if dia not in DIAS:
            raise ValueError("Dia no valido")
        if hora_inicio < 7:
            raise ValueError("Las clases no pueden empezar antes de las 7:00")
        if hora_fin > 19:
            raise ValueError("Las clases no pueden terminar despues de las 19:00")
        if hora_fin <= hora_inicio:
            raise ValueError("La hora de fin debe ser mayor que la de inicio")
        self.periodo = periodo.strip()
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin

    def duracion(self):
        return self.hora_fin - self.hora_inicio

    def clave(self):
        return (self.periodo, self.dia, self.hora_inicio, self.hora_fin)

    def se_cruza_con(self, otro):
        return (self.periodo == otro.periodo
                and self.dia == otro.dia
                and self.hora_inicio < otro.hora_fin
                and otro.hora_inicio < self.hora_fin)

    def datos(self):
        return {"periodo": self.periodo, "dia": self.dia,
                "hora_inicio": self.hora_inicio, "hora_fin": self.hora_fin}

    @classmethod
    def desde_datos(cls, d, datos=None):
        return cls(d["periodo"], d["dia"], d["hora_inicio"], d["hora_fin"])


# ---------------------------------------------------------------------------
# Asignaciones
# ---------------------------------------------------------------------------
# [I][D]
class Notificador(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, mensaje: str):
        pass


# [O]
class NotificadorConsola(Notificador):
    def enviar(self, destinatario, mensaje):
        print(f"[correo a {destinatario}] {mensaje}")


class Asignacion:
    def __init__(self, docente: Docente, materia: Materia, curso: Curso,
                 horario: Horario, espacio: EspacioEstudio, id: str = None):
        if not isinstance(docente, Docente):
            raise ValueError("Debe asignar un docente")
        if not espacio.admite(materia):
            raise ValueError("El espacio no es adecuado para la materia (requiere laboratorio)")
        self.id = id or uuid.uuid4().hex[:8]
        self.docente = docente
        self.materia = materia
        self.curso = curso
        self.horario = horario
        self.espacio = espacio


# [I][O]
class ReglaAsignacion(ABC):
    @abstractmethod
    def validar(self, nueva, existentes):
        """Lanza ValueError si la asignacion nueva no es valida."""


class MateriaDeLaCarrera(ReglaAsignacion):
    def validar(self, nueva, existentes):
        if nueva.materia.carrera is not nueva.curso.carrera:
            raise ValueError("La materia no pertenece a la carrera del curso")


class SinCruceDeEspacio(ReglaAsignacion):
    def validar(self, nueva, existentes):
        for a in existentes:
            if a.espacio is nueva.espacio and a.horario.se_cruza_con(nueva.horario):
                raise ValueError("Cruce de horario: el espacio ya esta ocupado en ese horario")


class SinCruceDeDocente(ReglaAsignacion):
    def validar(self, nueva, existentes):
        for a in existentes:
            if a.docente is nueva.docente and a.horario.se_cruza_con(nueva.horario):
                raise ValueError("Cruce de horario: el docente ya tiene otra asignacion en ese horario")


class SinCruceDeCurso(ReglaAsignacion):
    def validar(self, nueva, existentes):
        for a in existentes:
            if a.curso is nueva.curso and a.horario.se_cruza_con(nueva.horario):
                raise ValueError("Cruce de horario: el curso ya tiene otra materia en ese horario")


# [S][D][O]
class ServicioAsignaciones:
    def __init__(self, notificador: Notificador, reglas=None):
        self.__notificador = notificador
        self.__reglas = list(reglas) if reglas is not None else [
            MateriaDeLaCarrera(), SinCruceDeEspacio(), SinCruceDeDocente(), SinCruceDeCurso()]
        self.asignaciones = []

    def validar(self, nueva, ignorar=None):
        existentes = [a for a in self.asignaciones if a is not ignorar]
        for regla in self.__reglas:
            regla.validar(nueva, existentes)

    def asignar(self, docente, materia, curso, horario, espacio):
        nueva = Asignacion(docente, materia, curso, horario, espacio)
        self.validar(nueva)
        self.asignaciones.append(nueva)
        self.__notificador.enviar(
            docente.correo,
            f"Se le asigno {materia.nombre} en {espacio.descripcion()} "
            f"({horario.dia} {horario.hora_inicio}:00 a {horario.hora_fin}:00)")
        return nueva

    def eliminar(self, id):
        for a in self.asignaciones:
            if a.id == id:
                self.asignaciones.remove(a)
                return a
        return None
