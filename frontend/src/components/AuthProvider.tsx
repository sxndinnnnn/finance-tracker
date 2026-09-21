"use client";

import { createContext, useCallback, useEffect, useState } from "react";
import { api, clearTokens, getAccessToken, setTokens } from "@/lib/api-client";
import type { User } from "@/types";

interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  base_currency_code: string;
  locale: string;
  timezone: string;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await api.post<TokenPair>("/auth/login", { email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const register = useCallback(async (input: RegisterInput) => {
    const tokens = await api.post<TokenPair>("/auth/register", input);
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}
