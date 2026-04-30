# 커뮤니티 프로젝트 - 백엔드 (Backend)

이 프로젝트는 커뮤니티 서비스의 백엔드 API 서버입니다. FastAPI 프레임워크와 SQLAlchemy를 사용하여 구축되었으며, MySQL 데이터베이스를 사용합니다.

## 🛠 기술 스택

- **Language**: Python 3.x
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: MySQL (PyMySQL 드라이버 사용)
- **Server**: Uvicorn

## 🚀 설치 및 실행 방법

### 1. 환경 설정

`community_api` 디렉토리 내에 `.env` 파일을 생성하고 데이터베이스 연결 정보를 설정해야 합니다.

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
cd community_api
uvicorn app.main:app --reload
```
서버는 기본적으로 `http://localhost:8000` 에서 실행됩니다.

---

## 💾 데이터베이스 스키마 (Database Schema)

이 프로젝트는 MySQL을 사용하며, SQLAlchemy ORM을 통해 모델링되었습니다.

### 1. Users (사용자)
사용자 계정 정보를 저장합니다.

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | 사용자 고유 ID |
| `email` | String(255) | Unique, Not Null | 이메일 (로그인 ID) |
| `password_hash` | String(255) | Not Null | 암호화된 비밀번호 |
| `nickname` | String(50) | Unique, Not Null | 사용자 닉네임 |
| `profile_image_url` | String(500) | Nullable | 프로필 이미지 URL |
| `created_at` | DateTime | Default: Now | 가입 일시 |
| `updated_at` | DateTime | Default: Now | 정보 수정 일시 |
| `deleted_at` | DateTime | Nullable | 탈퇴 일시 (Soft Delete) |

### 2. Posts (게시글)
사용자가 작성한 게시글 정보를 저장합니다.

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | 게시글 고유 ID |
| `title` | String(200) | Not Null | 게시글 제목 |
| `content` | Text | Not Null | 게시글 내용 |
| `author_user_id` | Integer | FK (users.id) | 작성자 ID |
| `file_url` | String(500) | Nullable | 첨부 파일(이미지) URL |
| `hits` | Integer | Default: 0 | 조회수 |
| `created_at` | DateTime | Default: Now | 작성 일시 |
| `updated_at` | DateTime | Default: Now | 수정 일시 |

### 3. Comments (댓글)
게시글에 달린 댓글 정보를 저장합니다.

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | 댓글 고유 ID |
| `post_id` | Integer | FK (posts.id) | 게시글 ID |
| `author_user_id` | Integer | FK (users.id) | 작성자 ID |
| `content` | Text | Not Null | 댓글 내용 |
| `created_at` | DateTime | Default: Now | 작성 일시 |

### 4. Post Likes (좋아요)
게시글 좋아요 정보를 저장합니다 (Many-to-Many).

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `post_id` | Integer | FK (posts.id), PK | 게시글 ID |
| `user_id` | Integer | FK (users.id), PK | 사용자 ID |

### 5. Files (파일)
업로드된 이미지 등의 파일 바이너리 데이터를 저장합니다.

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `id` | String(36) | PK (UUID) | 파일 고유 ID |
| `mime_type` | String(100) | Not Null | 파일 MIME 타입 |
| `data` | LONGBLOB | Not Null | 파일 바이너리 데이터 |
| `created_at` | DateTime | Default: Now | 생성 일시 |

### 6. Sessions (세션)
로그인 세션 정보를 관리합니다.

| 컬럼명 (Column) | 타입 (Type) | 제약조건 (Constraints) | 설명 |
|---|---|---|---|
| `session_id` | String(36) | PK (UUID) | 세션 ID |
| `user_id` | Integer | FK (users.id) | 사용자 ID |
| `created_at` | DateTime | Default: Now | 생성 일시 |