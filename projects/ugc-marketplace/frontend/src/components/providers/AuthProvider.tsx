"use client";

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import apiClient from "@/lib/api-client";
import type { User } from "@/lib/types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const setAuthCookie = (token: string) => {
  document.cookie = `auth_token=${token}; path=/; max-age=86400; samesite=lax`;
};

const removeAuthCookie = () => {
  document.cookie = "auth_token=; path=/; max-age=0";
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      setAuthCookie(token);
      apiClient.setToken(token);
      apiClient
        .get<User>("/auth/me")
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("auth_token");
          apiClient.setToken(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.post<{ user: User; token: string }>("/auth/login", {
      email,
      password,
    });
    localStorage.setItem("auth_token", response.token);
    setAuthCookie(response.token);
    apiClient.setToken(response.token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const response = await apiClient.post<{ user: User; token: string }>("/auth/register", {
      name,
      email,
      password,
    });
    localStorage.setItem("auth_token", response.token);
    setAuthCookie(response.token);
    apiClient.setToken(response.token);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      localStorage.removeItem("auth_token");
      removeAuthCookie();
      apiClient.setToken(null);
      setUser(null);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const data = await apiClient.get<User>("/auth/me");
    setUser(data);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: !!user, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
