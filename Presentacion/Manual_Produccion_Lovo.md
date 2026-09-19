# Manual de Funcionamiento: Módulo "Producción Lovo"

Este documento explica de forma clara y directa el funcionamiento del nuevo módulo de **Producción** dentro de la PWA de Inventario Lovo. Está diseñado para que tanto la gerencia (Frank) como el equipo de producción entiendan su propósito, su uso diario y cómo impacta en los números finales del negocio.

---

## 1. ¿Cuál es el objetivo de este módulo?

En un bar de alta coctelería como Lovo, no todo el alcohol se sirve directamente de la botella al cliente. Una gran cantidad de producto se utiliza en el "back of house" (producción/laboratorio) para crear **macerados, siropes, pre-batches, clarificados y cordiales**.

**El problema anterior:**
Cuando se hacían estas producciones, el alcohol desaparecía de las botellas base (ej. ron, vodka), generando **descuadres en el inventario**. A final de mes, en el Excel, parecía que faltaban botellas (mermas inexplicables), cuando en realidad estaban invertidas en producciones internas.

**La solución actual:**
El módulo "Producción Lovo" digitaliza este proceso. Cuando el equipo cocina un *batch*, el sistema **descuenta automáticamente** la cantidad exacta de ingredientes utilizados del inventario principal y **crea un nuevo stock** del producto elaborado.

---

## 2. ¿Cómo funciona la precisión por Báscula?

Para que el inventario sea 100% real, hemos integrado un sistema de pesaje. Ya no se cuenta "a ojo" (ej. "queda media botella").

### Configuración de Botellas
El sistema necesita conocer tres datos de cada marca de botella (esto se configura una sola vez en el panel de administrador):
1. **Peso Llena (gr)**: Lo que pesa la botella nueva sin abrir.
2. **Peso Vacía / Tara (gr)**: Lo que pesa el cristal de la botella cuando está completamente vacía.
3. **Volumen (ml)**: El líquido que contiene (ej. 700ml, 1000ml).

### La Calculadora del Sistema
Cuando el equipo de producción o los bartenders van a hacer inventario de una botella empezada, simplemente la ponen en la báscula. 
Al introducir ese peso en la App, el sistema resta la tara del cristal mediante la fórmula:
`Peso Líquido = Peso Total en Báscula - Peso del Cristal`
Y con una simple regla de tres, calcula **exactamente cuántos mililitros exactos quedan**.

---

## 3. Flujo de Trabajo para el Equipo de Producción

El día a día del equipo de laboratorio se resume en estos pasos dentro de la App (Panel de Administrador > Pestaña *Producción Lovo*):

1. **Seleccionar la Receta:**
   Eligen qué van a producir hoy (ej. *Sirope de Vainilla*, *Batch Citrus Soul*). Las recetas ya están preconfiguradas con las cantidades exactas que lleva 1 Lote (1 Batch).

2. **Indicar la cantidad a producir:**
   Si la receta original es para 1 Litro, pero hoy van a hacer el triple, simplemente ponen `3` en "Cantidad de Lotes".

3. **Ejecutar Producción (El "Clic" mágico):**
   Al darle al botón "Producir y Descontar Stock", el sistema hace lo siguiente en milisegundos:
   - Busca en el almacén todos los ingredientes que lleva la receta.
   - Les **resta los mililitros correspondientes** multiplicados por los lotes hechos.
   - **Suma el stock nuevo** del producto final (ej. ahora hay +3 Litros de Batch Citrus Soul).

---

## 4. ¿Cómo impacta esto en el Excel a final de mes? (Para Gerencia / Frank)

Este es el punto más crítico a nivel de gestión y rentabilidad:

- **Se acabó el alcohol "fantasma":** Cuando descarguéis el archivo Excel de Inventario a final de mes, las botellas de destilados base habrán bajado su nivel, pero **el sistema sabrá exactamente por qué**. El consumo de esos mililitros quedará justificado como "Gastado en Producción".
- **Trazabilidad del Coste:** Al tener los ingredientes enlazados a una receta, en el futuro se puede saber exactamente cuánto cuesta producir cada litro de vuestros propios siropes o pre-batches, ajustando mejor los márgenes de beneficio de la carta de cócteles (escandallos más precisos).
- **Inventario Real de Batches:** El Excel ahora mostrará en el stock no solo las botellas de marcas comerciales, sino también los litros disponibles de vuestras propias creaciones, lo que representa un activo (dinero inmovilizado) que antes era muy difícil de cuantificar.

> [!TIP]
> **Resumen en una frase:** El módulo de Producción convierte el alcohol crudo del almacén en productos elaborados dentro de la App, manteniendo el valor del inventario cuadrado al milímetro y eliminando los descuadres por "mermas de laboratorio".

---

<br>

<div align="center">
  <p><b>Desarrollador Fullstack:</b> Marco Antonio Daza</p>
  <p><b>Cliente:</b> Coctelería Lovo</p>
  <p><i>&copy; 2026 Todos los derechos reservados.</i></p>
</div>
