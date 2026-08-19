from fastapi import APIRouter
from backend.app.api.v1 import auth, shows, episodes, artwork, catalog, admin

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(shows.router)
api_router.include_router(episodes.router)
api_router.include_router(artwork.router)
api_router.include_router(catalog.router)
api_router.include_router(admin.router)
