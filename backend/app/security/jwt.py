from functools import lru_cache
from typing import Any
import jwt
from jwt import PyJWKClient

from app.config.settings import get_settings
from app.exceptions.handlers import UnauthorizedException


@lru_cache
def get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def verify_supabase_token(token: str) -> dict[str, Any]:
    """
    Valida el JWT emitido por Supabase Auth.
    Soporta claves asimétricas modernas (RS256 / ES256 vía JWKS) y HS256 heredado.
    Verifica firma, expiración, audiencia e emisor sin confiar en metadatos del cliente.
    """
    settings = get_settings()
    if not token:
        raise UnauthorizedException("Token de autenticación no proporcionado.")

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException(f"Encabezado JWT inválido: {exc}") from exc

    decode_options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": bool(settings.supabase_jwt_audience),
        "verify_iss": bool(settings.supabase_issuer),
    }

    try:
        if alg in ("RS256", "ES256"):
            if not settings.supabase_jwks_url:
                raise UnauthorizedException("SUPABASE_URL no configurado para validar JWKS.")
            client = get_jwk_client(settings.supabase_jwks_url)
            signing_key = client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.supabase_jwt_audience or None,
                issuer=settings.supabase_issuer or None,
                options=decode_options,
            )
            return payload

        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise UnauthorizedException("SUPABASE_JWT_SECRET no configurado para tokens HS256.")
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=settings.supabase_jwt_audience or None,
                issuer=settings.supabase_issuer or None,
                options=decode_options,
            )
            return payload

        raise UnauthorizedException(f"Algoritmo JWT no soportado: {alg}")

    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("La sesión ha expirado. Inicia sesión nuevamente.") from exc
    except jwt.InvalidAudienceError as exc:
        raise UnauthorizedException("Audiencia del token inválida.") from exc
    except jwt.InvalidIssuerError as exc:
        raise UnauthorizedException("Emisor del token inválido.") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException(f"Token de autenticación inválido: {exc}") from exc
