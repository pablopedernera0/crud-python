from flask import Flask, render_template_string, request, redirect, url_for
import mysql.connector
import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Configuración MySQL ───────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "172.18.0.2"),
    "port":     int(os.getenv("MYSQL_PORT", 3306)),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "mysecretpassword"),
    "database": os.getenv("MYSQL_DATABASE", "alumnos"),
}

# ── Configuración S3 / Floci ──────────────────────────────────────────────────
S3_ENDPOINT   = os.getenv("S3_ENDPOINT",   "http://localhost:4566")
S3_REGION     = os.getenv("S3_REGION",     "us-east-1")
S3_BUCKET     = os.getenv("S3_BUCKET",     "fotos-alumnos")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID",     "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Agrega la columna foto_url si no existe."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            ALTER TABLE alumnos
            ADD COLUMN foto_url VARCHAR(500)
        """)
        db.commit()
        db.close()
    except mysql.connector.errors.DatabaseError:
        # La columna ya existe, no hacer nada
        pass

init_db()

# ── Templates ─────────────────────────────────────────────────────────────────
BASE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gestión de Alumnos</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .foto-thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 50%; }
    .foto-placeholder { width: 48px; height: 48px; border-radius: 50%;
                        background: #dee2e6; display:inline-flex;
                        align-items:center; justify-content:center; color:#6c757d; font-size:20px; }
  </style>
</head>
<body class="bg-light">
<nav class="navbar navbar-dark bg-primary mb-4">
  <div class="container">
    <span class="navbar-brand fw-bold">🎓 Gestión de Alumnos</span>
    <a href="/" class="btn btn-outline-light btn-sm">Ver todos</a>
  </div>
</nav>
<div class="container">
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
<table class="table table-bordered table-hover bg-white shadow-sm align-middle">
  <thead class="table-primary">
    <tr>
      <th>#</th><th>Foto</th><th>Nombre</th><th>Apellido</th><th>Fecha de nacimiento</th><th>Acciones</th>
    </tr>
  </thead>
  <tbody>
    {% for a in alumnos %}
    <tr>
      <td>{{ a[0] }}</td>
      <td>
        {% if a[4] %}
          <img src="{{ a[4] }}" class="foto-thumb" alt="foto">
        {% else %}
          <span class="foto-placeholder">👤</span>
        {% endif %}
      </td>
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
    <tr><td colspan="6" class="text-center text-muted">No hay alumnos cargados.</td></tr>
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
        <form method="POST" enctype="multipart/form-data">
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
          <div class="mb-3">
            <label class="form-label">Foto del alumno</label>
            {% if alumno and alumno[4] %}
              <div class="mb-2">
                <img src="{{ alumno[4] }}" style="height:80px; border-radius:8px;" alt="foto actual">
                <small class="text-muted ms-2">Foto actual</small>
              </div>
            {% endif %}
            <input type="file" name="foto" class="form-control" accept="image/*">
            <small class="text-muted">Formatos aceptados: JPG, PNG, GIF. Opcional.</small>
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def upload_foto(file, alumno_id):
    """Sube la foto a S3 y devuelve la URL pública."""
    if not file or file.filename == "":
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    key = f"alumnos/{alumno_id}.{ext}"
    s3 = get_s3()
    s3.upload_fileobj(
        file,
        S3_BUCKET,
        key,
        ExtraArgs={"ContentType": file.content_type or "image/jpeg"},
    )
    return f"{S3_ENDPOINT}/{S3_BUCKET}/{key}"

# ── Rutas ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, nombre, apellido, fecha_nacimiento, foto_url FROM alumnos ORDER BY id")
    alumnos = cur.fetchall()
    db.close()
    return render_template_string(LIST_TPL, alumnos=alumnos)

@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        nombre   = request.form["nombre"]
        apellido = request.form["apellido"]
        fecha    = request.form["fecha_nacimiento"]

        # Insertar primero para obtener el id
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO alumnos (nombre, apellido, fecha_nacimiento) VALUES (%s, %s, %s)",
            (nombre, apellido, fecha)
        )
        db.commit()
        alumno_id = cur.lastrowid

        # Subir foto si viene
        foto = request.files.get("foto")
        foto_url = upload_foto(foto, alumno_id)
        if foto_url:
            cur.execute("UPDATE alumnos SET foto_url=%s WHERE id=%s", (foto_url, alumno_id))
            db.commit()

        db.close()
        return redirect(url_for("index"))

    return render_template_string(FORM_TPL, titulo="Nuevo alumno", alumno=None)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        nombre   = request.form["nombre"]
        apellido = request.form["apellido"]
        fecha    = request.form["fecha_nacimiento"]

        foto = request.files.get("foto")
        foto_url = upload_foto(foto, id)

        if foto_url:
            cur.execute(
                "UPDATE alumnos SET nombre=%s, apellido=%s, fecha_nacimiento=%s, foto_url=%s WHERE id=%s",
                (nombre, apellido, fecha, foto_url, id)
            )
        else:
            cur.execute(
                "UPDATE alumnos SET nombre=%s, apellido=%s, fecha_nacimiento=%s WHERE id=%s",
                (nombre, apellido, fecha, id)
            )
        db.commit()
        db.close()
        return redirect(url_for("index"))

    cur.execute("SELECT id, nombre, apellido, fecha_nacimiento, foto_url FROM alumnos WHERE id=%s", (id,))
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