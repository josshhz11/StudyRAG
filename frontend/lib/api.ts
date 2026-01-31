// API client for FastAPI backend communication

import axios, { AxiosInstance, AxiosError } from "axios";
import { getToken, removeToken } from "./auth";
import type {
  AuthResponse,
  User,
  FilesResponse,
  MessageResponse,
  ChatResponse,
  ChatQueryRequest,
} from "@/types";

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - add JWT token to all requests
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      removeToken();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ============ AUTH ENDPOINTS ============

/**
 * Sign up new user
 */
export async function signup(
  email: string,
  password: string,
  username: string
): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/signup", {
    email,
    password,
    username,
  });
  return response.data;
}

/**
 * Login user
 */
export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/login", {
    email,
    password,
  });
  return response.data;
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

/**
 * Logout user
 */
export async function logoutUser(): Promise<void> {
  try {
    await api.post("/auth/logout");
  } catch (error) {
    // Ignore errors on logout
    console.error("Logout error:", error);
  }
}

// ============ FILE ENDPOINTS ============

/**
 * List all user's files
 */
export async function listFiles(): Promise<FilesResponse> {
  const response = await api.get<FilesResponse>("/api/files");
  return response.data;
}

/**
 * Upload a PDF file
 */
export async function uploadFile(
  file: File,
  semester: string,
  subject: string,
  book: string
): Promise<MessageResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<MessageResponse>(
    `/api/files/upload?semester=${encodeURIComponent(
      semester
    )}&subject=${encodeURIComponent(subject)}&book=${encodeURIComponent(book)}`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

/**
 * Delete a file
 */
export async function deleteFile(fileKey: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/api/files/${fileKey}`);
  return response.data;
}

// ============ CHAT ENDPOINTS ============

/**
 * Send chat query (RAG)
 */
export async function sendChatQuery(
  request: ChatQueryRequest
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/api/chat/query", request);
  return response.data;
}

// Export the axios instance for custom requests
export default api;
