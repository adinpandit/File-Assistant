from fastapi import APIRouter

router = APIRouter(
    prefix = "/query",
    tags = ["Query"],
)

@router.post("")
def query_documents():
    return {
        "answer":"",
        "sources":[],
    }