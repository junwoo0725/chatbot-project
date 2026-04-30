from fastapi import APIRouter, HTTPException, Query
from app.utils.responses import success_response
from app.utils.s3 import generate_presigned_url
import uuid

# 라우터 생성 (태그를 Upload로 지정하여 Swagger에 분리 표기)
router = APIRouter()

@router.get("/presigned-url")
def get_presigned_url(extension: str = Query(..., description="업로드할 이미지 확장자 (예: jpg, png)")):
    """
    S3에 이미지를 직접 업로드하기 위한 일회성 접근 주소(Presigned URL)를 발급받습니다.
    
    1. 프론트엔드가 이 API를 호출하여 `{ "upload_url": "...", "fields": {"key": "..."}, "file_url": "..." }` 응답을 받음
    2. 프론트엔드쪽에서 해당 upload_url 로 실제 이미지 파일을 Form-Data(POST) 형식으로 전송
    3. 전송된 이미지는 S3에 안전하게 저장되며, 데이터베이스에는 `file_url` 주소를 저장명으로 사용함
    """
    
    # 허용된 확장자(보안 검사) 추가 (선택사항)
    allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
    if extension.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail={"code": "INVALID_EXTENSION", "message": "허용되지 않는 이미지 확장자입니다. (jpg, png, gif 등만 가능)"}
        )

    # 유틸리티 함수 호출하여 URL 발급받기
    result = generate_presigned_url(file_extension=extension.lower())
    
    if not result:
        raise HTTPException(
            status_code=500, 
            detail={"code": "S3_GENERATE_ERROR", "message": "S3 임시 업로드 주소를 생성할 수 없습니다. (환경변수나 AWS 권한을 확인하세요)"}
        )
        
    return success_response(
        code="PRESIGNED_URL_GENERATED", 
        data=result
    )
