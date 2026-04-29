import { useEffect, useMemo, useState } from "react";

const API = "http://127.0.0.1:8000/api";
const views = ["dashboard", "alumno", "encuesta", "predicciones", "notas", "expediente"];
const encuestaKeys = [
  "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
  "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
];

const encuestaKeysA = encuestaKeys.filter((k) => k.startsWith("A"));
const encuestaKeysB = encuestaKeys.filter((k) => k.startsWith("B"));

const encuestaLabels = {
  A1: "No presta atención a detalles", A2: "Dificultades mantener atención", A3: "No escucha cuando se le habla",
  A4: "No sigue instrucciones", A5: "Dificultades organizar tareas", A6: "Evita tareas que requieren esfuerzo",
  A7: "Pierde objetos necesarios", A8: "Se distrae fácilmente", A9: "Descuidado en actividades diarias",
  A10: "Lentitud o falta de persistencia", B1: "Mueve manos o pies en exceso", B2: "Dificultad permanecer sentado",
  B3: "Corre o trepa inapropiadamente", B4: "Dificultad jugar tranquilo", B5: "Está \"en marcha\" constantemente",
  B6: "Habla en exceso", B7: "Responde antes de terminar pregunta", B8: "Dificultad esperar su turno",
  B9: "Interrumpe o se inmiscuye", B10: "Reacciones explosivas",
};

const encuestaEscalaOpciones = [
  { value: "0", label: "0 - Nunca" },
  { value: "1", label: "1 - Algunas veces" },
  { value: "2", label: "2 - Bastantes veces" },
  { value: "3", label: "3 - Siempre" },
];

const encuestaLeyendaAtencion =
  "0: Nunca | 1: Algunas veces | 2: Bastantes veces | 3: Siempre";

const ASIGNATURAS_VALIDAS = [
  "Matemática",
  "Comunicación",
  "Ciencias Sociales",
  "Ciencia y Tecnología",
  "Inglés",
  "Educación Física",
  "Arte",
  "Religión",
];

function normalizarCalificacionLiteral(texto) {
  const t = String(texto).trim().toUpperCase();
  if (t === "AD") return "AD";
  if (t === "A" || t === "B" || t === "C") return t;
  return null;
}

const evalSocialLabels = {
  c1: "C1: Asistencia y Participación Familiar",
  c2: "C2: Estabilidad Familiar",
  c3: "C3: Soporte Académico",
  c4: "C4: Cuidado y Atención",
  c5: "C5: Integración de Pares",
  c6: "C6: Riesgo de Aislamiento",
  c7: "C7: Conducta Prosocial",
  c8: "C8: Vulnerabilidad Social",
};

const socialSelectOptions = [
  { value: "0", label: "0 - Ningún Problema" },
  { value: "1", label: "1 - Leve" },
  { value: "2", label: "2 - Moderado" },
  { value: "3", label: "3 - Grave" },
];

const initialAlumno = {
  nombre: "",
  apellido: "",
  contacto_emergente: "",
  edad: "",
  grado: "",
  anio_cursada: "2025",
  c1: "0", c2: "0", c3: "0", c4: "0", c5: "0", c6: "0", c7: "0", c8: "0",
};

const initialEncuesta = Object.fromEntries([["alumno", ""], ...encuestaKeys.map((k) => [k, "0"])]);
const initialNota = { alumno: "", asignatura: "", nota: "" };
const initialExpediente = { alumno: "", nivel_preocupacion: "3", archivo_pdf: null };

function socialToCondicion(maxSocial) {
  if (maxSocial <= 0) return "NINGUNA";
  if (maxSocial === 1) return "LEVE";
  if (maxSocial === 2) return "MODERADA";
  return "GRAVE";
}

async function req(path, options = {}) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return null;
  return res.json();
}

