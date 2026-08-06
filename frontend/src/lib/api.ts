import axios from "axios";

// Base API URL targeting the FastAPI backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Send HttpOnly cookies for refresh endpoint
});

// Request Interceptor: Attach the JWT token if available
api.interceptors.request.use(
  (config) => {
    // We store the token in localStorage for this capstone
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle global 401 Unauthorized errors and silent refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If it's a 401 error, and we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Don't intercept 401s from the refresh endpoint itself to prevent infinite loops
      if (originalRequest.url === "/auth/refresh" || originalRequest.url === "/auth/login") {
        return Promise.reject(error);
      }

      try {
        // Attempt silent refresh via HttpOnly cookie
        const response = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        const newAccessToken = response.data.access_token;
        
        // Save the new token
        if (typeof window !== "undefined") {
          localStorage.setItem("auth_token", newAccessToken);
        }

        // Retry the original failed request with the new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, wipe local storage and redirect to login
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
          localStorage.removeItem("auth_user");
          
          if (!window.location.pathname.startsWith("/login")) {
            window.location.href = "/login";
          }
        }
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
