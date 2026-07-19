import axios from "axios";
import { message } from "antd";

const client = axios.create({
  baseURL: "/api",
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

// 请求拦截器：自动附加 Token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      // 未登录跳转到登录页
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    } else if (error.response?.status === 403) {
      message.error("权限不足");
    } else if (error.response?.data?.detail) {
      message.error(error.response.data.detail);
    } else {
      message.error("请求失败，请稍后重试");
    }
    return Promise.reject(error);
  }
);

export default client;
