import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

// Shape the login mutation accepts
interface LoginCredentials {
  email: string;
  password: string;
}

export function useLogin() {
  const loginAction = useAuthStore((state) => state.login);
  const router = useRouter();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      // Backend POST /auth/login expects JSON { email, password }
      // and returns { user: UserResponse, tokens: TokenResponse }
      const { data } = await api.post("/auth/login", credentials);
      return data;
    },
    onSuccess: (data) => {
      // Extract token and user from the backend LoginResponse shape
      const token = data.tokens.access_token;
      const user = data.user;

      // Store token + user via Zustand (also writes to localStorage)
      loginAction(token, user);
      router.push("/dashboard");
    },
  });
}

export function useSignup() {
  const router = useRouter();

  return useMutation({
    mutationFn: async (userData: any) => {
      const response = await api.post("/auth/register", userData);
      return response.data;
    },
    onSuccess: () => {
      // Registration successful, redirect to login
      router.push("/login?registered=true");
    },
  });
}

export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const { data } = await api.get("/users/me");
      return data;
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const updateUser = useAuthStore((state) => state.updateUser);

  return useMutation({
    mutationFn: async (payload: { name?: string; email?: string }) => {
      const { data } = await api.patch("/users/me", payload);
      return data;
    },
    onSuccess: (data) => {
      updateUser(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}
