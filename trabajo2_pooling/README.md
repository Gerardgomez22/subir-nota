# Trabajo 2: High Performance — Pooling de Conexiones

> **Módulo:** Acceso a Datos (2.º DAM)  
> **Objetivo:** Entender que el patrón Singleton tiene límites en entornos multiusuario y dominar las técnicas de pooling de conexiones para alto rendimiento.

---

## Índice

1. [Contenido Teórico](#contenido-teórico)
   - [El coste de abrir y cerrar una conexión TCP/IP](#1-el-coste-de-abrir-y-cerrar-una-conexión-tcpip)
   - [Singleton vs Pool de conexiones](#2-singleton-vs-pool-de-conexiones)
   - [Estrategias de gestión del Pool](#3-estrategias-de-gestión-del-pool)
2. [Parte Práctica](#parte-práctica)
3. [Instrucciones de Ejecución](#instrucciones-de-ejecución)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [Conclusiones](#conclusiones)

---

## Contenido Teórico

### 1. El coste de abrir y cerrar una conexión TCP/IP

Cada vez que una aplicación Python se conecta a PostgreSQL, se ejecuta un proceso costoso que involucra múltiples etapas a nivel de red y de servidor:

#### Etapa 1: Handshake TCP de 3 vías

Antes de poder enviar cualquier dato, cliente y servidor deben establecer una conexión TCP fiable. Esto requiere 3 intercambios de paquetes:

```
  Cliente                   Servidor (PostgreSQL)
     │                            │
     │─── SYN ──────────────────→ │   (1) "Quiero conectarme"
     │                            │
     │←── SYN + ACK ─────────────│   (2) "OK, te reconozco"
     │                            │
     │─── ACK ──────────────────→ │   (3) "Confirmado, empezamos"
     │                            │
```

Cada uno de estos paquetes tiene una latencia de red (en local ~0.1ms, en red ~1-5ms, en cloud ~10-50ms).

#### Etapa 2: Autenticación de PostgreSQL

Una vez establecida la conexión TCP, PostgreSQL debe verificar las credenciales:

1. El cliente envía el nombre de usuario y base de datos.
2. PostgreSQL consulta `pg_hba.conf` para determinar el método de autenticación.
3. Se ejecuta el protocolo de autenticación (MD5, SCRAM-SHA-256, etc.).
4. PostgreSQL verifica contra su catálogo interno.

#### Etapa 3: Creación del proceso backend

PostgreSQL utiliza un modelo de **un proceso por conexión**. Cada nueva conexión genera:

- Un `fork()` del proceso principal (postmaster).
- Asignación de memoria para el nuevo proceso (~5-10 MB).
- Inicialización de estructuras internas (catálogos, cachés, buffers).

#### Etapa 4: Cierre de la conexión

Al cerrar, se ejecuta el proceso inverso:

```
  Cliente                   Servidor (PostgreSQL)
     │                            │
     │─── FIN ──────────────────→ │   Liberación de recursos del backend
     │←── ACK ──────────────────│   Terminación del proceso hijo
     │←── FIN ──────────────────│   Liberación de memoria
     │─── ACK ──────────────────→ │   Conexión TCP cerrada
     │                            │
```

#### Coste total por conexión

| Concepto                  | Tiempo aproximado (local) | Tiempo aproximado (red) |
|---------------------------|:-------------------------:|:-----------------------:|
| Handshake TCP (3 vías)    | ~0.1 ms                   | ~3-15 ms                |
| Autenticación PostgreSQL  | ~0.5-1 ms                 | ~1-5 ms                 |
| Fork del proceso backend  | ~1-3 ms                   | ~1-3 ms                 |
| Cierre de conexión        | ~0.1 ms                   | ~1-5 ms                 |
| **Total por conexión**    | **~2-5 ms**               | **~6-28 ms**            |

Si multiplicamos este overhead por **200 operaciones**, el coste acumulado puede ser de **0.4 a 5.6 segundos** solo en abrir y cerrar conexiones, sin contar el trabajo real.

---

### 2. Singleton vs Pool de conexiones

#### Patrón Singleton

El patrón Singleton garantiza que solo existe **una única instancia** de la conexión en toda la aplicación:

```
  ┌──────────────────────────────────────────────────────┐
  │                    APLICACIÓN                         │
  │                                                      │
  │  Usuario A ──┐                                       │
  │              │                                       │
  │  Usuario B ──┼──→ [Singleton: 1 conexión] ──→ PostgreSQL
  │              │                                       │
  │  Usuario C ──┘                                       │
  │                                                      │
  │  ⚠ Los usuarios deben ESPERAR su turno (secuencial)  │
  └──────────────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Elimina el overhead de abrir/cerrar conexiones.
- ✅ Muy simple de implementar.

**Limitaciones:**
- ❌ **Cuello de botella**: con muchos usuarios concurrentes, todos compiten por la misma conexión.
- ❌ **Punto único de fallo**: si la conexión se cae, toda la aplicación queda sin acceso.
- ❌ **No es thread-safe**: compartir una conexión entre hilos puede provocar errores de concurrencia y corrupción de datos.
- ❌ **No escala**: un servidor web con 50 peticiones simultáneas no puede atenderlas con una sola conexión.

#### Pool de conexiones

Un Pool de conexiones mantiene un **conjunto de conexiones pre-creadas** listas para ser reutilizadas:

```
  ┌──────────────────────────────────────────────────────────────┐
  │                    APLICACIÓN                                 │
  │                                                              │
  │  Usuario A ──→ [Conexión 1] ──┐                              │
  │                               │                              │
  │  Usuario B ──→ [Conexión 2] ──┼──→ PostgreSQL                │
  │                               │                              │
  │  Usuario C ──→ [Conexión 3] ──┘                              │
  │                                                              │
  │  ✔ Cada usuario tiene su propia conexión del pool            │
  │  ✔ Las conexiones se reutilizan, no se abren/cierran         │
  │  ✔ Si el pool está lleno, el usuario espera brevemente       │
  └──────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ **Rendimiento**: elimina el overhead de abrir/cerrar conexiones TCP.
- ✅ **Concurrencia**: múltiples usuarios pueden trabajar en paralelo.
- ✅ **Resiliencia**: si una conexión falla, el pool la reemplaza automáticamente.
- ✅ **Control de recursos**: limita el número máximo de conexiones al servidor.
- ✅ **Thread-safe**: cada hilo recibe su propia conexión del pool.

---

### 3. Estrategias de gestión del Pool

Un pool bien configurado necesita ajustar varios parámetros:

#### Conexiones mínimas (`minconn` / `pool_size`)

Número de conexiones que se crean al iniciar el pool y se mantienen siempre abiertas.

- **Valor bajo** (1-2): ahorra memoria pero puede causar esperas iniciales.
- **Valor alto** (5-10): respuesta instantánea pero consume más recursos.
- **Recomendación**: establecer según el número habitual de usuarios concurrentes.

#### Conexiones máximas (`maxconn` / `max_overflow`)

Límite máximo de conexiones simultáneas permitidas.

- Protege al servidor de sobrecarga.
- PostgreSQL tiene un límite configurable (por defecto 100 conexiones).
- Si se alcanza el máximo, las nuevas peticiones deben esperar.

#### Tiempos de espera (`pool_timeout`)

Tiempo máximo (en segundos) que un cliente espera para obtener una conexión del pool.

- Si se excede el timeout, se lanza una excepción.
- Evita que la aplicación se quede bloqueada indefinidamente.
- Valor típico: 30 segundos.

#### Reciclado de conexiones (`pool_recycle`)

Tiempo tras el cual una conexión se cierra y se reabre automáticamente.

- Evita problemas con conexiones obsoletas (cortadas por firewall o timeout del servidor).
- Valor típico: 1800 segundos (30 minutos).

#### Pre-ping (`pool_pre_ping`)

Verificación de que una conexión sigue viva antes de usarla.

- Realiza un `SELECT 1` antes de entregar la conexión al usuario.
- Overhead mínimo (~0.1ms) pero evita errores de conexión cerrada.

#### Tabla resumen de parámetros

| Parámetro        | psycopg2.pool           | SQLAlchemy              | Descripción                         |
|------------------|-------------------------|-------------------------|-------------------------------------|
| Mínimas          | `minconn`               | `pool_size`             | Conexiones pre-creadas              |
| Máximas          | `maxconn`               | `pool_size + max_overflow` | Límite máximo                    |
| Timeout          | —                       | `pool_timeout`          | Espera máxima (seg)                 |
| Reciclado        | —                       | `pool_recycle`          | Renovación automática (seg)         |
| Pre-ping         | —                       | `pool_pre_ping`         | Verificación de conexión viva       |

> **Nota:** `psycopg2.pool` es más simple y tiene menos opciones de configuración. SQLAlchemy ofrece un sistema de pooling más sofisticado con más controles.

---

## Parte Práctica

El proyecto implementa 4 estrategias de conexión y un test de estrés comparativo:

| Archivo               | Estrategia                        | Descripción                                        |
|-----------------------|-----------------------------------|----------------------------------------------------|
| `sin_pool.py`         | Sin Pool                          | Conexión nueva para cada operación (anti-patrón)   |
| `singleton.py`        | Singleton                         | Una única conexión reutilizada                     |
| `pool_psycopg2.py`    | Pool psycopg2                     | `ThreadedConnectionPool` de psycopg2               |
| `pool_sqlalchemy.py`  | Pool SQLAlchemy                   | Pool integrado en el engine de SQLAlchemy          |
| `test_estres.py`      | **Test comparativo**              | 200 inserciones × 4 estrategias + gráfica          |

### Test de estrés

El test de estrés (`test_estres.py`) realiza **200 inserciones rápidas** con cada estrategia y mide:

- **Tiempo total** de las 200 inserciones.
- **Tiempo por inserción** (milisegundos).
- **Speedup** respecto a la estrategia más lenta (Sin Pool).

Los resultados se presentan en una tabla formateada y una **gráfica de barras** generada con matplotlib.

---

## Instrucciones de Ejecución

### Requisitos previos

- **Python 3.8+**
- **PostgreSQL** corriendo en `localhost:5432` (o usar Docker)

### Opción A: PostgreSQL local ya instalado

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar credenciales en config.py (si son diferentes de postgres/postgres)

# 3. Preparar la base de datos
python setup_db.py

# 4. Ejecutar los ejemplos individuales
python sin_pool.py
python singleton.py
python pool_psycopg2.py
python pool_sqlalchemy.py

# 5. Ejecutar el test de estrés completo
python test_estres.py
```

### Opción B: Usar Docker

```bash
# 1. Levantar PostgreSQL con Docker
docker-compose up -d

# 2. Esperar ~5 segundos a que arranque

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Preparar la base de datos
python setup_db.py

# 5. Ejecutar el test de estrés
python test_estres.py

# 6. (Opcional) Detener Docker al terminar
docker-compose down
```

---

## Estructura del Proyecto

```
trabajo2_pooling/
├── README.md               ← Este archivo (documentación teórica + instrucciones)
├── requirements.txt        ← Dependencias del proyecto
├── config.py               ← Configuración centralizada (host, puerto, pool, etc.)
├── docker-compose.yml      ← PostgreSQL con Docker (opcional)
├── setup_db.py             ← Preparación de la BBDD y tabla de pruebas
├── sin_pool.py             ← Ejemplo: conexión nueva cada vez (anti-patrón)
├── singleton.py            ← Ejemplo: patrón Singleton (una sola conexión)
├── pool_psycopg2.py        ← Ejemplo: pool con psycopg2.pool
├── pool_sqlalchemy.py      ← Ejemplo: pool con SQLAlchemy
├── test_estres.py          ← Test de estrés comparativo (200 inserciones)
├── guion_video.md          ← Guion para la grabación del vídeo explicativo
└── resultados/
    └── comparativa.png     ← Gráfica generada por el test de estrés
```

---

## Conclusiones

1. **Abrir una conexión nueva para cada operación es extremadamente costoso.** El handshake TCP, la autenticación y el fork del proceso backend suponen un overhead significativo que se multiplica con cada operación.

2. **El patrón Singleton mejora el rendimiento** al reutilizar una sola conexión, pero tiene limitaciones críticas en entornos multiusuario: cuello de botella, punto único de fallo y problemas de concurrencia.

3. **El Pool de conexiones es la solución correcta** para entornos de producción. Combina las ventajas del Singleton (reutilización) con soporte para concurrencia, resiliencia y control de recursos.

4. **SQLAlchemy ofrece un pool más sofisticado** que psycopg2, con funcionalidades como pre-ping, reciclado automático y control de overflow, lo que lo convierte en la opción preferida para aplicaciones complejas.

5. **La configuración del pool es crítica**: un pool mal dimensionado puede ser tan problemático como no tener pool. Los parámetros `minconn`, `maxconn`, `timeout` y `recycle` deben ajustarse según las características del entorno de producción.

---

## Recursos utilizados

- [Documentación de psycopg2.pool](https://www.psycopg.org/docs/pool.html)
- [Documentación de SQLAlchemy - Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PostgreSQL Documentation - Connection and Authentication](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [TCP/IP Three-Way Handshake](https://en.wikipedia.org/wiki/Handshake_(computing)#TCP_three-way_handshake)
