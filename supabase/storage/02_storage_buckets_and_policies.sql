-- =============================================================================
-- BOOKLY — Buckets y políticas de Supabase Storage
-- Buckets requeridos: book-covers, book-images, avatars
-- =============================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
    ('book-covers', 'book-covers', TRUE, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('book-images', 'book-images', TRUE, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('avatars', 'avatars', TRUE, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE
SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Lectura pública de portadas, galería y avatares
CREATE POLICY "Public read book-covers"
ON storage.objects FOR SELECT
USING (bucket_id = 'book-covers');

CREATE POLICY "Public read book-images"
ON storage.objects FOR SELECT
USING (bucket_id = 'book-images');

CREATE POLICY "Public read avatars"
ON storage.objects FOR SELECT
USING (bucket_id = 'avatars');

-- Avatares: cada cliente autenticado solo puede subir/actualizar/eliminar en su propia carpeta (<user_id>/...)
CREATE POLICY "Users manage own avatar"
ON storage.objects FOR ALL TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Portadas e imágenes del catálogo: únicamente administradores validados en public.user_roles
-- (Además, FastAPI valida el rol admin antes de operar con SUPABASE_SECRET_KEY)
CREATE POLICY "Admins manage book covers and images"
ON storage.objects FOR ALL TO authenticated
USING (
    bucket_id IN ('book-covers', 'book-images')
    AND EXISTS (
        SELECT 1
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid() AND r.name = 'admin'
    )
)
WITH CHECK (
    bucket_id IN ('book-covers', 'book-images')
    AND EXISTS (
        SELECT 1
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid() AND r.name = 'admin'
    )
);
