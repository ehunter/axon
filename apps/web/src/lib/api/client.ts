/**
 * Type-safe API client for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Base fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add auth token if available
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw new ApiError(
      errorData.detail || "An error occurred",
      response.status,
      errorData
    );
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) return {} as T;

  return JSON.parse(text);
}

// ============================================
// Sample Types
// ============================================

export interface Sample {
  id: string;
  source_bank: string;
  external_id: string;
  donor_age: number | null;
  donor_sex: string | null;
  donor_race: string | null;
  primary_diagnosis: string | null;
  brain_region: string | null;
  rin_score: number | null;
  postmortem_interval_hours: number | null;
  preservation_method: string | null;
  hemisphere: string | null;
}

export interface SampleSearchParams {
  diagnosis?: string;
  brain_region?: string;
  min_age?: number;
  max_age?: number;
  sex?: string;
  min_rin?: number;
  max_pmi?: number;
  source_bank?: string;
  limit?: number;
  offset?: number;
}

export interface SampleSearchResult {
  samples: Sample[];
  total: number;
}

// ============================================
// Conversation Types
// ============================================

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

// ============================================
// Selection Types
// ============================================

export interface SelectedSample {
  id: string;
  external_id: string;
  diagnosis: string | null;
  age: number | null;
  sex: string | null;
  rin: number | null;
  pmi: number | null;
  brain_region: string | null;
  source_bank: string | null;
}

export interface Selection {
  cases: SelectedSample[];
  controls: SelectedSample[];
}

// ============================================
// API Functions
// ============================================

export const api = {
  // Samples
  samples: {
    search: (params: SampleSearchParams) =>
      fetchApi<SampleSearchResult>("/api/v1/samples", {
        method: "POST",
        body: JSON.stringify(params),
      }),

    get: (id: string) => fetchApi<Sample>(`/api/v1/samples/${id}`),

    getFilters: () =>
      fetchApi<{
        diagnoses: string[];
        brain_regions: string[];
        source_banks: string[];
      }>("/api/v1/samples/filters"),
  },

  // Conversations
  conversations: {
    list: (limit = 20) =>
      fetchApi<Conversation[]>(`/api/v1/conversations?limit=${limit}`),

    get: (id: string) =>
      fetchApi<ConversationWithMessages>(`/api/v1/conversations/${id}`),

    create: (title?: string) =>
      fetchApi<Conversation>("/api/v1/conversations", {
        method: "POST",
        body: JSON.stringify({ title }),
      }),

    delete: (id: string) =>
      fetchApi<void>(`/api/v1/conversations/${id}`, {
        method: "DELETE",
      }),
  },

  // Chat
  chat: {
    send: (conversationId: string, message: string) =>
      fetchApi<{ response: string }>(`/api/v1/chat/${conversationId}`, {
        method: "POST",
        body: JSON.stringify({ message }),
      }),

    // Streaming chat - returns a ReadableStream
    stream: async function* (
      conversationId: string,
      message: string
    ): AsyncGenerator<string> {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chat/${conversationId}/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message }),
        }
      );

      if (!response.ok) {
        throw new ApiError("Chat stream failed", response.status);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        yield decoder.decode(value);
      }
    },
  },

  // Selection
  selection: {
    get: (conversationId: string) =>
      fetchApi<Selection>(`/api/v1/conversations/${conversationId}/selection`),

    clear: (conversationId: string) =>
      fetchApi<void>(`/api/v1/conversations/${conversationId}/selection`, {
        method: "DELETE",
      }),
  },

  // Health check
  health: () => fetchApi<{ status: string }>("/api/v1/health"),
};

