import client from "./client";
import type { LoginRequest, RegisterRequest, ChangePasswordRequest } from "../types";

export const authApi = {
  register: (data: RegisterRequest) => client.post("/auth/register", data),
  login: (data: LoginRequest) => client.post("/auth/login", data),
  me: () => client.get("/auth/me"),
  changePassword: (data: ChangePasswordRequest) =>
    client.post("/auth/change-password", data),
};
