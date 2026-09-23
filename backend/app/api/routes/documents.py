from fastapi import APIRouter

router = APIRouter(
    prefix = "/documents",
    tags = ["Documents"],
)

@router.get("")
def list_documents():
    return {"documents": []}

