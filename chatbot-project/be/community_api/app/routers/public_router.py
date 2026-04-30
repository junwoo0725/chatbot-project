from fastapi import APIRouter
from fastapi.responses import Response
from app.storage import db
from app.utils.responses import raise_http_error

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/files/{file_id}")
def get_file(file_id: str):
    data, mime = db.get_file_data(file_id)
    if data is None:
        raise_http_error(404, "NOT_FOUND")
    return Response(content=data, media_type=mime)
