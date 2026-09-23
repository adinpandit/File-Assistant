from fastapi import APIRouter

router = APIRouter(
    prefix = "/upload",
    tags = ["Upload"],
)

@router.post("")
def upload_document():
    return{"message":"Upload end point ready"}
