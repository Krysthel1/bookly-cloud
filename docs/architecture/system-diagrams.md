# Diagramas de Comportamiento y Despliegue de BOOKLY

## 1. Casos de Uso Principales

```mermaid
flowchart LR
    V(["Visitante"]) --> UC1["Explorar catálogo y buscar libros"]
    V --> UC2["Ver detalle y reseñas"]
    V --> UC3["Registrarse / Iniciar sesión"]

    C(["Cliente Autenticado"]) --> UC4["Gestionar carrito persistente"]
    C --> UC5["Ejecutar checkout y pago simulado"]
    C --> UC6["Seguir y cancelar pedidos"]
    C --> UC7["Gestionar favoritos, direcciones y reseñas"]

    A(["Administrador"]) --> UC8["Consultar Dashboard KPIs y gráficos"]
    A --> UC9["CRUD Libros, Categorías, Autores y Cupones"]
    A --> UC10["Gestionar Inventario y Pedidos"]
    A --> UC11["Exportar Reportes CSV y ver Auditoría"]
```

## 2. Secuencia de Autenticación (Supabase Auth + FastAPI)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as React Frontend
    participant SA as Supabase Auth
    participant BE as FastAPI Backend
    participant DB as Supabase PostgreSQL

    U->>FE: Ingresa email y contraseña
    FE->>SA: signInWithPassword()
    SA-->>FE: Access Token (JWT) + Refresh Token
    FE->>BE: GET /api/v1/auth/me (Bearer ACCESS_TOKEN)
    BE->>SA: Obtiene JWKS (/.well-known/jwks.json, cacheado)
    BE->>BE: Verifica firma, exp, aud, iss
    BE->>DB: Consulta public.profiles y public.user_roles
    DB-->>BE: Perfil + roles verificados en servidor
    BE-->>FE: 200 OK (ProfileOut con roles reales)
```

## 3. Secuencia de Compra Transaccional e Idempotente

```mermaid
sequenceDiagram
    actor C as Cliente
    participant FE as Checkout Wizard
    participant BE as FastAPI OrderService
    participant DB as PostgreSQL

    C->>FE: Confirma pedido (idempotency_key)
    FE->>BE: POST /api/v1/orders/checkout
    BE->>DB: Verifica idempotency_key existente
    BE->>DB: BEGIN TRANSACTION
    BE->>DB: UPDATE books SET stock = stock - qty WHERE id = :id AND stock >= :qty
    alt Stock insuficiente
        DB-->>BE: rowcount = 0
        BE->>DB: ROLLBACK
        BE-->>FE: 409 INSUFFICIENT_STOCK
    else Stock validado
        BE->>DB: Valida cupón, calcula envío y total en servidor
        BE->>DB: INSERT orders, order_items, payments (simulado), inventory_movements, notifications
        BE->>DB: DELETE cart_items
        BE->>DB: COMMIT
        BE-->>FE: 201 Created (order_code único)
    end
```

## 4. Flujo CI/CD en GitHub Actions

```mermaid
flowchart LR
    Push["Push / PR a main"] --> CI_FE["Frontend CI: Lint + Vitest + Vite Build"]
    Push --> CI_BE["Backend CI: Ruff + Alembic Postgres + Pytest + Docker Build"]
    CI_FE --> Gate1{"Aprobación Manual\n(Environment production-aws)"}
    CI_BE --> Gate2{"Aprobación Manual\n(Environment production-aws)"}
    Gate1 -->|OIDC Role| S3["S3 Sync + CloudFront Invalidation"]
    Gate2 -->|OIDC Role| ECR["Push ECR + ASG Rolling Instance Refresh"]
```
