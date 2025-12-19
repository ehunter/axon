"use client";

import { useSession, signIn, signOut } from "next-auth/react";

/**
 * Custom hook for authentication in client components
 * 
 * Provides easy access to:
 * - Current user session
 * - Loading state
 * - Authentication status
 * - Sign in/out functions
 */
export function useAuth() {
  const { data: session, status } = useSession();

  return {
    user: session?.user ?? null,
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
    signIn,
    signOut: () => signOut({ callbackUrl: "/" }),
  };
}






