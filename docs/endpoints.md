# Documentación de Endpoints

**Base URL:** `http://<host>/api/`  
**Autenticación:** JWT Bearer Token (excepto donde se indique lo contrario)  
**Formato:** JSON

---

## Autenticación (`/api/auth/`)

### Registro

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/register/` | No |

**Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "currency": "string (3 chars, opcional, default: USD)"
}
```

**Respuesta `201`:**
```json
{
  "user": { ... },
  "tokens": { "refresh": "...", "access": "..." },
  "message": "User registered successfully."
}
```

---

### Login

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/login/` | No |

**Body:**
```json
{ "username": "string", "password": "string" }
```

**Respuesta `200`:**
```json
{ "access": "...", "refresh": "..." }
```

---

### Renovar access token

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/token/refresh/` | No |

**Body:**
```json
{ "refresh": "string" }
```

**Respuesta `200`:**
```json
{ "access": "...", "refresh": "..." }
```

---

### Verificar token

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/token/verify/` | No |

**Body:**
```json
{ "token": "string" }
```

**Respuesta `200`:** `{}`  
**Respuesta `401`:** token inválido o expirado.

---

## Usuarios (`/api/auth/users/`)

### Listar usuarios

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/auth/users/` | Sí |

Usuarios normales solo ven su propio perfil. Staff ve todos.

**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "currency": "USD",
    "vehicles_count": 3,
    "created_at": "2026-03-03T10:00:00Z",
    "updated_at": "2026-03-03T10:00:00Z"
  }
]
```

---

### Obtener usuario por ID

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/auth/users/{id}/` | Sí |

**Respuesta `200`:** objeto `User` (ver schema arriba).

---

### Actualizar perfil

| Método | URL | Auth |
|--------|-----|------|
| `PUT` | `/api/auth/users/{id}/` | Sí |
| `PATCH` | `/api/auth/users/{id}/` | Sí |

**Body (campos editables):**
```json
{
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "currency": "string"
}
```

---

### Eliminar usuario

| Método | URL | Auth |
|--------|-----|------|
| `DELETE` | `/api/auth/users/{id}/` | Sí |

**Respuesta `204 No Content`.**

---

### Perfil propio

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/auth/users/me/` | Sí |

Devuelve el perfil del usuario autenticado.

---

### Cambiar contraseña

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/users/change_password/` | Sí |

**Body:**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Respuesta `200`:**
```json
{ "message": "Password updated successfully." }
```

**Respuesta `400`:** si la contraseña antigua es incorrecta.

---

### Logout

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/auth/users/logout/` | Sí |

**Body:**
```json
{ "refresh": "string" }
```

**Respuesta `200`:**
```json
{ "message": "User logged out successfully." }
```

---

## Vehículos (`/api/vehicles/`)

### Listar vehículos

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/vehicles/` | Sí |

Solo devuelve vehículos activos del usuario autenticado. Staff ve todos.

**Parámetros de query:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `brand` | string | Filtrar por marca |
| `year` | integer | Filtrar por año |
| `search` | string | Búsqueda en `brand`, `model`, `name` |
| `ordering` | string | Ordenar por `created_at`, `year`, `kilometers` (prefijo `-` para desc) |

**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "name": "Mi Corolla",
    "kilometers": 45000
  }
]
```

> La lista usa un serializer ligero (`VehicleListSerializer`). Para ver todos los campos, consulta el detalle.

---

### Crear vehículo

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/vehicles/` | Sí |

El campo `user` se asigna automáticamente al usuario autenticado.

**Body:**
```json
{
  "brand": "string",
  "model": "string",
  "year": 2020,
  "name": "string",
  "kilometers": 0,
  "is_active": true
}
```

**Respuesta `201`:**
```json
{
  "id": 1,
  "user": 1,
  "brand": "Toyota",
  "model": "Corolla",
  "year": 2020,
  "name": "Mi Corolla",
  "kilometers": 45000,
  "created_at": "2026-03-03T10:00:00Z",
  "updated_at": "2026-03-03T10:00:00Z",
  "is_active": true,
  "owner_username": "johndoe",
  "trackers_count": 0
}
```

**Validaciones:**
- `year` debe estar entre 1900 y el año actual + 5.

---

