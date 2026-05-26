# Guion del Vídeo Explicativo — Trabajo 2: Pooling de Conexiones

> **Duración estimada:** 8-10 minutos  
> **Formato:** Grabación de pantalla + explicación oral

---

## Slide 1: Introducción (1 minuto)

**Qué decir:**

> "Hola, en este vídeo voy a explicar el Trabajo 2 sobre Pooling de Conexiones 
> en bases de datos. El objetivo es entender por qué el patrón Singleton tiene 
> límites en entornos multiusuario y cómo el pooling de conexiones resuelve 
> este problema."

**Qué mostrar:**
- El README.md abierto en el editor, mostrando el índice.
- La estructura del proyecto en el explorador de archivos.

---

## Slide 2: El coste de abrir una conexión TCP/IP (2 minutos)

**Qué decir:**

> "Cada vez que nuestra aplicación Python se conecta a PostgreSQL, ocurren 
> varias cosas costosas. Primero, el handshake TCP de 3 vías: el cliente 
> envía un SYN, el servidor responde con SYN-ACK, y el cliente confirma con ACK. 
> Son 3 paquetes de red solo para establecer la conexión."
>
> "Después viene la autenticación: PostgreSQL comprueba nuestras credenciales. 
> Y lo más costoso: PostgreSQL crea un proceso nuevo para cada conexión, 
> con un fork del proceso principal y asignación de memoria."
>
> "Si multiplicamos todo esto por 200 operaciones, el overhead acumulado 
> puede ser de varios segundos."

**Qué mostrar:**
- El diagrama del handshake TCP en el README.
- La tabla de costes por etapa.

---

## Slide 3: Singleton vs Pool de conexiones (2 minutos)

**Qué decir:**

> "La primera solución que se nos ocurre es el patrón Singleton: crear una 
> sola conexión y reutilizarla para todo. Y funciona bien... para un solo 
> usuario."
>
> "El problema viene cuando tenemos múltiples usuarios. Con Singleton, todos 
> compiten por la misma conexión. Es como tener un solo cajero en un 
> supermercado: todos hacen cola."
>
> "El Pool de conexiones resuelve esto. Mantiene varias conexiones abiertas 
> y listas para usar. Cuando un usuario necesita una, el pool le da una libre. 
> Cuando termina, la devuelve al pool en lugar de cerrarla. Es como tener 
> 5 cajeros: puedes atender a 5 clientes a la vez."

**Qué mostrar:**
- Los diagramas ASCII del README (Singleton vs Pool).
- Abrir `singleton.py` y señalar la clase `SingletonConnection`.

---

## Slide 4: Parámetros de configuración del Pool (1 minuto)

**Qué decir:**

> "Un pool necesita configurarse correctamente. Los parámetros más importantes 
> son: minconn, que es el número de conexiones que se crean al inicio; maxconn, 
> el límite máximo; pool_timeout, cuánto espera un usuario si no hay conexiones 
> libres; y pool_recycle, que renueva conexiones antiguas para evitar problemas."

**Qué mostrar:**
- La tabla de parámetros en el README.
- Abrir `config.py` y señalar `POOL_MIN_CONN` y `POOL_MAX_CONN`.

---

## Slide 5: Demo del código (2 minutos)

**Qué decir:**

> "Voy a mostrar rápidamente los 4 archivos de ejemplo. 
>
> En `sin_pool.py`, veis cómo cada inserción abre una conexión nueva con 
> psycopg2.connect() y la cierra al final. Es el anti-patrón.
>
> En `pool_psycopg2.py`, usamos ThreadedConnectionPool. Fijaos en que usamos 
> getconn() para obtener una conexión del pool y putconn() para devolverla. 
> Nunca la cerramos.
>
> En `pool_sqlalchemy.py`, SQLAlchemy gestiona el pool automáticamente. 
> Con el bloque 'with engine.connect()', la conexión se devuelve al pool 
> al salir del bloque."

**Qué mostrar:**
- Abrir y recorrer brevemente `sin_pool.py`, `pool_psycopg2.py` y `pool_sqlalchemy.py`.
- Señalar las líneas clave: `connect()` vs `getconn()`/`putconn()`.

---

## Slide 6: Test de estrés y resultados (2 minutos)

**Qué decir:**

> "Ahora viene la parte interesante: el test de estrés. Voy a ejecutar 
> 200 inserciones con cada estrategia y comparar los tiempos."
>
> *Ejecutar `python test_estres.py` en la terminal.*
>
> "Como podéis ver en la tabla y la gráfica, la diferencia es brutal. 
> Sin pool tarda [X] segundos, mientras que con pool tarda solo [X] segundos. 
> Eso es [X] veces más rápido."
>
> "La conclusión es clara: en cualquier aplicación real, debemos usar un 
> pool de conexiones. El Singleton puede servir para scripts simples, 
> pero en un servidor web o una API con múltiples usuarios, el pool es 
> imprescindible."

**Qué mostrar:**
- Ejecutar `python test_estres.py` en vivo.
- Mostrar la tabla de resultados en la consola.
- Abrir la gráfica `resultados/comparativa.png`.

---

## Cierre (30 segundos)

**Qué decir:**

> "En resumen: abrir conexiones es caro, el Singleton es limitado, 
> y el pool de conexiones es la solución correcta para producción. 
> Gracias por ver el vídeo."

---

## Consejos para la grabación

1. **Software:** Usa OBS Studio (gratuito) o la grabación de pantalla de Windows (Win+G).
2. **Resolución:** Graba a 1920×1080 para que el código se lea bien.
3. **Terminal:** Pon la fuente de la terminal grande (16-18px) para que se vea en el vídeo.
4. **Ritmo:** No corras. Es mejor un vídeo pausado y claro que uno rápido e incomprensible.
5. **Errores:** Si te equivocas, simplemente repite la frase. No hace falta empezar de cero.
