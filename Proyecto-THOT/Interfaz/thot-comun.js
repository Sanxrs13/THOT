/* Utilidades compartidas por todas las paginas de THOT.
   Hablan con el servidor Flask (Servidor.py) a traves de /api/... */
const THOT = (() => {
  let sesion = null;

  async function api(url, opciones = {}) {
    const op = { method: opciones.method || "GET", headers: {}, credentials: "same-origin" };
    if (opciones.body !== undefined) {
      op.headers["Content-Type"] = "application/json";
      op.body = JSON.stringify(opciones.body);
    }
    let resp;
    try { resp = await fetch(url, op); }
    catch (e) { throw new Error("No hay conexión con el servidor. ¿Está ejecutando Servidor.py?"); }
    let datos = null;
    try { datos = await resp.json(); } catch (e) { /* respuesta sin cuerpo */ }
    if (resp.status === 401 && !url.startsWith("/api/login")) {
      location.href = "THOT - IincioSesion.html";
      throw new Error("Debe iniciar sesión");
    }
    if (!resp.ok) throw new Error((datos && datos.error) || ("Error " + resp.status));
    return datos;
  }

  const get = url => api(url);
  const post = (url, body) => api(url, { method: "POST", body });
  const put = (url, body) => api(url, { method: "PUT", body });
  const del = url => api(url, { method: "DELETE" });

  function puede(modulo, accion = "ver") {
    return !!(sesion && (sesion.permisos[modulo] || []).includes(accion));
  }

  /* Carga la sesion, rellena la barra lateral y oculta lo que el rol no puede usar. */
  async function iniciar(modulo) {
    sesion = await get("/api/sesion");
    const u = document.querySelector(".usuario");
    if (u) {
      u.querySelector(".avatar").textContent = (sesion.nombre[0] || "U").toUpperCase();
      u.querySelector("strong").textContent = sesion.nombre;
      u.querySelector("small").textContent = sesion.rol;
    }
    document.querySelectorAll(".navegacion a[data-modulo]").forEach(a => {
      if (!(sesion.permisos[a.dataset.modulo] || []).length) a.hidden = true;
    });
    const salir = document.getElementById("cerrar-sesion");
    if (salir) salir.addEventListener("click", async e => {
      e.preventDefault();
      try { await post("/api/logout", {}); } catch (err) { /* da igual */ }
      location.href = "THOT - IincioSesion.html";
    });
    if (modulo && !puede(modulo, "gestionar")) {
      document.body.classList.add("solo-lectura");
      document.querySelectorAll(".solo-gestion").forEach(el => { el.hidden = true; });
    }
    return sesion;
  }

  /* Llena un <select> con una lista de objetos. */
  function llenarSelect(select, lista, valor, texto, placeholder, seleccionado = "") {
    select.innerHTML = "";
    const base = document.createElement("option");
    base.value = ""; base.textContent = placeholder;
    select.append(base);
    lista.forEach(x => {
      const o = document.createElement("option");
      o.value = valor(x); o.textContent = texto(x);
      select.append(o);
    });
    select.value = seleccionado;
    if (select.value !== seleccionado) select.value = "";
  }

  function boton(clase, texto) {
    const b = document.createElement("button");
    b.type = "button"; b.className = clase; b.textContent = texto;
    return b;
  }

  /* Fila de lista con punto, titulo, detalle y botones editar/eliminar. */
  function fila(claseFila, claseInfo, titulo, detalle, conAcciones) {
    const li = document.createElement("li");
    li.className = claseFila;
    const info = document.createElement("div"); info.className = claseInfo;
    const punto = document.createElement("span"); punto.className = "punto";
    const datos = document.createElement("div");
    const t = document.createElement("strong"); t.textContent = titulo;
    const d = document.createElement("small"); d.textContent = detalle;
    datos.append(t, d); info.append(punto, datos); li.append(info);
    if (conAcciones) {
      const acciones = document.createElement("div"); acciones.className = "acciones-item";
      acciones.append(boton("btn-editar", "Editar"), boton("btn-eliminar", "Eliminar"));
      li.append(acciones);
    }
    return li;
  }

  function error(e) { alert(e.message || e); }

  return { api, get, post, put, del, puede, iniciar, llenarSelect, boton, fila, error,
           get sesion() { return sesion; } };
})();
