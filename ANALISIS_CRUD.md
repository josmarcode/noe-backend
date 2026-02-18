# Análisis del proyecto — CRUD de Users y Vehicles

## Estado actual

El proyecto es una API REST Django con autenticación JWT (`djangorestframework-simplejwt`). Las apps `accounts` y `vehicles` están **casi funcionales**, pero tienen varios bugs que impiden su correcto funcionamiento.

---

## 🐛 Bugs que rompen el funcionamiento

### 1. `CustomUser` no tiene los campos `created_at` / `updated_at`

**Archivo:** `accounts/models.py`  
**Problema:** `UserSerializer` lista `created_at` y `updated_at` en sus `fields`, pero el modelo `CustomUser` extiende `AbstractUser` y **no define esos campos**. La migración actual tampoco los incluye. Esto causará un error al intentar serializar un usuario.

```python
# accounts/models.py — CORRECCIÓN
class CustomUser(AbstractUser):
    currency   = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)  # ← añadir
    updated_at = models.DateTimeField(auto_now=True)      # ← añadir
```

Después de editar el modelo, correr:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

---

### 2. Inconsistencia de nombre de campo: `active` vs `is_active` en `Vehicle`

**Archivos:** `vehicles/models.py`, `vehicles/serializers.py`, `accounts/serializers.py`  
**Problema:** El modelo define el campo como `active`, pero el serializer lo referencia como `is_active`.

| Lugar | Valor actual | Correcto |
|---|---|---|
| `Vehicle` model | `active` | elegir uno y ser consistente |
| `VehicleSerializer.Meta.fields` | `'is_active'` ← **error** | `'active'` |
| `UserSerializer.get_vehicles_count` | `.filter(is_active=True)` ← **error** | `.filter(active=True)` |

**Opción A — renombrar en el serializer (sin migración nueva):**

```python
# vehicles/serializers.py — campo correcto
fields = [
    'id', 'user', 'brand', 'model', 'year',
    'name', 'kilometers', 'created_at', 'updated_at',
    'active',            # ← era 'is_active'
    'owner_username', 'trackers_count',
]
```

```python
# accounts/serializers.py — filtro correcto
def get_vehicles_count(self, obj):
    return obj.vehicles.filter(active=True).count()  # ← era is_active=True
```

**Opción B — renombrar el campo en el modelo a `is_active`** (requiere migración nueva y cuidado de no colisionar con `AbstractUser.is_active`). **Se recomienda la Opción A.**

---

### 3. Bug en `update_kilometers` — variable indefinida

**Archivo:** `vehicles/views.py`  
**Problema:** En el action `update_kilometers` se llama `int(kilometers)` pero la variable se llama `new_km`.

```python
# vehicles/views.py — línea con bug
new_km = int(kilometers)   # ← 'kilometers' no está definido → NameError

# CORRECCIÓN
new_km = int(new_km)
```

---

### 4. Falta el archivo `.env`

**Problema:** `config/settings.py` carga `SECRET_KEY` y `DEBUG` desde un archivo `.env` con `python-dotenv`, pero ese archivo no existe en el repositorio. El servidor no arrancará porque `SECRET_KEY` quedará como `None`.

```bash
# Crear el archivo .env en la raíz del proyecto
SECRET_KEY=django-insecure-tu-clave-secreta-aqui
DEBUG=True
```

> **Nota:** El `SECRET_KEY` hardcodeado al inicio de `settings.py` queda sobreescrito más abajo por el `os.getenv('SECRET_KEY')`. Asegúrate de que `.env` tenga la clave.

---

## ⚠️ Cosas incompletas (no rompen pero limitan)

| Item | Descripción |
|---|---|
| `accounts/admin.py` | No registra `CustomUser`. Invisible en `/admin/`. |
| `vehicles/admin.py` | No registra `Vehicle`. Invisible en `/admin/`. |
| `VehicleSerializer.get_trackers_count` | Devuelve `0` hardcodeado (el conteo real está comentado). |
| Paginación | `DEFAULT_PAGINATION_CLASS` está comentada en settings. Con muchos registros no habrá paginación. |
| `UserViewSet` — acción `delete` | El ViewSet completo está expuesto, incluyendo `DELETE /api/auth/users/{id}/`. Considera restringir permisos para que un usuario no pueda borrar a otro. |

---

## ✅ Checklist para tener el CRUD funcional

