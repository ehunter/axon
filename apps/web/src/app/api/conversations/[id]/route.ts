/**
 * Single Conversation API Route
 * 
 * Proxies conversation detail requests to the Python backend.
 */

import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export interface MessageItem {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface ConversationDetailResponse {
  id: string;
  title: string | null;
  messages: MessageItem[];
  created_at: string;
  updated_at: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const conversationId = params.id;

    const response = await fetch(
      `${BACKEND_URL}/api/v1/chat/conversations/${conversationId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new Response(
          JSON.stringify({ error: "Conversation not found" }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        );
      }
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
    console.error("Conversation API error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to fetch conversation" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

