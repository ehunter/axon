/**
 * Conversations API Route
 * 
 * Proxies conversation list requests to the Python backend.
 */

import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export interface ConversationListItem {
  id: string;
  title: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationsResponse {
  conversations: ConversationListItem[];
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = searchParams.get("limit") || "20";

    const response = await fetch(
      `${BACKEND_URL}/api/v1/chat/conversations?limit=${limit}`,
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
    console.error("Conversations API error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to fetch conversations" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

