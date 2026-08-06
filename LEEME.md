# Inventario Lovo - Guía de Inicio Rápido

Esta es una aplicación de inventario por voz con una PWA para móviles y un servidor local en Python que escribe directamente a un archivo de Excel (`inventario.xlsx`).

## Paso 1: Instalar dependencias en la computadora (Servidor)

Asegúrate de tener Python instalado en tu computadora (PC/Mac). Abre una terminal (o Símbolo del Sistema) en esta carpeta y ejecuta:

```bash
pip install -r requirements.txt
```

## Paso 2: Ejecutar el Servidor Local y Obtener tu IP

En la misma terminal, ejecuta el servidor:

```bash
python server.py
```

El servidor quedará encendido escuchando peticiones.
Para que los móviles puedan conectarse, necesitas saber la IP local de esta computadora.

- **En Windows:** Abre otra terminal y escribe `ipconfig`. Busca la "Dirección IPv4" (por ejemplo: `192.168.1.50`).
- **En Mac:** Ve a Configuración del Sistema > Red > Wi-Fi > Detalles y busca tu Dirección IP.

## Paso 3: Conectar los móviles (Frontend PWA)

1. En esta misma carpeta, simplemente abre el archivo `index.html` en tu navegador de la computadora, o usa una extensión como "Live Server" en VSCode.
2. Si usas VSCode Live Server, puedes acceder desde tu móvil entrando a `http://TU_IP_LOCAL:5500/index.html`.
3. Al abrir la app en el móvil por primera vez, **te pedirá la IP del servidor**. Escribe la IP obtenida en el Paso 2 (ej. `192.168.1.50`).
4. **Instala la app:** En el navegador del móvil (Chrome o Safari), pulsa "Añadir a la pantalla de inicio" para instalarla como una app nativa (PWA).

### Notas sobre el Micrófono y Redes Locales
> **IMPORTANTE:** La API nativa de voz (`Web Speech API`) requiere que la página sea segura (`https://`) para funcionar de forma continua sin interrupciones. Como estamos en una red local (`http://`), algunos móviles podrían bloquear el micrófono o pedir permiso constantemente.
> 
> **Solución para Chrome en móviles (Android):**
> 1. Abre Google Chrome en el móvil.
> 2. En la barra de direcciones escribe: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
> 3. Añade la dirección de tu aplicación local (ej. `http://192.168.1.50:5500`) en el cuadro de texto.
> 4. Cambia el desplegable a **Enabled**.
> 5. Reinicia Chrome. Esto permitirá que la voz funcione perfectamente en la red local.

¡Listo! Ya puedes pulsar el micrófono y dictar "1.4 Brugal" o "24 Tónicas".
