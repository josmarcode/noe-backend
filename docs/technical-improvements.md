# Documento Técnico: Mejoras y Pendientes

Este documento analiza el estado actual del proyecto, identifica lo que falta implementar y propone mejoras priorizadas del **1 (crítico)** al **3 (deseable)**.

**Contexto del despliegue:**
- Plataforma: **Railway** (despliegue directo desde Git, sin Docker)
- Frontend: proyecto separado (dominio distinto, CORS activo)
- Entorno: staging / pruebas (desplegado públicamente, pero no productivo)

---

## Estado actual del proyecto

El proyecto es una API REST para la gestión de mantenimiento vehicular. El stack es:

- **Django** con **Django REST Framework**
- **JWT** via `djangorestframework-simplejwt`
- **SQLite** como base de datos (**inviable en Railway** — ver 1.2)
- Apps con modelos definidos pero sin capa API: `notifications`, `access`, `errors`

| Componente | Estado |
|---|---|
| Autenticación JWT | ✅ Implementado |
| CRUD Vehículos | ✅ Implementado (con bug en filtros) |
| CRUD Trackers | ✅ Implementado |
| CRUD Registers | ✅ Implementado |
| App `notifications` | ⚠️ Modelo definido, sin API |
| App `access` | ⚠️ Modelo definido, sin API |
| App `errors` | ⚠️ Modelo definido, sin API |
| Configuración Railway | ❌ No existe (`Procfile`, `gunicorn`, `dj-database-url`) |
| Base de datos persistente | ❌ SQLite (datos se pierden con cada deploy en Railway) |
| Tests | ❌ Sin implementar |

---

## 🔴 Prioridad 1 — Crítico (bloquea el despliegue o causa pérdida de datos)

### 1.1 Configuración de despliegue en Railway (sin Procfile ni gunicorn)

**Problema actual:** No existe ningún archivo de configuración de arranque (`Procfile`) y `gunicorn` no está en `requirements.txt`. Railway detecta el proyecto como Django vía Nixpacks pero, sin un servidor WSGI declarado, arrancará con el servidor de desarrollo de Django (`runserver`), que no es seguro ni admite concurrencia.

**Impacto:** El servicio opera con el servidor de desarrollo de Django en producción: sin soporte de múltiples workers, sin manejo correcto de señales de proceso y con advertencias de seguridad activas.

**Solución:**

1. Añadir a `requirements.txt`:
```
gunicorn==23.0.0
```

2. Crear `Procfile` en la raíz del proyecto:
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py migrate --noinput
```

> El proceso `release` de Railway se ejecuta automáticamente antes de cada despliegue. Con esto, las migraciones se aplican sin intervención manual.

---

### 1.2 SQLite en Railway — pérdida de datos en cada deploy

**Problema actual:** Railway usa un **sistema de archivos efímero**. Cualquier archivo escrito en disco (incluido `db.sqlite3`) se destruye con cada nuevo despliegue o reinicio del servicio.

**Impacto:** Se pierden todos los datos del entorno de pruebas en cada deploy. Hace imposible mantener usuarios, vehículos o registros entre sesiones de prueba.

**Solución:** Aprovisionar el plugin de **PostgreSQL en Railway** (se añade desde el panel del proyecto en un clic). Railway inyecta automáticamente la variable `DATABASE_URL`.

Añadir a `requirements.txt`:
```
dj-database-url==2.3.0
psycopg2-binary==2.9.10
```

Actualizar `settings.py`:
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
    )
}
```

> Con `release: python manage.py migrate --noinput` en el Procfile, las migraciones se aplican automáticamente en cada deploy sin pasos manuales.

---

### 1.3 Variables de entorno, ALLOWED_HOSTS y CORS para frontend separado

**Problema actual:**
- `SECRET_KEY` está hardcodeada en `settings.py` como fallback inseguro.
- `DEBUG = True` es el valor por defecto si la variable de entorno no está definida.
- `ALLOWED_HOSTS = []` está vacío — Django rechazará todas las peticiones externas.
- `CORS_ALLOW_ALL_ORIGINS = True` permite peticiones desde cualquier dominio.

**Impacto:** Con `ALLOWED_HOSTS = []` Django bloquea todas las peticiones de Railway con error 400. Con `CORS_ALLOW_ALL_ORIGINS = True`, cualquier sitio web puede hacer peticiones autenticadas a la API en nombre de un usuario real — especialmente problemático con el frontend en un dominio separado.

**Solución:** Configurar en Railway (panel → Variables) las siguientes variables:

