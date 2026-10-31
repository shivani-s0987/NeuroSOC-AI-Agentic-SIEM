import { api } from "./api";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  setAccessToken(data.access_token);
  return data;
}

export async function register(username: string, email: string, password: string) {
  return api.post("/auth/register", { username, email, password });
}

export function logout() {
  setAccessToken(null);
}
