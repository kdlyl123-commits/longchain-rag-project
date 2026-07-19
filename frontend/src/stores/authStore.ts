import { create } from "zustand";
import type { User, LoginRequest, RegisterRequest, ChangePasswordRequest } from "../types";
import { authApi } from "../api/auth";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("token"),
  user: JSON.parse(localStorage.getItem("user") || "null"),
  loading: false,

  login: async (data) => {
    const res = await authApi.login(data);
    const { access_token } = res.data;
    localStorage.setItem("token", access_token);
    set({ token: access_token });
  },

  register: async (data) => {
    await authApi.register(data);
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ token: null, user: null });
  },

  fetchMe: async () => {
    try {
      const res = await authApi.me();
      const user = res.data;
      localStorage.setItem("user", JSON.stringify(user));
      set({ user });
    } catch {
      get().logout();
    }
  },

  changePassword: async (data) => {
    await authApi.changePassword(data);
  },

  isAdmin: () => get().user?.role === "admin",
}));
