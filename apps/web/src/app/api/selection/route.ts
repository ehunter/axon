import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * GET /api/selection
 * 
 * Fetch the current sample selection for a conversation.
 * Proxies to the Python backend.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const conversationId = searchParams.get("conversationId");

    if (!conversationId) {
      return new Response(
        JSON.stringify({ error: "conversationId is required" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Fetch selection from backend
    const response = await fetch(
      `${BACKEND_URL}/api/v1/chat/selection/${conversationId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      return new Response(
        JSON.stringify({ error: `Backend error: ${error}` }),
        { status: response.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Selection API error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to connect to selection service" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

