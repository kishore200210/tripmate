import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

export function useLogin() {
  const loginAction = useAuthStore((state) => state.login);
  const router = useRouter();

  return useMutation({
    mutationFn: async (credentials: URLSearchParams) => {
      // FastAPI OAuth2PasswordRequestForm expects x-www-form-urlencoded
      const { data } = await api.post("/auth/login", credentials, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      return data; // { access_token, token_type }
    },
    onSuccess: async (data) => {
      // Temporarily store token so the next request works
      localStorage.setItem("auth_token", data.access_token);
      
      // Fetch user profile immediately
      try {
        const { data: user } = await api.get("/users/me");
        loginAction(data.access_token, user);
        router.push("/dashboard");
      } catch (err) {
        console.error("Failed to fetch user profile after login", err);
      }
    },
  });
}

export function useSignup() {
  const router = useRouter();

  return useMutation({
    mutationFn: async (userData: any) => {
      const { password, ...safeUserData } = userData;
      console.log("API URL: /auth/register");
      console.log("Request body:", safeUserData);

      const response = await api.post("/auth/register", userData);
      
      console.log("Status code:", response.status);
      console.log("Response body:", response.data);

      return response.data;
    },
    onSuccess: () => {
      // Registration successful, redirect to login
      router.push("/login?registered=true");
    },
  });
}