### Obtener vehículo por ID

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/vehicles/{id}/` | Sí |

**Respuesta `200`:** objeto `Vehicle` completo (ver schema de creación).

---

### Actualizar vehículo

| Método | URL | Auth |
|--------|-----|------|
| `PUT` | `/api/vehicles/{id}/` | Sí |
| `PATCH` | `/api/vehicles/{id}/` | Sí |

**Body:** mismo schema que creación.

---

### Eliminar vehículo

| Método | URL | Auth |
|--------|-----|------|
| `DELETE` | `/api/vehicles/{id}/` | Sí |

**Respuesta `204 No Content`.**

---

### Actualizar kilómetros

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/vehicles/{id}/update_kilometers/` | Sí |

Actualiza el odómetro del vehículo. No permite reducir el valor actual.

**Body:**
```json
{ "kilometers": 50000 }
```

**Respuesta `200`:** objeto `Vehicle` actualizado.

**Respuesta `400`:** si `kilometers` es menor al valor actual o no es un entero válido.

---

## Trackers (`/api/trackers/`)

Un tracker representa un mantenimiento periódico configurado para un vehículo (cambio de aceite, frenos, filtro de aire, etc.).

### Listar trackers

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/trackers/` | Sí |

Solo devuelve trackers activos del usuario autenticado.

**Parámetros de query:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `vehicle` | integer | Filtrar por ID de vehículo |
| `type` | string | Filtrar por tipo |
| `active` | boolean | Filtrar por estado activo |
| `search` | string | Búsqueda en `name`, `type` |
| `ordering` | string | Ordenar por `created_at`, `next_due_km`, `last_service_km` |

**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "vehicle": 1,
    "type": "oil",
    "name": "Cambio de aceite",
    "icon": "oil-can",
    "unit": "km",
    "next_due_km": 50000,
    "active": true,
    "is_due": false
  }
]
```

---

### Crear tracker

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/trackers/` | Sí |

**Body:**
```json
{
  "vehicle": 1,
  "type": "string",
  "name": "string",
  "icon": "string (opcional)",
  "unit": "km",
  "interval_value": 5000,
  "last_service_km": 0,
  "last_service_at": "2026-01-01T00:00:00Z (opcional)",
  "next_due_km": 5000,
  "next_due_at": "2026-12-01T00:00:00Z (opcional)"
}
```

**Respuesta `201`:** objeto `Tracker` completo.

**Validaciones:**
- `next_due_km` debe ser mayor que `last_service_km`.
- El vehículo debe pertenecer al usuario autenticado.

---

### Obtener tracker por ID

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/trackers/{id}/` | Sí |

**Respuesta `200`:**
```json
{
  "id": 1,
  "vehicle": 1,
  "vehicle_name": "Mi Corolla",
  "type": "oil",
  "name": "Cambio de aceite",
  "icon": "oil-can",
  "unit": "km",
  "interval_value": 5000,
  "last_service_km": 45000,
  "last_service_at": "2026-01-15T10:00:00Z",
  "next_due_km": 50000,
  "next_due_at": null,
  "active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "is_due": false,
  "registers_count": 3
}
```

**Campo `is_due`:** `true` si los kilómetros actuales del vehículo son ≥ `next_due_km`.

---

### Actualizar tracker

| Método | URL | Auth |
|--------|-----|------|
| `PUT` | `/api/trackers/{id}/` | Sí |
| `PATCH` | `/api/trackers/{id}/` | Sí |

---

### Eliminar tracker

| Método | URL | Auth |
|--------|-----|------|
| `DELETE` | `/api/trackers/{id}/` | Sí |

**Respuesta `204 No Content`.**

---

### Registrar servicio

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/trackers/{id}/record_service/` | Sí |

Registra un evento de servicio manual directamente en el tracker, actualizando `last_service_km`, `next_due_km` y opcionalmente `last_service_at`.

> **Alternativa recomendada:** Crear un `Register` (ver sección siguiente), que actualiza el tracker automáticamente y deja historial.

**Body:**
```json
{
  "service_km": 45000,
  "service_at": "2026-02-23T10:00:00Z (opcional)"
}
```

**Respuesta `200`:** objeto `Tracker` actualizado.

---

## Registros de servicio (`/api/registers/`)

Un register es el registro histórico de un servicio realizado. Al crear o actualizar un register, el tracker asociado se actualiza automáticamente.

### Listar registers

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/registers/` | Sí |

