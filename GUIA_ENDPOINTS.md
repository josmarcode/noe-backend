# Guía de Desarrollo de Endpoints - Proyecto NOE

## 📋 Estado Actual del Proyecto

### ✅ Configuración Completada
- ✅ Django 6.0.1 instalado
- ✅ Django REST Framework 3.16.1 instalado
- ✅ Modelos de base de datos creados y migrados
- ✅ Estructura de apps bien organizada
- ✅ Variables de entorno configuradas (python-dotenv)
- ✅ Modelo de usuario personalizado (CustomUser)

### ⚠️ Pendiente para Producción de Endpoints
- ❌ **Falta crear serializadores** para cada modelo
- ❌ **Falta crear views/viewsets** para los endpoints
- ❌ **Falta configurar URLs** para las apps
- ✅ **Incluido**: Autenticación JWT con djangorestframework-simplejwt
- ⚠️ **Recomendado**: Configurar CORS si se usará desde frontend separado
- ⚠️ **Recomendado**: Configurar paginación global en REST Framework

### 🎯 Apps del Proyecto
1. **accounts** - Gestión de usuarios (CustomUser)
2. **vehicles** - Gestión de vehículos
3. **trackers** - Seguimiento de mantenimientos
4. **registers** - Registros de servicios
5. **notifications** - Sistema de notificaciones
6. **access** - Log de accesos
7. **errors** - Log de errores

---

## 🚀 Configuración Previa Recomendada

### 1. Instalar Paquetes Necesarios

```bash
# Instalar JWT para autenticación
pip install djangorestframework-simplejwt

# Para filtrado avanzado
pip install django-filter

# Para CORS (frontend separado)
pip install django-cors-headers

# Actualizar requirements
pip freeze > requirements.txt
```

### 2. Configurar REST Framework y JWT en settings.py

Agregar al final de `config/settings.py`:

```python
from datetime import timedelta

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}
```

### 3. Configurar CORS (si frontend está separado)

Agregar en `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Al inicio
    'django.middleware.security.SecurityMiddleware',
    # ...
]

# Configuración CORS (desarrollo)
CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo
# Para producción, especificar orígenes:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]
```

### 4. Agregar rest_framework_simplejwt.token_blacklist a INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Para blacklist de tokens
    'corsheaders',
    'django_filters',
    # ...
]
```

### 5. Correr Migraciones para Blacklist de Tokens

```bash
python manage.py migrate
```

---

## 🔐 Endpoints de Autenticación

### Crear Serializadores de Usuario

Crear archivo `accounts/serializers.py`:

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializador para información del usuario"""
    vehicles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'vehicles_count',
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_vehicles_count(self, obj):
        return obj.vehicles.filter(active=True).count()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializador para registro de nuevos usuarios"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirmar contraseña'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializador para cambio de contraseña"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas no coinciden."}
            )
        return attrs
```

### Crear Views de Autenticación

En `accounts/views.py`:

```python
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Endpoint para registro de nuevos usuarios"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar tokens para el nuevo usuario
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Usuario registrado exitosamente'
        }, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Los usuarios solo pueden ver su propio perfil, excepto staff
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña del usuario actual"""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Verificar contraseña antigua
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': ['Contraseña incorrecta.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Establecer nueva contraseña
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Contraseña actualizada exitosamente.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Cerrar sesión (blacklist del refresh token)"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Sesión cerrada exitosamente.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
```

### Configurar URLs de Autenticación

Crear archivo `accounts/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import RegisterView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT Endpoints
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User Management
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]
```

### Incluir URLs de Autenticación en config/urls.py

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),  # Endpoints de autenticación
    path('api/', include('vehicles.urls')),
    # ... otros endpoints
]
```

---

## 📝 Guía Paso a Paso: Crear un Endpoint

### Ejemplo Práctico: CRUD de Vehículos

#### Paso 1: Crear Serializador

Crear archivo `vehicles/serializers.py`:

```python
from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    # Agregar campos calculados o relacionados
    owner_username = serializers.CharField(source='user.username', read_only=True)
    trackers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'user',
            'brand',
            'model',
            'year',
            'name',
            'kilometers',
            'created_at',
            'updated_at',
            'active',
            'owner_username',  # Campo calculado
            'trackers_count',  # Campo método
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_trackers_count(self, obj):
        """Contar trackers activos del vehículo"""
        return obj.trackers.filter(active=True).count()
    
    def validate_year(self, value):
        """Validación personalizada para año"""
        if value < 1900 or value > 2030:
            raise serializers.ValidationError("Año inválido")
        return value

