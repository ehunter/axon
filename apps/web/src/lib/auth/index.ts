import NextAuth from "next-auth";
import { authConfig } from "./config";

/**
 * NextAuth.js v5 setup
 * 
 * Exports:
 * - auth: Get the current session (server-side)
 * - signIn: Sign in function
 * - signOut: Sign out function
 * - handlers: API route handlers (GET, POST)
 */
export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth(authConfig);



