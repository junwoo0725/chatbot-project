# S3 버킷 생성 (이름은 전 세계 고유해야 하므로 프로젝트명+랜덤문자열 조합 추천)
resource "aws_s3_bucket" "image_bucket" {
  bucket = "junwoo-community-images-2026" # 버킷 이름 (필요시 중복 방지를 위해 수정)

  tags = {
    Name        = "community-images"
    Environment = "production"
  }
}

# 버킷 퍼블릭 액세스 차단 설정 (보안 모범 사례: 업로드는 Backend API(Presigned URL)를 통해서만 진행)
resource "aws_s3_bucket_public_access_block" "image_bucket_access_block" {
  bucket = aws_s3_bucket.image_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# 객체 소유권 설정
resource "aws_s3_bucket_ownership_controls" "image_bucket_ownership" {
  bucket = aws_s3_bucket.image_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# 버킷 ACL 설정 (Public Read 허용 - 프론트엔드에서 이미지 URL로 직접 접근 가능하도록)
resource "aws_s3_bucket_acl" "image_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.image_bucket_ownership,
    aws_s3_bucket_public_access_block.image_bucket_access_block,
  ]

  bucket = aws_s3_bucket.image_bucket.id
  acl    = "public-read"
}

# CORS 설정 (프론트엔드 애플리케이션에서 직접 업로드/접근을 허용하기 위함)
resource "aws_s3_bucket_cors_configuration" "image_bucket_cors" {
  bucket = aws_s3_bucket.image_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"] # 실제 운영 시에는 프론트엔드 도메인으로 제한하는 것이 좋습니다 (예: "http://<프론트엔드-서버-IP>")
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# 정책 설정 (모든 사용자가 버킷의 객체를 읽을 수 있도록 허용)
resource "aws_s3_bucket_policy" "image_bucket_policy" {
  bucket = aws_s3_bucket.image_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.image_bucket.arn}/*"
      },
    ]
  })
  
  depends_on = [aws_s3_bucket_public_access_block.image_bucket_access_block]
}
