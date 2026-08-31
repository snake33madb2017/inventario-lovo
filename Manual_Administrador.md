# Manual del Encargado (Por Marco Daza) 🍸

¡Hola! Como sabes, he estado trabajando duro en esta aplicación para que hacer el inventario deje de ser una tortura y podamos tener un control total del negocio desde el móvil. Como encargado, tú tienes las llaves del coche. Mientras que los camareros solo se dedican a contar botellas, tú tienes acceso a los paneles de gestión, cuadre y análisis. 

Aquí te dejo detallado todo lo que puedes hacer con la app.

---

## 1. El Acceso
Para entrar, simplemente usa el enlace que te pasé o abre la app si ya la instalaste en tu móvil.
- En la pantalla de **Login**, pon tu **DNI** (con letra incluida) y la **Contraseña** que te he asignado.
- Como tu cuenta tiene el súper-rol de `encargado`, la app te abrirá todas las funciones especiales en la barra superior.

---

## 2. Gestión Diaria y Cierres (La Magia)
Puedes hacer inventario igual que el resto (usando la voz o el teclado manual), pero tú eres el responsable de que los números cuadren al final.

### 2.1. Deshacer errores de cualquiera
Si ves que alguien la ha liado contando o te das cuenta de un error grave, usa el botón **Deshacer (⟲)**. Ojo con esto: a diferencia de los camareros (que solo pueden borrar lo suyo), si tú pulsas ese botón, **borrarás el último registro de toda la base de datos**, lo haya metido quien lo haya metido. Úsalo con cuidado.

### 2.2. Descargar el Excel
En la pantalla principal tienes el botón amarillo (⬇️ Excel).
- Púlsalo siempre que quieras sacar un "pantallazo" de cómo va el inventario. Te descargará un archivo Excel perfecto (`Inventario_Hoy.xlsx`) con todo cuadradito por categorías. Haz esto siempre antes de cerrar el mes.

### 2.3. Cierre de Mes (El Botón Rojo de Peligro)
Al lado del Excel, hay un botón rojo (🗑️ Mes).
- **Esto es solo para el final del ciclo.** Cuando hayamos cerrado el mes y tengamos el Excel descargado a buen recaudo, pulsas este botón. Lo que hace es archivar el conteo actual en el historial y **reiniciar la base de datos** para empezar a contar de cero el mes que viene.

> [!CAUTION]
> **¡Peligro!** Nunca pulses el botón rojo de Cierre de Mes sin haber descargado y guardado el Excel primero. Si lo haces, perderemos los datos de lo que se ha contado hoy.

---

## 3. El Panel de Control (⚙️ Admin)
En la parte superior verás un botón azul que dice "⚙️ Admin". Ahí está la sala de máquinas de la aplicación. Tiene varias pestañas:

### Pestaña Usuarios
Desde aquí controlamos quién entra a la app.
- **Crear cuentas:** Pon su DNI, Nombre, Contraseña y decide si es `camarero` o `encargado`.
- **Despedir/Borrar:** Si alguien ya no trabaja con nosotros, búscalo en la lista y dale a Borrar. Se le cortará el acceso de inmediato.

### Pestaña Categorías
- Si metemos una nueva familia de alcohol (por ejemplo, "Mezcales"), añádela aquí.
- Aparecerá automáticamente en el desplegable de la pantalla principal para poder filtrar y contar.

### Pestaña Diccionario (Autocorrección)
Este es el cerebro del micrófono. Si ves que el micrófono se vuelve loco con alguna botella rara, aquí le enseñamos a hablar.
- **Alias (Lo que escucha el móvil):** Escribe el error habitual, todo en minúsculas y sin tildes (ej: `yaguer`).
- **Nombre Real (Lo que queremos):** Escribe cómo se llama de verdad (ej: `Jägermeister`).
- Cuando le des a guardar, la próxima vez que el móvil escuche "yaguer", lo cambiará mágicamente por el nombre real antes de guardarlo en la base de datos.

---

## 4. Las Novedades (Analítica y Compras)
He metido unas pestañas nuevas para que no tengas ni que abrir el Excel en el ordenador:

- **Balance:** Aquí puedes comparar el mes anterior con este. Y lo mejor: si hay algún descuadre o una botella rota, verás un lapicito (✏️) al lado de cada producto. Lo pulsas, modificas los números a mano, y el sistema cuadrará los gastos automáticamente firmando como "Ajuste Manual".
- **Compras:** Busca los productos y ponles un "Stock Ideal" (ej: quiero que siempre haya 10 botellas de Beefeater). Luego pulsa "Generar Lista de Compra" y la app te hará el cálculo matemático y te dará un texto listo para que lo pegues en el WhatsApp del proveedor con lo que nos falta.
- **Analítica:** Métete aquí para ver unos gráficos chulísimos de cuánto dinero nos hemos gastado por categorías y el Top 5 de las botellas que más se beben en el bar.

---

Cualquier cosa que falle, dímelo y lo corrijo. ¡A darle duro!

**Marco Daza**
*MDev - Soluciones Tecnológicas*
