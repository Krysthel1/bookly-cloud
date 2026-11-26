from fastapi import APIRouter

from app.api.v1 import admin, catalog, commerce, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(commerce.router)
api_router.include_router(admin.router)
