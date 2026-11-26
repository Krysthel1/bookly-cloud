-- =============================================================================
-- BOOKLY — Trigger de registro Supabase Auth y políticas Row Level Security (RLS)
-- Ejecutar en Supabase SQL Editor DESPUÉS de correr `alembic upgrade head`.
-- =============================================================================

-- 1. Trigger automático para sincronizar auth.users -> public.profiles + rol 'customer'
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    customer_role_id UUID;
BEGIN
    INSERT INTO public.profiles (id, email, full_name, is_active, created_at, updated_at)
    VALUES (
        NEW.id,
        LOWER(NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'full_name', SPLIT_PART(NEW.email, '@', 1)),
        TRUE,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    SELECT id INTO customer_role_id FROM public.roles WHERE name = 'customer' LIMIT 1;
    IF customer_role_id IS NOT NULL THEN
        INSERT INTO public.user_roles (id, user_id, role_id, created_at)
        VALUES (gen_random_uuid(), NEW.id, customer_role_id, NOW())
        ON CONFLICT (user_id, role_id) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Habilitar RLS en todas las tablas del esquema public expuestas por Data API
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.publishers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.books ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.book_authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.book_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.book_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coupon_usages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 3. Políticas de lectura pública únicamente para catálogo visible
CREATE POLICY "Public read active books" ON public.books
    FOR SELECT USING (is_active = TRUE AND deleted_at IS NULL);

CREATE POLICY "Public read active authors" ON public.authors
    FOR SELECT USING (is_active = TRUE AND deleted_at IS NULL);

CREATE POLICY "Public read active categories" ON public.categories
    FOR SELECT USING (is_active = TRUE AND deleted_at IS NULL);

CREATE POLICY "Public read active publishers" ON public.publishers
    FOR SELECT USING (is_active = TRUE AND deleted_at IS NULL);

CREATE POLICY "Public read book images" ON public.book_images
    FOR SELECT USING (TRUE);

CREATE POLICY "Public read approved reviews" ON public.reviews
    FOR SELECT USING (is_approved = TRUE AND deleted_at IS NULL);

-- 4. Políticas estrictas por propietario (para consultas directas autorizadas vía Supabase Realtime/Data API)
CREATE POLICY "Users read own profile" ON public.profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);

CREATE POLICY "Users update own profile" ON public.profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "Users read own notifications" ON public.notifications
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Users read own orders" ON public.orders
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Users read own favorites" ON public.favorites
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Users read own addresses" ON public.addresses
    FOR SELECT TO authenticated USING (auth.uid() = user_id AND deleted_at IS NULL);

-- 5. Tablas administrativas y transaccionales sin políticas Data API públicas
-- (inventory_movements, coupons, coupon_usages, payments, audit_logs, roles, user_roles, carts, cart_items, order_items):
-- Al tener RLS habilitado y cero políticas para anon/authenticated, la Data API bloquea todo acceso directo.
-- Todas las operaciones transaccionales pasan obligatoriamente por el backend FastAPI.

-- 6. Usuario de base de datos con privilegios mínimos para el backend (recomendado en producción)
-- Ejecutar manualmente sustituyendo <STRONG_PASSWORD> si se crea un rol dedicado distinto del propietario:
-- CREATE ROLE bookly_app WITH LOGIN PASSWORD '<STRONG_PASSWORD>' NOINHERIT;
-- GRANT USAGE ON SCHEMA public TO bookly_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bookly_app;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bookly_app;
