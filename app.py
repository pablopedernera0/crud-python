from flask import Flask, render_template_string, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecreto123"

DB_CONFIG = {
    "host": "172.18.0.2",
    "port": 3306,
    "user": "root",
    "password": "mysecretpassword",
    "database": "alumnos",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ── Template base ────────────────────────────────────────────────────────────
BASE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gestión de Alumnos</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<nav class="navbar navbar-dark bg-primary mb-4">
  <div class="container">
    <span class="navbar-brand fw-bold">🎓 Gestión de Alumnos</span>
    <div>
      <a href="/" class="btn btn-outline-light btn-sm">Ver todos</a>
      <a href="/logout" class="btn btn-outline-light btn-sm">Salir</a>
    </div>
  </div>
</nav>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
      <div class="alert alert-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
</body>
</html>
"""

LIST_TPL = BASE.replace("{% block content %}{% endblock %}", """
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h4>Listado de alumnos</h4>
  <a href="/nuevo" class="btn btn-success">+ Nuevo alumno</a>
</div>
<table class="table table-bordered table-hover bg-white shadow-sm">
  <thead class="table-primary">
    <tr>
      <th>#</th><th>Nombre</th><th>Apellido</th><th>Fecha de nacimiento</th><th>Acciones</th>
    </tr>
  </thead>
  <tbody>
    {% for a in alumnos %}
    <tr>
      <td>{{ a[0] }}</td>
      <td>{{ a[1] }}</td>
      <td>{{ a[2] }}</td>
      <td>{{ a[3] }}</td>
      <td>
        <a href="/editar/{{ a[0] }}" class="btn btn-warning btn-sm">Editar</a>
        <a href="/eliminar/{{ a[0] }}" class="btn btn-danger btn-sm"
           onclick="return confirm('¿Eliminar este alumno?')">Eliminar</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="5" class="text-center text-muted">No hay alumnos cargados.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
""")

FORM_TPL = BASE.replace("{% block content %}{% endblock %}", """
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">{{ titulo }}</h5>
      </div>
      <div class="card-body">
        <form method="POST">
          <div class="mb-3">
            <label class="form-label">Nombre</label>
            <input type="text" name="nombre" class="form-control"
                   value="{{ alumno[1] if alumno else '' }}" required maxlength="50">
          </div>
          <div class="mb-3">
            <label class="form-label">Apellido</label>
            <input type="text" name="apellido" class="form-control"
                   value="{{ alumno[2] if alumno else '' }}" required maxlength="50">
          </div>
          <div class="mb-3">
            <label class="form-label">Fecha de nacimiento</label>
            <input type="date" name="fecha_nacimiento" class="form-control"
                   value="{{ alumno[3] if alumno else '' }}" required>
          </div>
          <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary">Guardar</button>
            <a href="/" class="btn btn-secondary">Cancelar</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

LOGIN_TPL = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ingresar — Gestión de Alumnos</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<nav class="navbar navbar-dark bg-primary mb-4">
  <div class="container">
    <span class="navbar-brand fw-bold">🎓 Gestión de Alumnos</span>
  </div>
</nav>
<div class="container">
  <div class="row justify-content-center">
    <div class="col-md-4">
      <div class="card shadow-sm">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Iniciar sesión</h5>
        </div>
        <div class="card-body">
          {% if error %}
          <div class="alert alert-danger">{{ error }}</div>
          {% endif %}
          <form method="POST">
            <div class="mb-3">
              <label class="form-label">Usuario</label>
              <input type="text" name="usuario" class="form-control" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Contraseña</label>
              <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Ingresar</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# ── Autenticación ────────────────────────────────────────────────────────────

@app.before_request
def requerir_login():
    rutas_publicas = {"login", "static"}
    if request.endpoint not in rutas_publicas and not session.get("logged_in"):
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        db = get_db()
        cur = db.cursor()
        query = f"SELECT id, usuario FROM usuarios WHERE usuario = '{usuario}' AND password = '{password}'"
        cur.execute(query)
        fila = cur.fetchone()
        db.close()
        if fila:
            session["logged_in"] = True
            session["usuario"] = fila[1]
            return redirect(url_for("index"))
        error = "Usuario o contraseña incorrectos"
    return render_template_string(LOGIN_TPL, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Rutas ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, nombre, apellido, fecha_nacimiento FROM alumnos ORDER BY id")
    alumnos = cur.fetchall()
    db.close()
    return render_template_string(LIST_TPL, alumnos=alumnos)

@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        fecha = request.form["fecha_nacimiento"]
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO alumnos (nombre, apellido, fecha_nacimiento) VALUES (%s, %s, %s)",
            (nombre, apellido, fecha)
        )
        db.commit()
        db.close()
        return redirect(url_for("index"))
    return render_template_string(FORM_TPL, titulo="Nuevo alumno", alumno=None)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        fecha = request.form["fecha_nacimiento"]
        cur.execute(
            "UPDATE alumnos SET nombre=%s, apellido=%s, fecha_nacimiento=%s WHERE id=%s",
            (nombre, apellido, fecha, id)
        )
        db.commit()
        db.close()
        return redirect(url_for("index"))
    cur.execute("SELECT id, nombre, apellido, fecha_nacimiento FROM alumnos WHERE id=%s", (id,))
    alumno = cur.fetchone()
    db.close()
    return render_template_string(FORM_TPL, titulo="Editar alumno", alumno=alumno)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM alumnos WHERE id=%s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=False)
