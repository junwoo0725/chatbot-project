import os
import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any

# 환경 변수에서 AWS 접근 정보 가져오기
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-2")
AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", "junwoo-community-images-2026")

# boto3 클라이언트 초기화 (보안 자격 증명이 주어지지 않으면 IAM Role을 시도함)
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
else:
    s3_client = boto3.client('s3', region_name=AWS_REGION)

def generate_presigned_url(file_extension: str, file_prefix: str = "uploads") -> Optional[Dict[str, Any]]:
    """
    S3 업로드를 위한 Presigned URL 발급
    
    :param file_extension: 업로드하고자 하는 파일의 확장자 (예: 'png', 'jpg')
    :param file_prefix: 저장될 S3 폴더명 (기본값: 'uploads')
    :return: 생성된 URL 정보 딕셔너리 (실패 시 None)
    """
    # 고유한 파일명 생성 (충돌 방지용 UUID 삽입)
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    object_name = f"{file_prefix}/{unique_filename}"
    
    # 5분 동안만 유효한 presigned post 요청 생성 (Method: POST)
    # 크기 제한 등 S3 Conditions 추가 가능 
    try:
        response = s3_client.generate_presigned_post(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=object_name,
            Fields={"acl": "public-read"},
            Conditions=[
                {"acl": "public-read"},
                ["content-length-range", 0, 10485760]  # 최대 10MB 크기 제한
            ],
            ExpiresIn=300
        )
        
        # 파일이 최종적으로 접근 가능한 URL(Read URI) 도 함께 반환하여 응답에 활용
        final_file_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        
        return {
            "upload_url": response["url"],
            "upload_fields": response["fields"],
            "file_url": final_file_url,
            "object_key": object_name
        }
    except ClientError as e:
        print(f"[S3 Error] {e}")
        return None