| Variable | Valor de ejemplo |
|---|---|
| `SECRET_KEY` | cadena aleatoria de 50+ caracteres |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `tu-app.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | `https://tu-frontend.vercel.app` |
| `DATABASE_URL` | inyectada automáticamente por el plugin PostgreSQL |

Actualizar `settings.py`:
```python
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set.")

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Reemplazar CORS_ALLOW_ALL_ORIGINS = True por:
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
```

> Para el entorno de pruebas, `DEBUG = True` puede mantenerse temporalmente para facilitar la depuración, pero `ALLOWED_HOSTS` y `CORS_ALLOWED_ORIGINS` deben configurarse desde el primer deploy.

---

### 1.4 Bug en `VehicleViewSet` — campo `active` vs `is_active`

**Problema actual:** El modelo `Vehicle` usa el campo `is_active`, pero `VehicleViewSet` referencia `active` en dos lugares:

```python
# vehicles/views.py
filterset_fields = ['brand', 'year', 'active', 'user']   # ← campo inexistente en el modelo
queryset.filter(active=True)                               # ← campo inexistente en el modelo
```

**Impacto:** El filtro por estado lanza un error 500 o devuelve 0 resultados. La acción `list` no filtra vehículos inactivos, exponiendo registros que deberían estar ocultos.

**Solución:**
```python
# vehicles/views.py
filterset_fields = ['brand', 'year', 'is_active', 'user']
# ...
queryset = queryset.filter(is_active=True)
```

---

### 1.5 Archivos estáticos sin configuración para Railway

**Problema actual:** `STATIC_URL = 'static/'` está configurado pero no hay `STATIC_ROOT` definido ni `whitenoise` instalado. Sin esto, `collectstatic` falla y el panel de administración de Django no carga CSS/JS en Railway.

**Impacto:** El admin de Django no es usable visualmente en el entorno desplegado.

**Solución:** Añadir `whitenoise` (sirve estáticos directamente desde gunicorn, sin infraestructura adicional):
```
whitenoise==6.9.0
```

```python
# settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← inmediatamente después de SecurityMiddleware
    ...
]
```

Actualizar el `Procfile`:
```
web: python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py migrate --noinput
```

---

### 1.6 Paginación deshabilitada

**Problema actual:** La paginación está comentada en `REST_FRAMEWORK`:
```python
# 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
# 'PAGE_SIZE': 100,
```

**Impacto:** Si un usuario tiene muchos registros, todos se devuelven en una sola respuesta. En Railway con el plan gratuito (512 MB RAM), esto puede provocar un reinicio del proceso. El frontend también recibe payloads innecesariamente grandes.

**Solución:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    ...
}
```

---

## 🟡 Prioridad 2 — Importante (afecta correctitud y seguridad de datos)

### 2.1 Apps con modelos pero sin capa API

Las apps `access`, `notifications` y `errors` tienen modelos de datos completamente definidos pero no tienen views, serializers ni URLs. El sistema de observabilidad y notificaciones está diseñado pero completamente inactivo.

| App | Modelo | Propósito | Falta |
|-----|--------|-----------|-------|
| `access` | `Accesses` | Audit log de peticiones HTTP (método, path, status, IP, duración) | Middleware que lo popule + endpoint de consulta |
| `notifications` | `Notification` | Alertas para el usuario (pending/sent/read, con canal y scheduling) | Lógica de generación + endpoint `GET /api/notifications/` |
| `errors` | `Error` | Registro de errores 4xx/5xx ligado a `Accesses` | Handler de excepciones DRF + endpoint de consulta para staff |

**Impacto:** Las tablas existen en la base de datos pero nunca se pueblan. La infraestructura de observabilidad diseñada no aporta ningún valor.

**Acción recomendada — `access`:** Implementar un middleware que registre cada petición autenticada:
```python
# access/middleware.py
import time
from .models import Accesses

class AccessLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        if request.user.is_authenticated:
            Accesses.objects.create(
                user=request.user,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip_address=request.META.get('REMOTE_ADDR'),
                duration_ms=int((time.time() - start) * 1000),
            )
        return response
```

**Acción recomendada — `notifications`:** Crear notificaciones automáticamente cuando un tracker pasa a `is_due = True` (al actualizar kilómetros del vehículo). Exponer `GET /api/notifications/` para que el frontend las consulte.

**Acción recomendada — `errors`:** Registrar errores 5xx con un handler personalizado de excepciones en DRF:
```python
# config/exceptions.py
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and response.status_code >= 500:
        # Crear Error ligado al Accesses más reciente del usuario
        pass
    return response
