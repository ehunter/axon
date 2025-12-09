import type { NextAuthConfig } from "next-auth";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

/**
 * NextAuth configuration
 * 
 * Supports multiple authentication providers:
 * - GitHub OAuth (for development)
 * - Google OAuth (for production)
 * - Credentials (email/password - for testing)
 * 
 * Add more providers as needed (Azure AD, Okta, etc.)
 */
export const authConfig: NextAuthConfig = {
  providers: [
    // GitHub OAuth - good for development
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
    }),
    
    // Google OAuth - common for research institutions
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
    }),
    
    // Credentials provider for email/password (optional)
    // In production, you'd validate against your user database
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // For development/demo purposes only
        // In production, validate against your database
        if (
          credentials?.email === "demo@axon.research" &&
          credentials?.password === "demo123"
        ) {
          return {
            id: "demo-user",
            name: "Demo Researcher",
            email: "demo@axon.research",
            image: null,
          };
        }
        return null;
      },
    }),
  ],
  
  pages: {
    signIn: "/login",
    error: "/login",
  },
  
  callbacks: {
    // Control access to pages
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isOnDashboard = nextUrl.pathname.startsWith("/chat") ||
                           nextUrl.pathname.startsWith("/samples") ||
                           nextUrl.pathname.startsWith("/history") ||
                           nextUrl.pathname.startsWith("/settings");
      
      if (isOnDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect to login
      }
      
      // Allow access to public pages
      return true;
    },
    
    // Add user info to session
    async session({ session, token }) {
      if (token.sub && session.user) {
        session.user.id = token.sub;
      }
      return session;
    },
    
    // Add user ID to JWT token
    async jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
      }
      return token;
    },
  },
  
  // Use JWT for session strategy (stateless, scalable)
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  
  // Enable debug in development
  debug: process.env.NODE_ENV === "development",
};



