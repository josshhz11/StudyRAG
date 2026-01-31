// Type definitions matching FastAPI backend response models

export interface User {
  user_id: string;
  email: string;
  username?: string;
  created_at?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
}

export interface FileInfo {
  key: string;
  semester: string;
  subject: string;
  book_id: string;
  book_title: string;
  size: number;
  s3_url?: string;
}

export interface FilesResponse {
  files: FileInfo[];
  total: number;
}

export interface MessageResponse {
  message: string;
  success?: boolean;
  details?: Record<string, any>;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    content: string;
    metadata: Record<string, any>;
  }>;
  metadata?: {
    user_id: string;
    scope: {
      semester?: string;
      subject?: string;
    };
    model: string;
  };
}

export interface ChatQueryRequest {
  question: string;
  semester?: string;
  subject?: string;
  books?: string[];
}