```
[ ] 1. Añadir created_at y updated_at a CustomUser
[ ] 2. Correr makemigrations + migrate
[ ] 3. Corregir 'is_active' → 'active' en VehicleSerializer y UserSerializer
[ ] 4. Corregir int(kilometers) → int(new_km) en update_kilometers
[ ] 5. Crear archivo .env con SECRET_KEY y DEBUG
[ ] 6. (Opcional) Registrar modelos en admin.py
```

---

## 🗺️ Mapa de endpoints

### Auth — Base: `http://localhost:8000/api/auth/`

| Método | URL | Descripción | Auth necesaria |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Registro de usuario | No |
| `POST` | `/api/auth/login/` | Login — devuelve access + refresh token | No |
| `POST` | `/api/auth/token/refresh/` | Renovar access token | No |
| `POST` | `/api/auth/token/verify/` | Verificar validez de un token | No |
| `GET` | `/api/auth/users/` | Listar usuarios (solo el propio, o todos si staff) | Sí |
| `POST` | `/api/auth/users/` | Crear usuario directamente (staff) | Sí |
| `GET` | `/api/auth/users/{id}/` | Ver perfil de usuario | Sí |
| `PUT` | `/api/auth/users/{id}/` | Actualizar usuario completo | Sí |
| `PATCH` | `/api/auth/users/{id}/` | Actualizar usuario parcial | Sí |
| `DELETE` | `/api/auth/users/{id}/` | Eliminar usuario | Sí |
| `GET` | `/api/auth/users/me/` | Perfil del usuario autenticado | Sí |
| `POST` | `/api/auth/users/change_password/` | Cambiar contraseña | Sí |
| `POST` | `/api/auth/users/logout/` | Logout (blacklist del refresh token) | Sí |

### Vehicles — Base: `http://localhost:8000/api/vehicles/`

| Método | URL | Descripción | Auth necesaria |
|---|---|---|---|
| `GET` | `/api/vehicles/vehicles/` | Listar vehículos del usuario | Sí |
| `POST` | `/api/vehicles/vehicles/` | Crear vehículo | Sí |
| `GET` | `/api/vehicles/vehicles/{id}/` | Ver detalle de vehículo | Sí |
| `PUT` | `/api/vehicles/vehicles/{id}/` | Actualizar vehículo completo | Sí |
| `PATCH` | `/api/vehicles/vehicles/{id}/` | Actualizar vehículo parcial | Sí |
| `DELETE` | `/api/vehicles/vehicles/{id}/` | Eliminar vehículo | Sí |
| `POST` | `/api/vehicles/vehicles/{id}/update_kilometers/` | Actualizar kilometraje | Sí |

**Filtros disponibles en listado de vehículos:**
- `?brand=Toyota` — Filtrar por marca
- `?year=2020` — Filtrar por año
- `?active=true` — Filtrar por estado activo
- `?search=civic` — Búsqueda en brand, model, name
- `?ordering=year` — Ordenar por año (`-year` para descendente)

---

## 🧪 Cómo probar desde Postman paso a paso

### Paso 0 — Arrancar el servidor

```bash
python manage.py runserver
```

---

### Paso 1 — Registrar un usuario

**`POST` `http://localhost:8000/api/auth/register/`**

Headers:
```
Content-Type: application/json
```

Body (raw JSON):
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "MiPassword123!",
    "password2": "MiPassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "currency": "USD"
}
```

Respuesta esperada `201 Created`:
```json
{
    "user": { "id": 1, "username": "johndoe", ... },
    "tokens": {
        "refresh": "eyJ...",
        "access": "eyJ..."
    },
    "message": "User registered successfully."
}
```

---

### Paso 2 — Login (obtener tokens)

**`POST` `http://localhost:8000/api/auth/login/`**

Body:
```json
{
    "username": "johndoe",
    "password": "MiPassword123!"
}
```

Respuesta esperada `200 OK`:
```json
{
    "access": "eyJ...",
    "refresh": "eyJ..."
}
```

> **Guarda el `access` token.** Lo usarás en todas las peticiones siguientes.

---

### Paso 3 — Configurar autenticación en Postman

En cada petición que requiera auth, ir a la pestaña **Authorization**:
- Type: `Bearer Token`
- Token: `<pega aquí el access token>`

O manualmente en **Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Paso 4 — Ver mi perfil

**`GET` `http://localhost:8000/api/auth/users/me/`**

Headers: `Authorization: Bearer <token>`

---

### Paso 5 — Actualizar perfil (PATCH parcial)

**`PATCH` `http://localhost:8000/api/auth/users/1/`**

