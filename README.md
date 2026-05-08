# CRUD Alumnos — Python + Flask + MySQL

Aplicación web minimalista para gestionar alumnos, desarrollada con Flask y MySQL. Diseñada para ejecutarse junto a un entorno Docker con MySQL ya levantado.

## Requisitos previos

- Python 3.x
- MySQL corriendo en Docker (ver contexto del curso)
- Las dependencias del proyecto

## Instalación y puesta en marcha

### 1. Clonar el repositorio

```bash
git clone https://github.com/pablopedernera0/crud-python.git
cd crud-python
```

### 2. Instalar dependencias

```bash
pip install flask mysql-connector-python --break-system-packages --ignore-installed
```

### 3. Configurar la IP del servidor MySQL

La aplicación se conecta al container MySQL por su IP interna en la red de Docker. Para obtenerla y configurarla automáticamente:

```bash
MYSQL_IP=$(docker inspect $(docker ps --filter "ancestor=mysql:latest" -q) --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
sed -i "s/172.18.0.2/$MYSQL_IP/" app.py
```

### 4. Iniciar la aplicación

```bash
python app.py &
```

La aplicación queda disponible en: [http://localhost:8888](http://localhost:8888)

---

## Estructura del proyecto

```
crud-python/
└── app.py        # Aplicación completa (rutas + templates + conexión BD)
```

Un solo archivo. Sin módulos adicionales, sin carpetas de configuración.

## Base de datos esperada

La aplicación utiliza la base de datos `alumnos` con la siguiente tabla:

```sql
CREATE TABLE alumnos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  apellido VARCHAR(50) NOT NULL,
  fecha_nacimiento DATE NOT NULL
);
```

Esta tabla es creada en el paso 3 del escenario Killercoda correspondiente.

## Funcionalidades

| Acción   | Ruta              | Método     |
|----------|-------------------|------------|
| Listar   | `/`               | GET        |
| Crear    | `/nuevo`          | GET / POST |
| Editar   | `/editar/<id>`    | GET / POST |
| Eliminar | `/eliminar/<id>`  | GET        |

## Contexto

Este proyecto forma parte de la práctica **"Nginx, MySQL, PhpMyAdmin y Flask con Docker"** del curso de Redes. Se utiliza como ejemplo de despliegue de una aplicación Python conectada a un servidor MySQL que corre en un container Docker, sin instalar nada directamente en el sistema operativo host.

## Autor

Pablo Pedernera
