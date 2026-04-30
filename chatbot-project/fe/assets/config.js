// Nginx 리버스 프록시(포트 80)를 사용하는 Docker 환경에서는 상대 경로("")를 사용하고,
// 그 외(Live Server 등 포트가 있는 로컬 환경)에서는 8000 포트의 백엔드를 직접 호출합니다.
export const API_BASE = (window.location.port === "80" || window.location.port === "")
    ? ""
    : "http://localhost:8001";


