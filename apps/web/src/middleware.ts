import { auth } from "@/lib/auth";

/**
 * Middleware for protecting routes
 * 
 * This runs on every request to matched routes and checks
 * if the user is authenticated before allowing access.
 */
export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const { pathname } = req.nextUrl;

  // Protected routes that require authentication
  const protectedRoutes = ["/chat", "/samples", "/history", "/settings"];
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  // Redirect to login if trying to access protected route while not logged in
  if (isProtectedRoute && !isLoggedIn) {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return Response.redirect(loginUrl);
  }

  // Redirect to dashboard if already logged in and trying to access login
  if (pathname === "/login" && isLoggedIn) {
    return Response.redirect(new URL("/chat", req.nextUrl.origin));
  }
});

export const config = {
  // Match all routes except static files and API routes
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};