export default function App() {
  const [auth, setAuth] = useState({ usuario: "", password: "", logged: false });
  const [activeView, setActiveView] = useState("dashboard");
  const [status, setStatus] = useState({ msg: "", error: false });
  const [alumnos, setAlumnos] = useState([]);

  const [alumnoForm, setAlumnoForm] = useState(initialAlumno);
  const [encuestaForm, setEncuestaForm] = useState(initialEncuesta);
  const [notaForm, setNotaForm] = useState(initialNota);
  const [expForm, setExpForm] = useState(initialExpediente);
  const [predAlumno, setPredAlumno] = useState("");
  const [predicciones, setPredicciones] = useState([]);
  const [alumnoFormError, setAlumnoFormError] = useState("");
  const [encuestaStatus, setEncuestaStatus] = useState({ msg: "", error: false });
  const [notasModoLista, setNotasModoLista] = useState("actuales");
  const [notasModoCarga, setNotasModoCarga] = useState("individual");
  const [notasStatus, setNotasStatus] = useState({ msg: "", error: false });
  const [historicoNotas, setHistoricoNotas] = useState([]);
  const [archivoMasivo, setArchivoMasivo] = useState(null);

  const goToView = (v) => {
    setActiveView(v);
    setStatus({ msg: "", error: false });
    setAlumnoFormError("");
    setEncuestaStatus({ msg: "", error: false });
    setNotasStatus({ msg: "", error: false });
  };

  const alumnoOptions = useMemo(
    () => alumnos.map((a) => ({ value: a.id, label: `${a.nombre} ${a.apellido} - ${a.grado}` })),
    [alumnos]
  );

  async function loadAlumnos() {
    const data = await req("/alumnos/");
    setAlumnos(data);
  }

  async function loadPredicciones(alumnoId) {
    if (!alumnoId) return setPredicciones([]);
    const data = await req(`/predicciones/?alumno=${alumnoId}`);
    setPredicciones(data);
  }

  useEffect(() => {
    if (auth.logged) {
      loadAlumnos().catch((e) => setStatus({ msg: e.message, error: true }));
    }
  }, [auth.logged]);

  useEffect(() => {
    if (!auth.logged || activeView !== "notas" || notasModoLista !== "historico") {
      return;
    }
    const id = notaForm.alumno;
    if (!id) {
      setHistoricoNotas([]);
      return;
    }
    let cancelled = false;
    req(`/notas/?alumno=${id}`)
      .then((data) => {
        if (!cancelled) {
          setHistoricoNotas(Array.isArray(data) ? data : []);
          setNotasStatus({ msg: "", error: false });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setHistoricoNotas([]);
          setNotasStatus({
            msg: err.message || "Error al cargar el histórico de notas.",
            error: true,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [auth.logged, activeView, notasModoLista, notaForm.alumno]);

  const notify = (msg, error = false) => setStatus({ msg, error });

  const onLogin = (e) => {
    e.preventDefault();
    if (auth.usuario === "admin" && auth.password === "admin123") {
      setAuth((s) => ({ ...s, logged: true }));
      notify("Sesión iniciada correctamente.");
    } else {
      notify("Credenciales inválidas.", true);
    }
  };

  const submitAlumno = async (e) => {
    e.preventDefault();
    setAlumnoFormError("");
    const socialVals = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"].map((k) => Number(alumnoForm[k]));
    const body = {
      nombre: alumnoForm.nombre,
      apellido: alumnoForm.apellido,
      contacto_emergente: alumnoForm.contacto_emergente,
      edad: Number(alumnoForm.edad),
      grado: alumnoForm.grado,
      anio_cursada: Number(alumnoForm.anio_cursada),
      condicion_social: socialToCondicion(Math.max(...socialVals)),
    };
    try {
      await req("/alumnos/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setAlumnoForm(initialAlumno);
      await loadAlumnos();
      notify("Alumno registrado.");
    } catch (err) {
      setAlumnoFormError(err.message || "No se pudo registrar el alumno.");
    }
  };

  const submitEncuesta = async (e) => {
    e.preventDefault();
    setEncuestaStatus({ msg: "", error: false });
    const body = { alumno: Number(encuestaForm.alumno) };
    encuestaKeys.forEach((k) => { body[k] = Number(encuestaForm[k]); });
    try {
      await req("/encuestas/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setEncuestaStatus({ msg: "Encuesta guardada correctamente.", error: false });
    } catch (err) {
      setEncuestaStatus({
        msg: err.message || "No se pudo guardar la encuesta.",
        error: true,
      });
    }
  };

  const submitNota = async (e) => {
    e.preventDefault();
    setNotasStatus({ msg: "", error: false });
    const asignatura = notaForm.asignatura.trim();
    if (!ASIGNATURAS_VALIDAS.includes(asignatura)) {
      setNotasStatus({
        msg: `Asignatura no válida. Use exactamente: ${ASIGNATURAS_VALIDAS.join(", ")}.`,
        error: true,
      });
      return;
    }
    const calificacion_literal = normalizarCalificacionLiteral(notaForm.nota);
    if (!calificacion_literal) {
      setNotasStatus({
        msg: "La nota debe ser AD, A, B o C.",
        error: true,
      });
      return;
    }
    try {
      await req("/notas/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alumno: Number(notaForm.alumno),
          asignatura,
          calificacion_literal,
        }),
      });
      setNotaForm({ ...notaForm, asignatura: "", nota: "" });
      setNotasStatus({ msg: "Nota registrada correctamente.", error: false });
    } catch (err) {
      setNotasStatus({
        msg: err.message || "No se pudo registrar la nota.",
        error: true,
      });
    }
  };

  const submitMasivaCsv = async (e) => {
    e.preventDefault();
    setNotasStatus({ msg: "", error: false });
    if (!archivoMasivo) {
      setNotasStatus({ msg: "Selecciona un archivo CSV.", error: true });
      return;
    }
    const text = await archivoMasivo.text();
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length < 2) {
      setNotasStatus({
        msg: "El CSV debe tener encabezado y al menos una fila de datos.",
        error: true,
      });
      return;
    }
    let ok = 0;
    const errores = [];
    for (let i = 1; i < lines.length; i++) {
      const partes = lines[i].split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
      const [alumnoId, asig, notaVal] = partes;
      if (!alumnoId || !asig || notaVal === undefined) {
        errores.push(`Fila ${i + 1}: datos incompletos`);
        continue;
      }
      if (!ASIGNATURAS_VALIDAS.includes(asig)) {
        errores.push(`Fila ${i + 1}: asignatura no válida`);
        continue;
      }
      const lit = normalizarCalificacionLiteral(notaVal);
      if (!lit) {
        errores.push(`Fila ${i + 1}: calificación debe ser AD, A, B o C`);
        continue;
      }
      try {
        await req("/notas/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            alumno: Number(alumnoId),
            asignatura: asig,
            calificacion_literal: lit,
          }),
        });
        ok += 1;
      } catch (err) {
        errores.push(`Fila ${i + 1}: ${err.message || "error"}`);
      }
    }
    setArchivoMasivo(null);
    await loadAlumnos();
    if (errores.length) {
      setNotasStatus({
        msg: `Procesadas ${ok} filas. Errores: ${errores.slice(0, 5).join("; ")}${errores.length > 5 ? "…" : ""}`,
        error: ok === 0,
      });
    } else {
      setNotasStatus({ msg: `Carga masiva: ${ok} nota(s) registrada(s).`, error: false });
    }
  };

  const submitExpediente = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("alumno", expForm.alumno);
    fd.append("nivel_preocupacion", expForm.nivel_preocupacion);
    if (expForm.archivo_pdf) fd.append("archivo_pdf", expForm.archivo_pdf);
    await req("/expedientes/", { method: "POST", body: fd });
    notify("Expediente guardado.");
  };

  const generarPrediccion = async () => {
    if (!predAlumno) return notify("Selecciona un alumno para generar predicción.", true);
    await req("/predicciones/generar/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alumno: Number(predAlumno) }),
    });
    await loadPredicciones(predAlumno);
    notify("Predicción generada.");
  };

  if (!auth.logged) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <h1>Sistema de Predicción Educativa</h1>
          <p>Inicia sesión</p>
          <form onSubmit={onLogin}>
            <label>Usuario</label>
            <input value={auth.usuario} onChange={(e) => setAuth({ ...auth, usuario: e.target.value })} required />
            <label>Contraseña</label>
            <input type="password" value={auth.password} onChange={(e) => setAuth({ ...auth, password: e.target.value })} required />
            <button type="submit">Iniciar Sesión</button>
          </form>
          <small>Usuario: <strong>admin</strong> | Contraseña: <strong>admin123</strong></small>
          {status.msg && <p className="status" style={{ color: status.error ? "#d62828" : "#14732b" }}>{status.msg}</p>}
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h2>Sistema</h2>
          <span>admin</span>
        </div>
        <nav>
          {views.map((v) => {
            const labels = {
              dashboard: "Dashboard",
              alumno: "Registrar Alumno",
              encuesta: "Encuesta",
              predicciones: "Predicciones",
              notas: "Subir Notas",
              expediente: "Expediente Psicológico",
            };
            return (
              <button
                key={v}
                type="button"
                className={activeView === v ? "nav-active" : ""}
                onClick={() => goToView(v)}
              >
                {labels[v]}
              </button>
            );
          })}
          <button type="button" className="danger" onClick={() => window.location.reload()}>Cerrar Sesión</button>
        </nav>
      </aside>
      <section className="content">
        {activeView === "dashboard" && (
          <article className="panel">
            <h2>Dashboard del Estudiante</h2>
            <label>Selecciona un Estudiante</label>
            <select>
              <option value="">-- Selecciona --</option>
              {alumnoOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </article>
        )}

        {activeView === "alumno" && (
          <>
            <h1 className="page-title">Registrar Nuevo Alumno</h1>
            <article className="panel">
              <form className="grid" onSubmit={submitAlumno}>
                <div className="field-group">
                  <label htmlFor="alumno-nombre">Nombre</label>
                  <input
                    id="alumno-nombre"
                    type="text"
                    value={alumnoForm.nombre}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, nombre: e.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="alumno-apellido">Apellido</label>
                  <input
                    id="alumno-apellido"
                    type="text"
                    value={alumnoForm.apellido}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, apellido: e.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="alumno-contacto">Contacto de Emergencia</label>
                  <input
                    id="alumno-contacto"
                    type="text"
                    value={alumnoForm.contacto_emergente}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, contacto_emergente: e.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="alumno-edad">Edad</label>
                  <input
                    id="alumno-edad"
                    type="number"
                    min={5}
                    max={30}
                    value={alumnoForm.edad}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, edad: e.target.value })}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="alumno-grado">Grado</label>
                  <select
                    id="alumno-grado"
                    value={alumnoForm.grado}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, grado: e.target.value })}
                    required
                  >
                    <option value="">Selecciona (ej. 10mo)</option>
                    <option value="1°">1°</option>
                    <option value="2°">2°</option>
                    <option value="3°">3°</option>
                    <option value="4°">4°</option>
                    <option value="5°">5°</option>
                    <option value="10mo">10mo</option>
                    <option value="11vo">11vo</option>
                    <option value="12vo">12vo</option>
                  </select>
                </div>
                <div className="field-group">
                  <label htmlFor="alumno-anio">Año de cursada</label>
                  <input
                    id="alumno-anio"
                    type="number"
                    placeholder="2025"
                    value={alumnoForm.anio_cursada}
                    onChange={(e) => setAlumnoForm({ ...alumnoForm, anio_cursada: e.target.value })}
                    required
                  />
                </div>

                <div className="form-section full">
                  <h3 className="form-section__title">Evaluación Social (0-3)</h3>
                  <p className="form-legend">
                    0: Ningún Problema | 1: Leve | 2: Moderado | 3: Grave
                  </p>
                  <div className="grid" style={{ marginTop: 8 }}>
                    {["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"].map((c) => (
                      <div key={c} className="field-group">
                        <label htmlFor={`alumno-${c}`}>{evalSocialLabels[c]}</label>
                        <select
                          id={`alumno-${c}`}
                          value={alumnoForm[c]}
                          onChange={(e) => setAlumnoForm({ ...alumnoForm, [c]: e.target.value })}
                        >
                          {socialSelectOptions.map((opt) => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                {alumnoFormError && (
                  <div className="alert-error" role="alert">
                    {alumnoFormError}
                  </div>
                )}
                <button className="full" type="submit">Registrar Alumno</button>
              </form>
            </article>
          </>
        )}

        {activeView === "encuesta" && (
          <div className="encuesta-layout">
            <h1 className="page-title">Encuesta Psicoeducativa</h1>
            <article className="panel panel-encuesta">
              <form className="grid encuesta-form" onSubmit={submitEncuesta}>
                <div className="field-group full">
                  <label htmlFor="encuesta-alumno">Selecciona Estudiante</label>
                  <select
                    id="encuesta-alumno"
                    value={encuestaForm.alumno}
                    onChange={(e) => setEncuestaForm({ ...encuestaForm, alumno: e.target.value })}
                    required
                  >
                    <option value="">-- Selecciona --</option>
                    {alumnoOptions.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-section full encuesta-bloque">
                  <h3 className="form-section__title">Atención (A1-A10)</h3>
                  <p className="form-legend">{encuestaLeyendaAtencion}</p>
                  <div className="grid encuesta-grid">
                    {encuestaKeysA.map((k) => (
                      <div key={k} className="field-group">
                        <label htmlFor={`encuesta-${k}`}>
                          {k}: {encuestaLabels[k]}
                        </label>
                        <select
                          id={`encuesta-${k}`}
                          value={encuestaForm[k]}
                          onChange={(e) => setEncuestaForm({ ...encuestaForm, [k]: e.target.value })}
                        >
                          {encuestaEscalaOpciones.map((opt) => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="form-section full encuesta-bloque">
                  <h3 className="form-section__title">Hiperactividad/Impulsividad (B1-B10)</h3>
                  <div className="grid encuesta-grid">
                    {encuestaKeysB.map((k) => (
                      <div key={k} className="field-group">
                        <label htmlFor={`encuesta-${k}`}>
                          {k}: {encuestaLabels[k]}
                        </label>
                        <select
                          id={`encuesta-${k}`}
                          value={encuestaForm[k]}
                          onChange={(e) => setEncuestaForm({ ...encuestaForm, [k]: e.target.value })}
                        >
                          {encuestaEscalaOpciones.map((opt) => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                {encuestaStatus.msg && (
                  <div
                    className={encuestaStatus.error ? "alert-error" : "alert-success"}
                    role="status"
                  >
                    {encuestaStatus.msg}
                  </div>
                )}
                <button className="full" type="submit">Guardar Encuesta</button>
              </form>
            </article>
          </div>
        )}

        {activeView === "predicciones" && (
          <article className="panel">
            <h2>Historial de Predicciones</h2>
            <div className="row">
              <select
                value={predAlumno}
                onChange={(e) => {
                  const id = e.target.value;
                  setPredAlumno(id);
                  loadPredicciones(id).catch(() => notify("Error al cargar predicciones", true));
                }}
              >
                <option value="">-- Selecciona --</option>
                {alumnoOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              <button type="button" onClick={generarPrediccion}>Generar Predicción</button>
            </div>
            {predicciones.map((p) => (
              <div key={p.id} className="card">
                <strong>{p.alumno_nombre ?? "Alumno"}</strong><br />
                <b>Predicción de Notas:</b> {p.prediccion_notas}<br />
                <b>Condiciones Psicoeducativas:</b> {p.condiciones_psicoeducativas}
              </div>
            ))}
          </article>
        )}

        {activeView === "notas" && (
          <div className="notas-layout">
            <h1 className="page-title">Subir/Actualizar Notas</h1>
            <article className="panel panel-notas">
              <div className="toggle-row">
                <button
                  type="button"
                  className={notasModoLista === "actuales" ? "toggle-btn toggle-btn--active" : "toggle-btn toggle-btn--inactive"}
                  onClick={() => {
                    setNotasModoLista("actuales");
                    setNotasStatus({ msg: "", error: false });
                  }}
                >
                  Notas Actuales
                </button>
                <button
                  type="button"
                  className={notasModoLista === "historico" ? "toggle-btn toggle-btn--active" : "toggle-btn toggle-btn--inactive"}
                  onClick={() => {
                    setNotasModoLista("historico");
                    setNotasStatus({ msg: "", error: false });
                  }}
                >
                  Histórico de Notas
                </button>
              </div>

              {notasModoLista === "actuales" && (
                <div className="toggle-row">
                  <button
                    type="button"
                    className={notasModoCarga === "individual" ? "toggle-btn toggle-btn--active" : "toggle-btn toggle-btn--inactive"}
                    onClick={() => {
                      setNotasModoCarga("individual");
                      setNotasStatus({ msg: "", error: false });
                    }}
                  >
                    Formulario Individual
                  </button>
                  <button
                    type="button"
                    className={notasModoCarga === "masiva" ? "toggle-btn toggle-btn--active" : "toggle-btn toggle-btn--inactive"}
                    onClick={() => {
                      setNotasModoCarga("masiva");
                      setNotasStatus({ msg: "", error: false });
                    }}
                  >
                    Carga Masiva CSV/Excel
                  </button>
                </div>
              )}

              {notasModoLista === "actuales" && notasModoCarga === "individual" && (
                <form className="grid notas-form" onSubmit={submitNota}>
                  <div className="field-group full">
                    <label htmlFor="nota-alumno">Estudiante</label>
                    <select
                      id="nota-alumno"
                      value={notaForm.alumno}
                      onChange={(e) => setNotaForm({ ...notaForm, alumno: e.target.value })}
                      required
                    >
                      <option value="">Selecciona</option>
                      {alumnoOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field-group full">
                    <label htmlFor="nota-asignatura">Asignatura</label>
                    <input
                      id="nota-asignatura"
                      type="text"
                      placeholder="Ej. Matemática"
                      value={notaForm.asignatura}
                      onChange={(e) => setNotaForm({ ...notaForm, asignatura: e.target.value })}
                      list="lista-asignaturas"
                      required
                    />
                    <datalist id="lista-asignaturas">
                      {ASIGNATURAS_VALIDAS.map((a) => (
                        <option key={a} value={a} />
                      ))}
                    </datalist>
                  </div>
                  <div className="field-group full">
                    <label htmlFor="nota-calif">Nota</label>
                    <input
                      id="nota-calif"
                      type="text"
                      placeholder="AD, A, B o C"
                      value={notaForm.nota}
                      onChange={(e) => setNotaForm({ ...notaForm, nota: e.target.value })}
                      required
                    />
                  </div>
                  {notasStatus.msg && (
                    <div
                      className={notasStatus.error ? "alert-error" : "alert-success"}
                      role="status"
                    >
                      {notasStatus.msg}
                    </div>
                  )}
                  <button className="full" type="submit">Actualizar Nota</button>
                </form>
              )}

              {notasModoLista === "actuales" && notasModoCarga === "masiva" && (
                <form className="grid notas-form" onSubmit={submitMasivaCsv}>
                  <p className="form-legend full">
                    CSV con encabezado: <strong>alumno_id,asignatura,calificacion</strong>
                    {" "}(calificacion: AD, A, B o C; asignatura exacta como en el sistema).
                    Excel: exporta a CSV antes de subir.
                  </p>
                  <input
                    className="full"
                    type="file"
                    accept=".csv,text/csv"
                    onChange={(e) => setArchivoMasivo(e.target.files?.[0] ?? null)}
                  />
                  {notasStatus.msg && (
                    <div
                      className={notasStatus.error ? "alert-error" : "alert-success"}
                      role="status"
                    >
                      {notasStatus.msg}
                    </div>
                  )}
                  <button className="full" type="submit">Procesar archivo</button>
                </form>
              )}

              {notasModoLista === "historico" && (
                <div className="grid notas-form">
                  <div className="field-group full">
                    <label htmlFor="nota-hist-alumno">Estudiante</label>
                    <select
                      id="nota-hist-alumno"
                      value={notaForm.alumno}
                      onChange={(e) => setNotaForm({ ...notaForm, alumno: e.target.value })}
                    >
                      <option value="">Selecciona</option>
                      {alumnoOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                  {notasStatus.msg && (
                    <div
                      className={notasStatus.error ? "alert-error" : "alert-success"}
                      role="status"
                    >
                      {notasStatus.msg}
                    </div>
                  )}
                  {!notaForm.alumno && (
                    <p className="form-legend full">Selecciona un estudiante para ver su histórico.</p>
                  )}
                  {notaForm.alumno && historicoNotas.length === 0 && !notasStatus.error && (
                    <p className="form-legend full">No hay notas registradas para este estudiante.</p>
                  )}
                  {historicoNotas.map((n) => (
                    <div key={n.id} className="card full">
                      <strong>{n.asignatura}</strong>
                      {" — "}
                      Calificación: <strong>{n.calificacion_literal}</strong>
                      {n.fecha_registro && (
                        <>
                          {" · "}
                          Fecha: {n.fecha_registro}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </article>
          </div>
        )}

        {activeView === "expediente" && (
          <article className="panel">
            <h2>Expediente Psicológico</h2>
            <form className="grid" onSubmit={submitExpediente}>
              <select className="full" value={expForm.alumno} onChange={(e) => setExpForm({ ...expForm, alumno: e.target.value })} required>
                <option value="">-- Selecciona --</option>
                {alumnoOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              <select className="full" value={expForm.nivel_preocupacion} onChange={(e) => setExpForm({ ...expForm, nivel_preocupacion: e.target.value })} required>
                <option value="1">1 - Muy baja preocupación</option><option value="2">2 - Preocupación leve</option><option value="3">3 - Preocupación moderada</option>
                <option value="4">4 - Preocupación alta</option><option value="5">5 - Preocupación crítica</option>
              </select>
              <input className="full" type="file" accept="application/pdf" onChange={(e) => setExpForm({ ...expForm, archivo_pdf: e.target.files?.[0] ?? null })} required />
              <button className="full" type="submit">Guardar Expediente</button>
            </form>
          </article>
        )}

        {status.msg && activeView !== "encuesta" && activeView !== "notas" && (
          <p className="status" style={{ color: status.error ? "#d62828" : "#14732b" }}>{status.msg}</p>
        )}
      </section>
    </div>
  );
}
