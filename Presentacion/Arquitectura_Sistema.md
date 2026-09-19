# Arquitectura Sistema Inventario Hostelería (Producción Lovo)

Este documento detalla la estructura de la base de datos y el flujo de procesos del módulo de Producción, diseñado para explicar técnicamente cómo se gestionan los stocks, las recetas y el pesaje.

## 1. Estructura de la Base de Datos (Entidad-Relación)

A continuación, se muestra el modelo relacional que permite conectar el inventario general con las producciones de laboratorio.

```mermaid
erDiagram
    STOCK_REFERENCIA {
        int id PK
        string producto
        string categoria
        float stock_actual "Fracción de botella (ej. 1.5)"
        float peso_llena_gr "Peso bruto (botella nueva)"
        float peso_tara_gr "Peso del cristal"
        float volumen_nominal_ml "Volumen total (ej. 700)"
    }
    
    RECETAS_PRODUCCION {
        int id PK
        string nombre "Ej: Citrus Soul"
        float volumen_final_ml "Total ml por lote"
    }
    
    PRODUCCION_INGREDIENTES {
        int id PK
        int receta_id FK "Relación con RECETAS_PRODUCCION"
        int ingrediente_id FK "Relación con STOCK_REFERENCIA"
        float cantidad_ml "Mililitros requeridos por lote"
    }
    
    STOCK_PRODUCCION {
        int id PK
        int receta_id FK "Relación con RECETAS_PRODUCCION"
        float stock_actual_ml "Inventario actual del batch"
    }

    RECETAS_PRODUCCION ||--o{ PRODUCCION_INGREDIENTES : "contiene"
    STOCK_REFERENCIA ||--o{ PRODUCCION_INGREDIENTES : "es usado como"
    RECETAS_PRODUCCION ||--|| STOCK_PRODUCCION : "genera stock en"
```

## 2. Diagrama de Flujo: Ejecución de una Producción

El siguiente diagrama explica el proceso algorítmico que ocurre en el servidor cuando el equipo decide preparar un lote de producción (ej. cocinar un sirope).

```mermaid
sequenceDiagram
    participant B as Bartender / Lab
    participant F as Frontend (PWA)
    participant S as Servidor (FastAPI)
    participant DB as Base de Datos (SQLite)

    B->>F: 1. Selecciona Receta y Nº de Lotes
    F->>S: 2. POST /api/produccion/ejecutar (receta, lotes)
    S->>DB: 3. Consultar `produccion_ingredientes` de la receta
    DB-->>S: 4. Retorna lista de ingredientes y cantidades (ml)
    
    loop Por cada ingrediente
        S->>DB: 5. Consultar volumen_nominal_ml del ingrediente en `stock_referencia`
        S->>S: 6. Calcular ML totales = cantidad_ml * lotes
        S->>S: 7. Convertir ML a botellas: botellas_a_restar = ML / volumen_nominal_ml
        S->>DB: 8. UPDATE `stock_referencia`: stock_actual -= botellas_a_restar
    end
    
    S->>DB: 9. UPDATE `stock_produccion`: sumar (volumen_final_ml * lotes)
    DB-->>S: 10. Confirmación de transacción (Commit)
    S-->>F: 11. Success: "Producción completada"
    F-->>B: 12. Notificación en pantalla
```

## 3. Diagrama de Flujo: Sistema de Pesaje (Báscula)

Este proceso detalla cómo la aplicación convierte el peso físico (en gramos) a un formato de inventario decimal (botellas).

```mermaid
flowchart TD
    A[Botella en Báscula] --> B(Ingresar Peso en PWA)
    B --> C{¿Tiene Tara configurada?}
    C -- Sí --> D[Calcular Peso Neto: Peso Báscula - Tara]
    C -- No --> E[Error: Configurar Pesos Primero]
    D --> F[Calcular Peso Líquido Total: Peso Llena - Tara]
    F --> G[Calcular Porcentaje: Peso Neto / Peso Líquido Total]
    G --> H[Multiplicar Porcentaje * Volumen Nominal (ml)]
    H --> I[Resultado: Fracción de Botella y ML restantes]
    I --> J((Actualizar Stock))
```

## 4. Notas Técnicas
- **Atomicidad:** Todo el proceso de descuento de stock de múltiples ingredientes y suma del producto final se ejecuta en una única transacción de base de datos (`commit` o `rollback`). Si falla un ingrediente, no se altera ningún dato.
- **Trazabilidad de Peso:** Al disociar el peso del cristal (tara) del peso bruto, evitamos desviaciones provocadas por los diferentes grosores de vidrio de cada fabricante.
