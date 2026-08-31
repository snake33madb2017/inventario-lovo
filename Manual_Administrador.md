# Manual de Uso para el Administrador (Encargado) - Inventario Lovo

Bienvenido al manual de uso de la aplicación web progresiva (PWA) de **Inventario Lovo**. Este documento detalla todas las funciones exclusivas para tu rol de `encargado`, diseñadas para facilitarte el control del inventario y la gestión de tu equipo.

---

## 1. Acceso a la Aplicación

Para utilizar las funciones de administrador, debes iniciar sesión con tus credenciales.
1. Abre la aplicación en tu navegador o desde el icono en la pantalla de inicio de tu móvil.
2. En la pantalla de **Login**, introduce tu **DNI** y tu **Contraseña**.
3. Si tus credenciales tienen el rol de `encargado`, la aplicación te dará la bienvenida y mostrará los controles avanzados de administración.

> [!NOTE]
> El DNI debe ingresarse exactamente como se registró (incluyendo la letra, si aplica).

---

## 2. Gestión Diaria del Inventario

Al igual que los camareros, puedes registrar el inventario usando la voz o manualmente, pero tú tienes opciones adicionales para el control de los datos.

### 2.1. Dictado por Voz y Registro Manual
- **Por Voz:** Toca el botón rojo del micrófono y dicta la cantidad seguida del producto (ej: *"Tres Brugal"*). La aplicación lo reconocerá y lo guardará automáticamente en la categoría correspondiente.
- **Manual:** Si hay mucho ruido, pulsa el botón del teclado (⌨️) e introduce el texto de la misma manera.
- **Deshacer:** Si te equivocas, puedes pulsar el botón **Deshacer (⟲)**. Como encargado, al deshacer **borrarás el último registro de toda la base de datos**, independientemente de quién lo haya introducido (los camareros solo pueden borrar sus propios registros).

### 2.2. Descargar Reporte (Excel)
En la parte superior de la pantalla principal verás un botón verde con el icono de un documento (⬇️ Excel).
- Al pulsarlo, descargarás automáticamente un archivo Excel (`Inventario_Hoy.xlsx`) con todo el inventario registrado en el día actual, organizado en pestañas por categorías.

### 2.3. Borrar Inventario Mensual (Cierre)
Junto al botón de Excel, tienes un botón rojo de advertencia (🗑️ Mes).
- **¿Para qué sirve?** Al final de tu periodo de inventario (por ejemplo, a final de mes o de semana), una vez hayas descargado y guardado tu Excel de forma segura, puedes pulsar este botón para **borrar toda la base de datos** y empezar un nuevo inventario desde cero.

> [!CAUTION]
> **Peligro:** Esta acción borra TODOS los registros actuales. Asegúrate siempre de haber descargado el reporte en Excel antes de pulsarlo. El sistema te pedirá confirmación antes de proceder.

---

## 3. Panel de Configuración Avanzada

Como encargado, verás un botón gris con un icono de tuerca (⚙️) en la pantalla principal. Este botón te da acceso al **Panel de Configuración**, desde donde puedes gestionar cómo funciona la aplicación.

El panel está dividido en tres pestañas:

### 3.1. Pestaña: Usuarios
Aquí puedes ver todos los empleados que tienen acceso a la app.
- **Crear un nuevo usuario:**
  - Introduce su DNI, Nombre, Contraseña y selecciona su Rol (`camarero` o `encargado`).
  - Pulsa **Crear**.
- **Borrar usuario:**
  - Busca al usuario en la lista inferior y pulsa el botón **Borrar**. Ese usuario perderá el acceso inmediatamente.

### 3.2. Pestaña: Categorías
El inventario se organiza en categorías (Cristalería, Licores, Refrescos, etc.).
- **Añadir categoría:** Escribe el nombre de la nueva categoría y pulsa **Crear**. La categoría aparecerá inmediatamente en el menú desplegable de la pantalla principal.
- **Borrar categoría:** Busca la categoría en la lista y pulsa **Borrar**. 

> [!WARNING]
> No borres una categoría si aún hay productos de esa categoría en el inventario actual que no has exportado, para evitar desorganización en los datos.

### 3.3. Pestaña: Diccionario (Autocorrección)
El diccionario es la "inteligencia" de la app. Sirve para corregir automáticamente lo que el asistente de voz escucha mal.
- **¿Cómo funciona?** Si cuando dictas *"Coca-Cola"*, el móvil suele entender *"cocacola"*, puedes crear una regla.
- **Alias (lo que escucha la app):** Escribe cómo suele equivocarse la aplicación, por ejemplo: `cocacola`. (Siempre en minúsculas y sin tildes).
- **Nombre Real (lo que se guardará):** Escribe cómo quieres que aparezca en el Excel, por ejemplo: `Coca-Cola`.
- Al pulsar **Crear**, a partir de ese momento, cualquier camarero que dicte algo que contenga el "alias", será corregido automáticamente al "Nombre Real".

---

## 4. Solución de Problemas Comunes

- **El botón del micrófono no funciona:** Asegúrate de que el navegador tiene permisos para usar el micrófono. Si estás en un iPhone/Safari, debes pulsar la pantalla antes de que el audio se desbloquee.
- **No se guardan los registros:** Comprueba el indicador de estado en la parte superior derecha. Si dice "Desconectado" en rojo, significa que el móvil no tiene conexión a internet o el servidor está apagado.
- **El servidor está encendido pero sigo Desconectado:** Ve a la pantalla de Login y pulsa el botón de configuración (⚙️) abajo a la derecha. Escribe la dirección IP correcta del servidor (Ej: `http://192.168.1.50:8000`).

---
*Manual generado para Inventario Lovo. Versión 1.0.*
**Por : MDev - Soluciones Tecnológicas (Marco Daza)**