```

---

### 2.2 Soft-delete no implementado en los endpoints DELETE

**Problema actual:** Los modelos tienen campos `active` / `is_active` para borrado lógico, pero los endpoints `DELETE` realizan borrado físico (comportamiento por defecto de DRF), incluyendo el `CASCADE` sobre registros asociados.

**Impacto:** Al eliminar un tracker, se pierden todos sus registers históricos. Al eliminar un vehículo, se pierden sus trackers y registers. Esto destruye el historial de mantenimiento.

**Solución:** Sobreescribir `perform_destroy` en cada ViewSet:
```python
# vehicles/views.py
def perform_destroy(self, instance):
    instance.is_active = False
    instance.save()

# trackers/views.py
def perform_destroy(self, instance):
    instance.active = False
    instance.save()

# registers/views.py
def perform_destroy(self, instance):
    instance.active = False
    instance.save()
    # Re-sincronizar el tracker usando el siguiente registro activo más reciente
    self._sync_tracker(instance)
```

---

### 2.3 Permisos a nivel de objeto (object-level permissions)

**Problema actual:** La seguridad se basa únicamente en filtrar el queryset. Si la lógica del queryset cambia, un usuario podría acceder a recursos de otro con un ID conocido.

**Impacto:** Riesgo de modificación o borrado de datos de otro usuario mediante `PUT/DELETE /api/vehicles/{id}/` con un ID ajeno.

**Solución:** Crear un permiso reutilizable en `config/permissions.py`:
```python
from rest_framework.permissions import BasePermission

class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # Soporta Vehicle, Tracker y Register mediante resolución de propietario
        owner = getattr(obj, 'user',
                    getattr(getattr(obj, 'vehicle', None), 'user',
                        getattr(getattr(getattr(obj, 'tracker', None), 'vehicle', None), 'user', None)))
        return owner == request.user
```

---

### 2.4 Rate limiting en endpoints de autenticación

**Problema actual:** No hay límite de peticiones configurado.

**Impacto:** El endpoint `POST /api/auth/login/` es vulnerable a ataques de fuerza bruta. Relevante incluso en staging, ya que el entorno está desplegado públicamente en Railway.

**Solución:**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/min',
        'user': '300/min',
    }
}
```

---

### 2.5 Validación incorrecta de `kilometers` al editar un Register

**Problema actual:** Al hacer `PUT/PATCH` sobre un `Register` existente, el validador compara `kilometers` contra `tracker.last_service_km`, que puede haber sido calculado a partir del propio registro que se está editando.

**Impacto:** Editar un registro existente sin cambiar los kilómetros devuelve un error de validación falso positivo.

**Solución:** Excluir el propio registro de la comparación:
```python
def validate_kilometers(self, value):
    tracker_id = self.initial_data.get('tracker')
    if tracker_id:
        from trackers.models import Tracker
        try:
            t = Tracker.objects.get(pk=tracker_id)
            qs = Register.objects.filter(tracker=t, active=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            prev = qs.order_by('-kilometers').first()
            if prev and value < prev.kilometers:
                raise serializers.ValidationError(
                    'kilometers cannot be less than the previous register kilometers.'
                )
        except Tracker.DoesNotExist:
            pass
    return value
```

---

### 2.6 Campo `tracker_at` no editable en Register

**Problema actual:** `Register.tracker_at = models.DateTimeField(auto_now_add=True)` fija siempre la fecha al momento de creación del registro. No es posible registrar un servicio pasado con su fecha real.

**Impacto:** El historial de mantenimiento muestra fechas incorrectas para servicios ingresados retroactivamente. Afecta gráficas y reportes en el frontend.

**Solución:**
```python
# registers/models.py
from django.utils import timezone
tracker_at = models.DateTimeField(default=timezone.now)
```

Remover `tracker_at` de `read_only_fields` en el serializer y añadir una nueva migración.

---

## 🟢 Prioridad 3 — Deseable (mejora la experiencia, la observabilidad y el desarrollo)

### 3.1 Tests automatizados

**Problema actual:** Todos los archivos `tests.py` están vacíos.

**Impacto:** Sin tests, cada iteración en staging puede romper funcionalidad existente sin detectarse. El ciclo de corrección se alarga porque los bugs se descubren manualmente desde el frontend.

**Recomendación:** Implementar con `pytest-django`:
```
pytest-django==4.9.0
pytest-cov==6.1.0
```

Casos mínimos a cubrir:
- Registro, login, refresh y logout.
- Un usuario no puede acceder ni modificar recursos de otro usuario.
- Lógica de `_sync_tracker` cuando se crea/edita/elimina un Register.
- Campo `is_due` cuando `vehicle.kilometers >= tracker.next_due_km`.
- Validaciones de año en Vehicle y de kilómetros en Register.

