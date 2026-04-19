from fastapi import APIRouter

from app.api.v1.endpoints.customers import router as customer_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.metadata import router as metadata_router
from app.api.v1.endpoints.pos import router as pos_router
from app.api.v1.endpoints.reports import router as report_router
from app.api.v1.endpoints.rental import router as rental_router
from app.api.v1.endpoints.system import router as system_router
from app.api.v1.endpoints.checkout import router as checkout_router
from app.api.v1.endpoints.auth import router as auth_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(health_router, tags=["system"])
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(customer_router)
api_v1_router.include_router(pos_router)
api_v1_router.include_router(rental_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(metadata_router)
api_v1_router.include_router(report_router)
api_v1_router.include_router(system_router)
