const API_BASE = "http://localhost:8000/api/v1";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    firebase_uid: string;
    created_at: string;
  };
}

export interface Image {
  id: string;
  filename: string;
  gcs_uri: string;
  created_at: string;
}

class ApiService {
  private token: string | null = localStorage.getItem("token");

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("token", token);
  }

  getToken() {
    return this.token || localStorage.getItem("token");
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem("token");
  }

  private getHeaders() {
    return {
      "Content-Type": "application/json",
      ...(this.getToken() && {
        Authorization: `Bearer ${this.getToken()}`,
      }),
    };
  }

  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Signup failed");
    }

    const result = await response.json();
    this.setToken(result.access_token);
    return result;
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const result = await response.json();
    this.setToken(result.access_token);
    return result;
  }

  async uploadImage(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/images/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  async listImages(): Promise<{ total: number; images: Image[] }> {
    const response = await fetch(`${API_BASE}/images/`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch images");
    }

    return response.json();
  }

  async deleteImage(imageId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/images/${imageId}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Delete failed");
    }

    return response.json();
  }

  async getDashboard(): Promise<any> {
    const response = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch dashboard");
    }

    return response.json();
  }
}

export const apiService = new ApiService();
