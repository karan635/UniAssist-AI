from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_registry_builder
from app.services.knowledge.registry_builder import RegistryBuilder

router = APIRouter()


@router.get("/registry")
def registry(
    builder: RegistryBuilder = Depends(get_registry_builder),
):

    try:

        return builder.build()

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=f"Document directory not found: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to build registry: {str(e)}"
        )