Body:
```json
{
    "first_name": "Jonathan",
    "currency": "EUR"
}
```

---

### Paso 6 — Cambiar contraseña

**`POST` `http://localhost:8000/api/auth/users/change_password/`**

Body:
```json
{
    "old_password": "MiPassword123!",
    "new_password": "NuevoPass456!",
    "new_password2": "NuevoPass456!"
}
```

---

### Paso 7 — Crear un vehículo

**`POST` `http://localhost:8000/api/vehicles/vehicles/`**

Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`

Body:
```json
{
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2021,
    "name": "Mi Corolla",
    "kilometers": 15000
}
```

> **Nota:** No envíes el campo `user`; el backend lo asigna automáticamente con `perform_create`.

Respuesta esperada `201 Created`:
```json
{
    "id": 1,
    "user": 1,
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2021,
    "name": "Mi Corolla",
    "kilometers": 15000,
    "created_at": "2026-02-17T...",
    "updated_at": "2026-02-17T...",
    "active": true,
    "owner_username": "johndoe",
    "trackers_count": 0
}
```

---

### Paso 8 — Listar vehículos

**`GET` `http://localhost:8000/api/vehicles/vehicles/`**

Devuelve solo los vehículos activos del usuario autenticado (usando `VehicleListSerializer`, campos reducidos).

Con filtros:
```
GET /api/vehicles/vehicles/?brand=Toyota
GET /api/vehicles/vehicles/?year=2021
GET /api/vehicles/vehicles/?search=corolla
GET /api/vehicles/vehicles/?ordering=-year
```

---

### Paso 9 — Ver detalle de un vehículo

**`GET` `http://localhost:8000/api/vehicles/vehicles/1/`**

---

### Paso 10 — Actualizar vehículo

**`PUT` `http://localhost:8000/api/vehicles/vehicles/1/`** (requiere todos los campos)

```json
{
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2021,
    "name": "Mi Corolla Actualizado",
    "kilometers": 20000
}
```

**`PATCH` `http://localhost:8000/api/vehicles/vehicles/1/`** (solo los campos a cambiar)

```json
{
    "kilometers": 22000
}
```

---

### Paso 11 — Actualizar kilometraje con el action personalizado

**`POST` `http://localhost:8000/api/vehicles/vehicles/1/update_kilometers/`**

Body:
```json
{
    "kilometers": 25000
}
```

> ⚠️ Este endpoint tiene el bug mencionado (variable `kilometers` indefinida). Requiere el fix antes de poder usarlo.

---

### Paso 12 — Eliminar vehículo

**`DELETE` `http://localhost:8000/api/vehicles/vehicles/1/`**

Respuesta: `204 No Content`

---

### Paso 13 — Renovar el access token

Cuando el token (`ACCESS_TOKEN_LIFETIME = 1h`) expire:

**`POST` `http://localhost:8000/api/auth/token/refresh/`**

Body:
```json
{
    "refresh": "eyJ..."
}
```

Respuesta:
```json
{
    "access": "eyJ...",
    "refresh": "eyJ..."   // nuevo refresh (ROTATE_REFRESH_TOKENS = True)
}
```

---

### Paso 14 — Logout

**`POST` `http://localhost:8000/api/auth/users/logout/`**

Body:
```json
{
    "refresh": "eyJ..."
}
```

---

## 💡 Colección Postman sugerida

Estructura recomendada para organizar la colección:

```
📁 NOE API
  📁 Auth
    POST  Register
    POST  Login
    POST  Token Refresh
    POST  Token Verify
  📁 Users
    GET   Me
    GET   List Users
    GET   Get User
    PATCH Update User
    DELETE Delete User
    POST  Change Password
    POST  Logout
  📁 Vehicles
    GET   List Vehicles
    POST  Create Vehicle
    GET   Get Vehicle
    PUT   Update Vehicle
    PATCH Partial Update Vehicle
    DELETE Delete Vehicle
    POST  Update Kilometers
```

**Variable de entorno en Postman:**

| Variable | Valor inicial |
|---|---|
| `base_url` | `http://localhost:8000` |
| `access_token` | *(se llena tras login)* |
| `refresh_token` | *(se llena tras login)* |

En el **Post-request Script** del request de Login, puedes guardar los tokens automáticamente:

```javascript
const res = pm.response.json();
pm.environment.set("access_token", res.access);
pm.environment.set("refresh_token", res.refresh);
```

Y usar en Authorization: `Bearer {{access_token}}`
