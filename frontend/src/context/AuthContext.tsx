import React, { createContext, useContext, useState, useEffect } from "react";
import { UserPrincipal } from "../types/index.ts";
import { apiClient, setAuthToken } from "../api/client.ts";

interface AuthContextType {
  user: UserPrincipal | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  loginDemo: (role?: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserPrincipal | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Auto-login with default analyst role for local development/demo
    const initAuth = async () => {
      try {
        const res = await apiClient.demoLogin("analyst");
        setToken(res.access_token);
        setUser(res.user);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to initialize authentication.");
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const loginDemo = async (role = "analyst") => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.demoLogin(role);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo login failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch {
      // Ignore logout errors
    } finally {
      setUser(null);
      setToken(null);
      setAuthToken(null);
    }
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    if (user.roles.includes("admin")) return true;
    return user.roles.includes(role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        loginDemo,
        logout,
        isAuthenticated: !!token && !!user,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
