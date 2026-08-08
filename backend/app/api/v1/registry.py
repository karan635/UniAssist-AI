from fastapi import APIRouter

from app.services.knowledge.registry_builder import RegistryBuilder

router = APIRouter()


@router.get("/registry")
def registry():

    builder = RegistryBuilder()

    return builder.build()