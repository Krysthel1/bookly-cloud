# Diagrama Entidad-Relación (23 Tablas Normalizadas)

El esquema de datos de BOOKLY es gestionado mediante Alembic (`backend/alembic/versions/0001_initial_schema.py`) y enlazado con `auth.users` de Supabase.

```mermaid
erDiagram
    profiles ||--o{ user_roles : tiene
    roles ||--o{ user_roles : asignado
    profiles ||--o| carts : posee
    carts ||--o{ cart_items : contiene
    books ||--o{ cart_items : incluido
    profiles ||--o{ favorites : marca
    books ||--o{ favorites : guardado
    profiles ||--o{ addresses : registra
    profiles ||--o{ orders : realiza
    addresses ||--o{ orders : referencia
    coupons ||--o{ orders : aplica
    orders ||--o{ order_items : detalla
    books ||--o{ order_items : vendido
    orders ||--|| payments : registra
    coupons ||--o{ coupon_usages : historial
    orders ||--o{ coupon_usages : usa
    profiles ||--o{ coupon_usages : redime
    books ||--o{ reviews : recibe
    profiles ||--o{ reviews : escribe
    books ||--o{ inventory_movements : traza
    profiles ||--o{ inventory_movements : ejecuta
    profiles ||--o{ notifications : recibe
    profiles ||--o{ audit_logs : audita
    publishers ||--o{ books : publica
    books ||--o{ book_images : galeria
    books ||--o{ book_authors : escrito_por
    authors ||--o{ book_authors : participa
    books ||--o{ book_categories : clasificado
    categories ||--o{ book_categories : agrupa
```

## Convenciones de Integridad
- Todas las claves primarias utilizan `UUID`.
- Todos los importes monetarios utilizan `NUMERIC(10, 2)` (`DECIMAL`).
- Restricciones `CHECK` impiden precios negativos, porcentajes fuera de `[0, 100]`, stock negativo (`stock >= 0`) y calificaciones fuera de `[1, 5]`.
- Eliminación lógica (`deleted_at`) en entidades maestras (`profiles`, `books`, `authors`, `categories`, `publishers`, `addresses`, `reviews`, `coupons`).
