# Guía de Registro y Autenticación

Esta guía describe el flujo completo de autenticación de la API, basada en **JWT (JSON Web Tokens)** gestionados con `djangorestframework-simplejwt`.

---

## Resumen del mecanismo

La autenticación se basa en dos tokens:

| Token | Duración | Propósito |
|---|---|---|
| `access` | 1 hora | Autorizar peticiones a la API |
| `refresh` | 7 días | Obtener un nuevo `access` sin re-login |

Cada token de refresco se invalida tras el uso (`ROTATE_REFRESH_TOKENS = True`) y se registra en una blacklist (`BLACKLIST_AFTER_ROTATION = True`).

---

## Flujo completo

### 1. Registro

**Endpoint:** `POST /api/auth/register/`  
**Autenticación requerida:** No

El usuario proporciona sus datos. Al registrarse correctamente, la API devuelve directamente los tokens, por lo que no es necesario hacer un login posterior.

**Request body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "currency": "USD"
}
```

**Campos requeridos:** `username`, `email`, `password`, `first_name`, `last_name`  
**Campos opcionales:** `currency` (default: `"USD"`, código ISO 4217 de 3 caracteres)

**Respuesta exitosa (`201 Created`):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "currency": "USD",
    "vehicles_count": 0,
    "created_at": "2026-03-03T10:00:00Z",
    "updated_at": "2026-03-03T10:00:00Z"
  },
  "tokens": {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  },
  "message": "User registered successfully."
}
```

**Validaciones aplicadas:**
- El `email` debe ser único en el sistema.
- El `password` pasa por los validadores de Django: longitud mínima, similitud con datos del usuario, contraseñas comunes y numérica-únicamente.

---

### 2. Login (obtener tokens)

**Endpoint:** `POST /api/auth/login/`  
**Autenticación requerida:** No

**Request body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Respuesta exitosa (`200 OK`):**
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

---

### 3. Uso del token en peticiones protegidas

Todas las rutas de la API (excepto `/api/auth/register/` y `/api/auth/login/`) requieren el token de acceso en el header de autorización:

```
Authorization: Bearer <access_token>
```

Si el token no se incluye o está expirado, la API responde con `401 Unauthorized`.

---

### 4. Renovar el access token (refresh)

Cuando el `access_token` expira (después de 1 hora), se puede recuperar un nuevo par de tokens sin necesidad de hacer login.

**Endpoint:** `POST /api/auth/token/refresh/`  
**Autenticación requerida:** No

**Request body:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Respuesta exitosa (`200 OK`):**
```json
{
  "access": "<nuevo_access_token>",
  "refresh": "<nuevo_refresh_token>"
}
```

> **Importante:** El `refresh_token` usado se invalida inmediatamente. El nuevo `refresh_token` devuelto es el que debe utilizarse en la próxima renovación.

---

### 5. Verificar un token

Para confirmar que un token de acceso es válido y no ha expirado.

**Endpoint:** `POST /api/auth/token/verify/`  
**Autenticación requerida:** No

**Request body:**
```json
{
  "token": "<access_token>"
}
```

**Respuesta exitosa (`200 OK`):**
```json
{}
```

**Respuesta si el token es inválido (`401 Unauthorized`):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 6. Logout (invalidar el refresh token)

El logout invalida el `refresh_token` agregándolo a la blacklist, impidiendo que se use para generar nuevos `access_token`.

**Endpoint:** `POST /api/auth/users/logout/`  
**Autenticación requerida:** Sí (`Authorization: Bearer <access_token>`)

**Request body:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Respuesta exitosa (`200 OK`):**
```json
{
  "message": "User logged out successfully."
}
```

> **Nota:** El `access_token` actual seguirá siendo técnicamente válido hasta su expiración natural (1 hora). Para revocar el acceso de forma inmediata sería necesario implementar una blacklist también para access tokens.

---

## Gestión del perfil autenticado

### Ver perfil propio

**Endpoint:** `GET /api/auth/users/me/`  
**Autenticación requerida:** Sí

**Respuesta (`200 OK`):**
```json
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
```

### Cambiar contraseña

**Endpoint:** `POST /api/auth/users/change_password/`  
**Autenticación requerida:** Sí

**Request body:**
```json
{
  "old_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**Respuesta exitosa (`200 OK`):**
```json
{
  "message": "Password updated successfully."
}
```

---

## Diagrama del flujo

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       │  POST /api/auth/register/
       │  POST /api/auth/login/
       ▼
┌─────────────────────┐
│   Recibe tokens     │
│   access (1h)       │
│   refresh (7 días)  │
└──────┬──────────────┘
       │
       │  Authorization: Bearer <access_token>
       ▼
┌─────────────────────────┐
│  Peticiones protegidas  │
│  /api/vehicles/         │
│  /api/trackers/         │
│  /api/registers/        │
└──────┬──────────────────┘
       │
       │  (cuando access expira)
       │  POST /api/auth/token/refresh/
       ▼
┌─────────────────────┐
│  Nuevo par de       │
│  tokens             │
└──────┬──────────────┘
       │
       │  (al cerrar sesión)
       │  POST /api/auth/users/logout/
       ▼
┌─────────────────────┐
│  refresh invalidado │
│  en blacklist       │
└─────────────────────┘
```

---

## Notas de seguridad

- El `SECRET_KEY` se carga desde variables de entorno (`.env`). Nunca debe estar hardcodeado en producción.
- `DEBUG = False` en producción para evitar la exposición de trazas de error.
- `CORS_ALLOW_ALL_ORIGINS = True` está activo — restringir a los dominios permitidos en producción.
- Los tokens usan el algoritmo `HS256`.
