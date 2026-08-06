import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (token: string, user: User) => void;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start loading as we need to check localStorage

  login: (token, user) => {
    localStorage.setItem("auth_token", token);
    localStorage.setItem("auth_user", JSON.stringify(user));
    set({ user, isAuthenticated: true, isLoading: false });
  },
  
  logout: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  checkAuth: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      const userStr = localStorage.getItem("auth_user");
      
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    }
  }
}));