---

### 3.2 Documentación interactiva (OpenAPI / Swagger)

**Problema actual:** No hay documentación interactiva de la API.

**Impacto:** Con el frontend en un proyecto separado, el equipo de frontend depende de este documento para conocer los contratos de la API. Una UI Swagger permite explorar y probar endpoints directamente desde el navegador, reduciendo la fricción entre equipos.

**Recomendación:** Integrar `drf-spectacular`:
```
drf-spectacular==0.28.0
```

```python
# settings.py
INSTALLED_APPS += ['drf_spectacular']
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'
```

```python
# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

Disponible en `https://tu-app.up.railway.app/api/docs/` para cualquiera del equipo.

---

### 3.3 Historial de kilómetros del vehículo

**Problema actual:** `Vehicle.kilometers` es un campo escalar. Al actualizarlo se pierde el valor anterior. No hay traza del odómetro en el tiempo.

**Impacto:** El frontend no puede mostrar evolución del kilometraje. No es posible calcular km recorridos por período sin este historial.

**Recomendación:** Crear un modelo `KilometerLog` en la app `vehicles`:
```python
class KilometerLog(models.Model):
    vehicle     = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='km_logs')
    kilometers  = models.PositiveIntegerField()
    recorded_at = models.DateTimeField(auto_now_add=True)
```

Y crear un log automáticamente desde la acción `update_kilometers`:
```python
vehicle.kilometers = new_km
vehicle.save()
KilometerLog.objects.create(vehicle=vehicle, kilometers=new_km)
```

---

### 3.4 Endpoints de estadísticas y reportes

**Problema actual:** No hay endpoints de resumen o reportes. El frontend debe calcular todo en cliente.

**Casos de uso relevantes:**
- Gasto total por vehículo o por período.
- Lista de trackers vencidos del usuario (`is_due = True`).
- Kilómetros restantes hasta el próximo mantenimiento de cada tracker.

**Endpoints sugeridos:**
```
GET /api/vehicles/{id}/stats/   → gasto acumulado, km registrados, cantidad de trackers vencidos
GET /api/trackers/due/          → todos los trackers del usuario con is_due = True
GET /api/registers/summary/     → agrupación de gastos por mes
```

---

### 3.5 Internacionalización de mensajes

**Problema actual:** Los mensajes de error están hardcodeados en inglés. Si el frontend está en español, la experiencia es inconsistente para el usuario final.

**Recomendación:** Usar `gettext_lazy` en serializers y views, y configurar el idioma:
```python
# settings.py
LANGUAGE_CODE = 'es'

# serializers
from django.utils.translation import gettext_lazy as _
raise serializers.ValidationError(_('This email is already registered.'))
```

---

## Resumen de prioridades

| # | Item | Prioridad | Área |
|---|------|-----------|------|
| 1.1 | Procfile + gunicorn para Railway | 🔴 1 | Despliegue |
| 1.2 | PostgreSQL + dj-database-url (SQLite es efímero en Railway) | 🔴 1 | Infraestructura |
| 1.3 | Variables de entorno + ALLOWED_HOSTS + CORS para frontend separado | 🔴 1 | Seguridad / Despliegue |
| 1.4 | Bug `active` vs `is_active` en VehicleViewSet | 🔴 1 | Bug |
| 1.5 | Whitenoise para archivos estáticos en Railway | 🔴 1 | Despliegue |
| 1.6 | Paginación habilitada | 🔴 1 | Performance |
| 2.1 | Implementar capa API de `access`, `notifications` y `errors` | 🟡 2 | Feature / Observabilidad |
| 2.2 | Soft-delete en endpoints DELETE | 🟡 2 | Correctitud |
| 2.3 | Object-level permissions (`IsOwnerOrStaff`) | 🟡 2 | Seguridad |
| 2.4 | Rate limiting en endpoints de autenticación | 🟡 2 | Seguridad |
| 2.5 | Validación de `kilometers` en update de Register | 🟡 2 | Bug |
| 2.6 | Campo `tracker_at` editable | 🟡 2 | UX |
| 3.1 | Tests automatizados | 🟢 3 | Calidad |
| 3.2 | Documentación Swagger/OpenAPI | 🟢 3 | DX |
| 3.3 | Historial de kilómetros (`KilometerLog`) | 🟢 3 | Feature |
| 3.4 | Endpoints de estadísticas y reportes | 🟢 3 | Feature |
| 3.5 | Internacionalización de mensajes | 🟢 3 | UX |