Solo devuelve registers activos del usuario autenticado.

**Parámetros de query:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `tracker` | integer | Filtrar por ID de tracker |
| `tracker__vehicle` | integer | Filtrar por ID de vehículo |
| `active` | boolean | Filtrar por estado activo |
| `search` | string | Búsqueda en `note`, `tracker__name`, `tracker__type` |
| `ordering` | string | Ordenar por `tracker_at`, `kilometers`, `amount`, `created_at` |

**Respuesta `200`:**
```json
[
  {
    "id": 1,
    "tracker": 1,
    "tracker_name": "Cambio de aceite",
    "tracker_type": "oil",
    "kilometers": 45000,
    "amount": "35.50",
    "tracker_at": "2026-01-15T10:00:00Z",
    "active": true
  }
]
```

---

### Crear register

| Método | URL | Auth |
|--------|-----|------|
| `POST` | `/api/registers/` | Sí |

Al crear, se actualiza automáticamente el tracker con el km del servicio y se recalcula `next_due_km`.

**Body:**
```json
{
  "tracker": 1,
  "kilometers": 45000,
  "amount": "35.50",
  "note": "string (opcional)"
}
```

**Respuesta `201`:**
```json
{
  "id": 1,
  "tracker": 1,
  "tracker_name": "Cambio de aceite",
  "tracker_type": "oil",
  "vehicle_id": 1,
  "vehicle_name": "Mi Corolla",
  "kilometers": 45000,
  "amount": "35.50",
  "tracker_at": "2026-03-03T10:00:00Z",
  "note": null,
  "active": true,
  "created_at": "2026-03-03T10:00:00Z",
  "updated_at": "2026-03-03T10:00:00Z"
}
```

**Validaciones:**
- `kilometers` no puede ser menor que el `last_service_km` del tracker asociado.

---

### Obtener register por ID

| Método | URL | Auth |
|--------|-----|------|
| `GET` | `/api/registers/{id}/` | Sí |

**Respuesta `200`:** objeto `Register` completo (ver schema de creación).

---

### Actualizar register

| Método | URL | Auth |
|--------|-----|------|
| `PUT` | `/api/registers/{id}/` | Sí |
| `PATCH` | `/api/registers/{id}/` | Sí |

Al actualizar, el tracker se re-sincroniza automáticamente usando el register más reciente (mayor `kilometers`) activo.

---

### Eliminar register

| Método | URL | Auth |
|--------|-----|------|
| `DELETE` | `/api/registers/{id}/` | Sí |

**Respuesta `204 No Content`.**

---

## Códigos de respuesta comunes

| Código | Significado |
|--------|-------------|
| `200 OK` | Operación exitosa |
| `201 Created` | Recurso creado |
| `204 No Content` | Eliminación exitosa |
| `400 Bad Request` | Datos inválidos o faltantes |
| `401 Unauthorized` | Token ausente, inválido o expirado |
| `403 Forbidden` | Sin permisos sobre el recurso |
| `404 Not Found` | Recurso no encontrado |

---

## Resumen de rutas

```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/token/refresh/
POST   /api/auth/token/verify/
GET    /api/auth/users/
GET    /api/auth/users/{id}/
PUT    /api/auth/users/{id}/
PATCH  /api/auth/users/{id}/
DELETE /api/auth/users/{id}/
GET    /api/auth/users/me/
POST   /api/auth/users/change_password/
POST   /api/auth/users/logout/

GET    /api/vehicles/
POST   /api/vehicles/
GET    /api/vehicles/{id}/
PUT    /api/vehicles/{id}/
PATCH  /api/vehicles/{id}/
DELETE /api/vehicles/{id}/
POST   /api/vehicles/{id}/update_kilometers/

GET    /api/trackers/
POST   /api/trackers/
GET    /api/trackers/{id}/
PUT    /api/trackers/{id}/
PATCH  /api/trackers/{id}/
DELETE /api/trackers/{id}/
POST   /api/trackers/{id}/record_service/

GET    /api/registers/
POST   /api/registers/
GET    /api/registers/{id}/
PUT    /api/registers/{id}/
PATCH  /api/registers/{id}/
DELETE /api/registers/{id}/
```
