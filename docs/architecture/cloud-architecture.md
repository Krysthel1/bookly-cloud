# Arquitectura Lógica y Cloud de BOOKLY

## 1. Arquitectura Lógica de Tres Capas

BOOKLY implementa una arquitectura monolítica modular desacoplada en tres capas independientes:

```mermaid
flowchart TB
    subgraph "Capa de Presentación (Frontend SPA)"
        UI["React 18 + TypeScript + Vite"]
        State["Zustand + TanStack Query + React Hook Form + Zod"]
        AuthSDK["Supabase Auth JS SDK"]
    end

    subgraph "Capa de Negocio (Backend API REST)"
        API["FastAPI + Uvicorn + Pydantic v2"]
        Sec["JWKS / JWT Verification + RBAC + Rate Limiting"]
        Services["Servicios Modulares: Catalog, Cart, Checkout, Inventory, Admin, Reports"]
        ORM["SQLAlchemy 2.0 + Alembic"]
    end

    subgraph "Capa de Datos y BaaS (Supabase)"
        DB[("PostgreSQL Gestionado + RLS")]
        Auth["Supabase Auth (GoTrue)"]
        Storage["Supabase Storage (book-covers, book-images, avatars)"]
    end

    UI --> AuthSDK
    AuthSDK -->|HTTPS / OAuth2 JWT| Auth
    UI -->|REST JSON + Bearer Access Token| API
    API --> Sec --> Services --> ORM
    ORM -->|PostgreSQL sobre TLS / Supavisor Pooler| DB
    Services -->|HTTPS + SUPABASE_SECRET_KEY| Storage
```

## 2. Arquitectura Cloud Computing (AWS + Supabase Externo)

Supabase es un servicio BaaS externo a la VPC de AWS; las instancias backend en subredes privadas se conectan hacia Supabase saliendo por NAT Gateway con cifrado TLS/HTTPS.

```mermaid
flowchart LR
    User(["Usuario / Lector"]) -->|HTTPS| CF["Amazon CloudFront + OAC"]
    CF -->|Privado SigV4| S3[("Amazon S3\nFrontend Dist")]
    User -->|HTTPS / Auth| SupaAuth["Supabase Auth\n(Externo)"]
    User -->|HTTPS| ALB["Application Load Balancer\n(Subredes Públicas)"]

    subgraph "AWS VPC (10.0.0.0/16) - 2 Zonas de Disponibilidad"
        subgraph "Subredes Públicas (10.0.1.0/24, 10.0.2.0/24)"
            ALB
            NAT["NAT Gateway"]
            IGW["Internet Gateway"]
        end

        subgraph "Subredes Privadas (10.0.11.0/24, 10.0.12.0/24)"
            EC2_1["EC2 AZ-a\nDocker FastAPI"]
            EC2_2["EC2 AZ-b\nDocker FastAPI"]
        end

        ALB -->|HTTP:8000| EC2_1
        ALB -->|HTTP:8000| EC2_2
        EC2_1 --> NAT
        EC2_2 --> NAT
        NAT --> IGW
    end

    ECR[("Amazon ECR")] -.->|docker pull| EC2_1
    SM["AWS Secrets Manager"] -.->|IAM Role| EC2_1
    EC2_1 -->|Logs & Métricas| CW["Amazon CloudWatch"]
    EC2_2 -->|Logs & Métricas| CW

    IGW -->|PostgreSQL TLS :6543/:5432| SupaDB[("Supabase PostgreSQL\n(Externo a la VPC)")]
    IGW -->|HTTPS :443| SupaStorage["Supabase Storage\n(Externo a la VPC)"]
```
