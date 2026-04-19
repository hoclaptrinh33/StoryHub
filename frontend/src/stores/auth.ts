import { defineStore } from "pinia";
import { ref, computed } from "vue";

export type User = {
  id: number;
  username: string;
  full_name: string | null;
  role: "owner" | "manager" | "cashier";
  scopes: string[];
};

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("storyhub_token"));
  const user = ref<User | null>(null);
  
  try {
    const savedUser = localStorage.getItem("storyhub_user");
    if (savedUser) {
      user.value = JSON.parse(savedUser);
    }
  } catch (e) {
    console.error("Failed to parse saved user", e);
  }

  const isAuthenticated = computed(() => !!token.value);
  
  function setAuth(newToken: string, newUser: User) {
    token.value = newToken;
    user.value = newUser;
    localStorage.setItem("storyhub_token", newToken);
    localStorage.setItem("storyhub_user", JSON.stringify(newUser));
  }

  function clearAuth() {
    token.value = null;
    user.value = null;
    localStorage.removeItem("storyhub_token");
    localStorage.removeItem("storyhub_user");
  }

  return {
    token,
    user,
    isAuthenticated,
    setAuth,
    clearAuth,
  };
});
