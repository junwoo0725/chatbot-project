import { API_BASE } from "./config.js";

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request(path, { method = "GET", body, headers } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let json = null;
  try {
    json = await res.json();
  } catch (_) { }

  if (!res.ok) {
    const code = json?.code || "UNKNOWN";
    const msg = json?.message || "Request failed";
    throw new ApiError(code, msg, res.status);
  }
  return json;
}

// ---------- Auth ----------
export const AuthAPI = {
  signup: (payload) => request("/v1/auth/signup", { method: "POST", body: payload }),
  login: (payload) => request("/v1/auth/login", { method: "POST", body: payload }),
  logout: () => request("/v1/auth/logout", { method: "POST" }),
  me: () => request("/v1/auth/me"),
  emailAvailability: (email) => request(`/v1/auth/availability/email?email=${encodeURIComponent(email)}`),
  nicknameAvailability: (nickname) =>
    request(`/v1/auth/availability/nickname?nickname=${encodeURIComponent(nickname)}`),
};

// ---------- Users ----------
export const UsersAPI = {
  getUser: (userId) => request(`/v1/users/${userId}`),
  updateMe: (payload) => request(`/v1/users/me`, { method: "PATCH", body: payload }),
  updatePassword: (payload) => request(`/v1/users/me/password`, { method: "PATCH", body: payload }),
  deleteMe: () => request(`/v1/users/me`, { method: "DELETE" }),
};

// ---------- Posts ----------
export const PostsAPI = {
  list: ({ offset = 0, limit = 10 } = {}) => request(`/v1/posts?offset=${offset}&limit=${limit}`),
  get: (postId) => request(`/v1/posts/${postId}`),
  create: (payload) => request(`/v1/posts`, { method: "POST", body: payload }),
  update: (postId, payload) => request(`/v1/posts/${postId}`, { method: "PATCH", body: payload }),
  remove: (postId) => request(`/v1/posts/${postId}`, { method: "DELETE" }),

  // ✅ 백엔드 라우터와 일치: /likes
  like: (postId) => request(`/v1/posts/${postId}/likes`, { method: "POST" }),
  unlike: (postId) => request(`/v1/posts/${postId}/likes`, { method: "DELETE" }),

  listComments: (postId) => request(`/v1/posts/${postId}/comments`),
  createComment: (postId, payload) => request(`/v1/posts/${postId}/comments`, { method: "POST", body: payload }),
  updateComment: (postId, commentId, payload) =>
    request(`/v1/posts/${postId}/comments/${commentId}`, { method: "PATCH", body: payload }),
  deleteComment: (postId, commentId) =>
    request(`/v1/posts/${postId}/comments/${commentId}`, { method: "DELETE" }),
};

// ---------- Chat ----------
export const ChatAPI = {
  getConversations: () => request("/v1/chat/conversations"),
  getMessages: (conversationId) => request(`/v1/chat/conversations/${conversationId}/messages`),
  createConversation: (otherUserId) => request("/v1/chat/conversations", { method: "POST", body: { other_user_id: otherUserId } }),
};

