import { api } from "./api";

let accessToken: string | null = localStorage.getItem("neurosoc_access_token");
let refreshToken: string | null = localStorage.getItem("neurosoc_refresh_token");
let refreshPromise: Promise<string> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) localStorage.setItem("neurosoc_access_token", token);
  else localStorage.removeItem("neurosoc_access_token");
}

export function setRefreshToken(token: string | null) {
  refreshToken = token;
  if (token) localStorage.setItem("neurosoc_refresh_token", token);
  else localStorage.removeItem("neurosoc_refresh_token");
}

export function getAccessToken() {
  return accessToken;
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

async function refreshAccessToken() {
  if (!refreshToken) throw new Error("No refresh token");
  if (!refreshPromise) {
    refreshPromise = api
      .post("/auth/refresh", { refresh_token: refreshToken })
      .then(({ data }) => {
        setAccessToken(data.access_token);
        setRefreshToken(data.refresh_token);
        return data.access_token as string;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config;
    if (error.response?.status !== 401 || request?._retry || request?.url?.startsWith("/auth/")) {
      return Promise.reject(error);
    }
    try {
      request._retry = true;
      const token = await refreshAccessToken();
      request.headers = request.headers ?? {};
      request.headers.Authorization = `Bearer ${token}`;
      return api.request(request);
    } catch {
      setAccessToken(null);
      setRefreshToken(null);
      window.location.assign("/");
      return Promise.reject(error);
    }
  },
);

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  setAccessToken(data.access_token);
  setRefreshToken(data.refresh_token);
  return data;
}

export async function register(username: string, email: string, password: string) {
  return api.post("/auth/register", { username, email, password });
}

export async function logout() {
  const suppliedRefreshToken = refreshToken;
  if (suppliedRefreshToken) {
    try {
      await api.post("/auth/logout", { refresh_token: suppliedRefreshToken });
    } catch {
      // Local session cleanup still succeeds if the API is unavailable.
    }
  }
  setAccessToken(null);
  setRefreshToken(null);
}