# Serializador simplificado para listados
class VehicleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'brand', 'model', 'year', 'name', 'kilometers']
```

#### Paso 2: Crear ViewSet

En `vehicles/views.py`:

```python
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Vehicle
from .serializers import VehicleSerializer, VehicleListSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD completo de vehículos
    
    Endpoints automáticos:
    - GET    /api/vehicles/          - Listar todos
    - POST   /api/vehicles/          - Crear nuevo
    - GET    /api/vehicles/{id}/     - Detalle de uno
    - PUT    /api/vehicles/{id}/     - Actualizar completo
    - PATCH  /api/vehicles/{id}/     - Actualizar parcial
    - DELETE /api/vehicles/{id}/     - Eliminar
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    
    # Filtrado y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'year', 'active', 'user']
    search_fields = ['brand', 'model', 'name']
    ordering_fields = ['created_at', 'year', 'kilometers']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Personalizar queryset - optimizar consultas"""
        queryset = super().get_queryset()
        
        # Optimización: traer relaciones en una sola query
        queryset = queryset.select_related('user')
        queryset = queryset.prefetch_related('trackers')
        
        # Filtrar por usuario (solo ver sus propios vehículos, excepto staff)
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Solo vehículos activos por defecto
        if self.action == 'list':
            queryset = queryset.filter(active=True)
        
        return queryset
    
    def get_serializer_class(self):
        """Usar serializador diferente según la acción"""
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer
    
    def perform_create(self, serializer):
        """Personalizar creación - asignar usuario actual"""
        serializer.save(user=self.request.user)
    
    # Endpoint personalizado
    @action(detail=True, methods=['post'])
    def update_kilometers(self, request, pk=None):
        """
        Endpoint personalizado: POST /api/vehicles/{id}/update_kilometers/
        Body: {"kilometers": 50000}
        """
        vehicle = self.get_object()
        new_km = request.data.get('kilometers')
        
        if not new_km:
            return Response(
                {'error': 'Debe proporcionar el campo kilometers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_km = int(new_km)
            if new_km < vehicle.kilometers:
                return Response(
                    {'error': 'Los kilómetros no pueden disminuir'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            vehicle.kilometers = new_km
            vehicle.save()
            
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Valor de kilómetros inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def by_brand(self, request):
        """
        Endpoint personalizado: GET /api/vehicles/by_brand/?brand=Toyota
        """
        brand = request.query_params.get('brand')
        if not brand:
            return Response(
                {'error': 'Debe proporcionar el parámetro brand'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vehicles = self.get_queryset().filter(brand__icontains=brand)
        serializer = self.get_serializer(vehicles, many=True)
        return Response(serializer.data)
```

#### Paso 3: Configurar URLs

Crear archivo `vehicles/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
```

#### Paso 4: Incluir en URLs Principales

Modificar `config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('vehicles.urls')),
    # Agregar más apps según necesites
    # path('api/', include('trackers.urls')),
    # path('api/', include('registers.urls')),
]
```

---

## 🗄️ Acceso a Datos de la Base de Datos

### 1. Consultas Básicas con Django ORM

```python
from vehicles.models import Vehicle
from trackers.models import Tracker
from accounts.models import CustomUser

# Obtener todos los registros
vehicles = Vehicle.objects.all()

# Filtrar
active_vehicles = Vehicle.objects.filter(active=True)
toyota_vehicles = Vehicle.objects.filter(brand='Toyota')

# Obtener uno
vehicle = Vehicle.objects.get(id=1)
# O de forma segura:
from django.shortcuts import get_object_or_404
vehicle = get_object_or_404(Vehicle, id=1)

# Crear
vehicle = Vehicle.objects.create(
    user_id=1,
    brand='Toyota',
    model='Corolla',
    year=2020,
    name='Mi Toyota',
    kilometers=50000
)

# Actualizar
vehicle.kilometers = 60000
vehicle.save()

# O actualización masiva
Vehicle.objects.filter(year__lt=2010).update(active=False)

# Eliminar (soft delete recomendado)
vehicle.active = False
vehicle.save()

# Eliminar físicamente
vehicle.delete()
```

### 2. Consultas con Relaciones

```python
# Acceso a relaciones ForeignKey (de hijo a padre)
tracker = Tracker.objects.get(id=1)
vehicle_of_tracker = tracker.vehicle
user_of_vehicle = tracker.vehicle.user

# Acceso a relaciones inversas (de padre a hijo)
vehicle = Vehicle.objects.get(id=1)
trackers = vehicle.trackers.all()  # related_name='trackers'
active_trackers = vehicle.trackers.filter(active=True)

# Usuario y sus vehículos
user = CustomUser.objects.get(id=1)
user_vehicles = user.vehicles.all()

# Vehículo y sus notificaciones
vehicle_notifications = vehicle.notifications.filter(status='pending')
```

### 3. Optimización de Consultas

```python
# Evitar N+1 queries con select_related (ForeignKey)
vehicles = Vehicle.objects.select_related('user').all()
# Ahora vehicle.user no hace query adicional

# Evitar N+1 queries con prefetch_related (Many)
vehicles = Vehicle.objects.prefetch_related('trackers').all()
# Ahora vehicle.trackers.all() no hace query adicional

# Combinados
vehicles = Vehicle.objects.select_related('user').prefetch_related('trackers', 'notifications').all()

# Solo traer campos específicos
vehicles = Vehicle.objects.values('id', 'brand', 'model')
# Retorna diccionarios en lugar de objetos

# O con values_list para tuplas
brands = Vehicle.objects.values_list('brand', flat=True).distinct()
```

### 4. Consultas Avanzadas

```python
from django.db.models import Q, F, Count, Avg, Sum
from django.db.models.functions import Lower

# Operadores Q para OR y NOT
vehicles = Vehicle.objects.filter(
    Q(brand='Toyota') | Q(brand='Honda')
)

vehicles = Vehicle.objects.filter(
    Q(year__gte=2015) & ~Q(brand='Ford')
)

# Expresiones F para comparar campos
# Vehículos que necesitan servicio (km actual >= próximo servicio)
trackers_due = Tracker.objects.filter(
    vehicle__kilometers__gte=F('next_due_km')
)

# Agregaciones
from django.db.models import Count, Avg

# Contar trackers por vehículo
vehicle_stats = Vehicle.objects.annotate(
    num_trackers=Count('trackers'),
    avg_interval=Avg('trackers__interval_value')
)

for vehicle in vehicle_stats:
    print(f"{vehicle.name}: {vehicle.num_trackers} trackers")

# Agrupar por campo
from django.db.models import Count
brand_counts = Vehicle.objects.values('brand').annotate(
    total=Count('id')
).order_by('-total')

# Búsqueda case-insensitive
vehicles = Vehicle.objects.filter(brand__iexact='toyota')

# Búsqueda parcial
vehicles = Vehicle.objects.filter(name__icontains='corolla')

# Rango de fechas
from datetime import datetime, timedelta
recent_vehicles = Vehicle.objects.filter(
    created_at__gte=datetime.now() - timedelta(days=30)
)

# Ordenamiento
vehicles = Vehicle.objects.order_by('-created_at', 'brand')

# Limitar resultados
latest_10 = Vehicle.objects.order_by('-created_at')[:10]
```

### 5. Transacciones

```python
from django.db import transaction

# Asegurar que todas las operaciones se ejecuten o ninguna
@transaction.atomic
def create_vehicle_with_trackers(user, vehicle_data, trackers_data):
    vehicle = Vehicle.objects.create(user=user, **vehicle_data)
    
    for tracker_data in trackers_data:
        Tracker.objects.create(vehicle=vehicle, **tracker_data)
    
    return vehicle

# O con context manager
from django.db import transaction

try:
    with transaction.atomic():
        vehicle = Vehicle.objects.create(...)
        Tracker.objects.create(vehicle=vehicle, ...)
        # Si algo falla, todo se revierte
except Exception as e:
    print(f"Error: {e}")
```

---

## 📚 Tipos de Views en Django REST Framework

### 1. APIView (Más control, más código)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class VehicleListView(APIView):
    def get(self, request):
        vehicles = Vehicle.objects.all()
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 2. GenericAPIView + Mixins (Balance)

```python
from rest_framework import generics

class VehicleListCreateView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
```

### 3. ViewSet (Menos código, CRUD automático) - **RECOMENDADO**

```python
from rest_framework import viewsets

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    # Automáticamente crea: list, create, retrieve, update, destroy
```

---

## 🧪 Probar los Endpoints

### 1. Flujo de Autenticación

#### Paso 1: Registrar un nuevo usuario

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan",
    "email": "juan@example.com",
    "password": "MiPassword123!",
    "password2": "MiPassword123!",
    "first_name": "Juan",
    "last_name": "Pérez"
  }'
```

**Respuesta:**
```json
{
  "user": {
    "id": 1,
    "username": "juan",
    "email": "juan@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "is_active": true,
    "date_joined": "2026-02-16T10:30:00Z",
    "vehicles_count": 0
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Usuario registrado exitosamente"
}
```

#### Paso 2: Login (obtener tokens)

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan",
    "password": "MiPassword123!"
  }'
```

**Respuesta:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Paso 3: Usar el token de acceso

Guardar el token de acceso en una variable:
```bash
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 2. Endpoints Protegidos con Autenticación

```bash
# GET - Obtener información del usuario actual
curl http://localhost:8000/api/auth/users/me/ \
  -H "Authorization: Bearer $TOKEN"

# GET - Listar vehículos (solo los del usuario autenticado)
curl http://localhost:8000/api/vehicles/ \
  -H "Authorization: Bearer $TOKEN"

# GET - Detalle de un vehículo
curl http://localhost:8000/api/vehicles/1/ \
  -H "Authorization: Bearer $TOKEN"

# POST - Crear vehículo (se asigna automáticamente al usuario autenticado)
curl -X POST http://localhost:8000/api/vehicles/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "name": "Mi Carro",
    "kilometers": 50000
  }'

# PUT - Actualizar completo
curl -X PUT http://localhost:8000/api/vehicles/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "name": "Mi Carro Actualizado",
    "kilometers": 60000
  }'

# PATCH - Actualizar parcial
curl -X PATCH http://localhost:8000/api/vehicles/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"kilometers": 70000}'

# DELETE - Eliminar
curl -X DELETE http://localhost:8000/api/vehicles/1/ \
  -H "Authorization: Bearer $TOKEN"

# Filtrado
curl "http://localhost:8000/api/vehicles/?brand=Toyota&year=2020" \
  -H "Authorization: Bearer $TOKEN"

# Búsqueda
curl "http://localhost:8000/api/vehicles/?search=corolla" \
  -H "Authorization: Bearer $TOKEN"

# Ordenamiento
curl "http://localhost:8000/api/vehicles/?ordering=-created_at" \
  -H "Authorization: Bearer $TOKEN"

# Paginación
curl "http://localhost:8000/api/vehicles/?page=2" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Renovar Token de Acceso

Cuando el token de acceso expire (después de 1 hora), usar el refresh token:

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Respuesta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // Nuevo refresh token
}
```

### 4. Verificar Token

```bash
curl -X POST http://localhost:8000/api/auth/token/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

### 5. Cambiar Contraseña

```bash
curl -X POST http://localhost:8000/api/auth/users/change_password/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "MiPassword123!",
    "new_password": "NuevaPassword456!",
    "new_password2": "NuevaPassword456!"
  }'
```

### 6. Cerrar Sesión (Logout)

```bash
curl -X POST http://localhost:8000/api/auth/users/logout/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

### 7. Usar el Navegador

```
http://localhost:8000/api/vehicles/
```

DRF proporciona una interfaz web interactiva. Deberás hacer login primero en:
```
http://localhost:8000/api/auth/login/
```

### 8. Usar herramientas GUI

- **Postman**: https://www.postman.com/
- **Insomnia**: https://insomnia.rest/
- **Thunder Client**: Extensión de VSCode

#### Configurar Authentication en Postman/Insomnia:

1. Crear request de login
2. Extraer el `access` token de la respuesta
3. En las siguientes requests, agregar Header:
   - **Key**: `Authorization`
   - **Value**: `Bearer {access_token}`

#### Hacer Endpoints Públicos (Opcional)

Si necesitas que algunos endpoints no requieran autenticación:

```python
from rest_framework.permissions import AllowAny

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    
    def get_permissions(self):
        """Personalizar permisos por acción"""
        if self.action in ['list', 'retrieve']:  # Solo lectura pública
            return [AllowAny()]
        return [IsAuthenticated()]  # Escritura requiere autenticación
```

---

## 🎯 Próximos Pasos Recomendados

### 1. Crear Serializadores para Todas las Apps

```bash
# Crear estos archivos:
touch accounts/serializers.py
touch vehicles/serializers.py
touch trackers/serializers.py
touch registers/serializers.py
touch notifications/serializers.py
touch access/serializers.py
touch errors/serializers.py
```

### 2. Crear Views para Todas las Apps

Similar al ejemplo de `vehicles/views.py` para cada app.

### 3. Crear URLs para Todas las Apps

```bash
touch accounts/urls.py
touch vehicles/urls.py
touch trackers/urls.py
touch registers/urls.py
touch notifications/urls.py
touch access/urls.py
touch errors/urls.py
```

### 4. Estructura Recomendada de URLs

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('vehicles.urls')),
    path('api/', include('trackers.urls')),
    path('api/', include('registers.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('access.urls')),
    path('api/', include('errors.urls')),
]
```

### 5. Instalar Paquetes Adicionales Útiles (Opcional)

```bash
# Para generar documentación automática de API
pip install drf-yasg
# o
pip install drf-spectacular

# Actualizar requirements
pip freeze > requirements.txt
```

---

## 📖 Recursos Adicionales

- **Django REST Framework Docs**: https://www.django-rest-framework.org/
- **Django ORM Docs**: https://docs.djangoproject.com/en/6.0/topics/db/queries/
- **DRF Tutorial**: https://www.django-rest-framework.org/tutorial/quickstart/

---

## ✅ Checklist de Implementación

### Configuración Inicial
- [ ] Instalar paquetes: `djangorestframework-simplejwt`, `django-filter`, `django-cors-headers`
- [ ] Configurar REST_FRAMEWORK con autenticación JWT en settings.py
- [ ] Configurar SIMPLE_JWT en settings.py
- [ ] Agregar `rest_framework_simplejwt.token_blacklist` a INSTALLED_APPS
- [ ] Configurar django-cors-headers en settings.py
- [ ] Correr migraciones: `python manage.py migrate`

### Autenticación
- [ ] Crear `accounts/serializers.py` (UserSerializer, RegisterSerializer, ChangePasswordSerializer)
- [ ] Crear `accounts/views.py` (RegisterView, UserViewSet)
- [ ] Crear `accounts/urls.py` con endpoints de auth
- [ ] Incluir `path('api/auth/', include('accounts.urls'))` en config/urls.py
- [ ] Probar registro, login, refresh token, logout

### Endpoints de Negocio
- [ ] Crear serializers.py para cada app (vehicles, trackers, registers, etc.)
- [ ] Crear views.py con ViewSets para cada app
- [ ] Configurar permisos y filtrado por usuario
- [ ] Crear urls.py para cada app
- [ ] Incluir URLs de apps en config/urls.py
- [ ] Probar endpoints con autenticación (Bearer token)

### Pruebas y Documentación
- [ ] Probar todos los endpoints con Postman/Insomnia
- [ ] Verificar que los usuarios solo accedan a sus propios datos
- [ ] Documentar endpoints (opcional: drf-yasg o drf-spectacular)
- [ ] Agregar tests (opcional pero recomendado)

---

**¡El proyecto está listo con autenticación JWT desde el inicio!** 🚀🔐

Ahora puedes implementar los serializadores y views para cada app, siguiendo los patrones de esta guía.
