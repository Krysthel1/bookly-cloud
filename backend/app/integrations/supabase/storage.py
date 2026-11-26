import io
from uuid import uuid4

import httpx
from fastapi import UploadFile
from PIL import Image

from app.config.settings import get_settings
from app.exceptions.handlers import BadRequestException

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class SupabaseStorageService:
    """Gestiona subida, optimización y eliminación de imágenes en Supabase Storage (API REST oficial)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _auth_headers(self) -> tuple[str, dict[str, str]]:
        if not self.settings.supabase_url or not self.settings.supabase_secret_key:
            raise BadRequestException(
                "Supabase Storage no está configurado en las variables de entorno del backend."
            )
        base_url = self.settings.supabase_url.rstrip("/")
        secret = self.settings.supabase_secret_key.strip()
        headers = {
            "apikey": secret,
            "Authorization": f"Bearer {secret}",
        }
        return base_url, headers

    async def upload_image(
        self,
        file: UploadFile,
        bucket_type: str,
        folder: str = "",
        max_width: int = 1200,
    ) -> dict[str, str]:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise BadRequestException(
                "Formato de imagen no permitido. Solo se aceptan JPEG, PNG o WebP."
            )

        raw_bytes = await file.read()
        if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
            raise BadRequestException("La imagen excede el tamaño máximo permitido de 5 MB.")

        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                img = img.convert("RGB")
                if img.width > max_width:
                    ratio = max_width / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=85, optimize=True)
                optimized_bytes = output.getvalue()
        except Exception as exc:
            raise BadRequestException(f"Archivo de imagen corrupto o inválido: {exc}") from exc

        bucket_map = {
            "covers": self.settings.supabase_bucket_covers,
            "images": self.settings.supabase_bucket_images,
            "avatars": self.settings.supabase_bucket_avatars,
        }
        bucket_name = bucket_map.get(bucket_type)
        if not bucket_name:
            raise BadRequestException("Bucket de destino inválido.")

        prefix = f"{folder.strip('/')}/" if folder else ""
        object_path = f"{prefix}{uuid4()}.webp"

        base_url, headers = self._auth_headers()
        upload_url = f"{base_url}/storage/v1/object/{bucket_name}/{object_path}"
        upload_headers = {
            **headers,
            "Content-Type": "image/webp",
            "x-upsert": "true",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(upload_url, headers=upload_headers, content=optimized_bytes)
            if resp.status_code not in (200, 201):
                raise BadRequestException(
                    f"No se pudo subir la imagen a Supabase Storage ({resp.status_code}): {resp.text}"
                )

        public_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{object_path}"
        return {"bucket": bucket_name, "path": object_path, "url": public_url}

    def delete_image(self, bucket_name: str, object_path: str) -> None:
        base_url, headers = self._auth_headers()
        delete_url = f"{base_url}/storage/v1/object/{bucket_name}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.request("DELETE", delete_url, headers=headers, json={"prefixes": [object_path]})
            if resp.status_code not in (200, 204):
                raise BadRequestException(
                    f"No se pudo eliminar la imagen de Supabase Storage ({resp.status_code}): {resp.text}"
                )
