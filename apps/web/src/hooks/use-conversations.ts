"use client";

import { useState, useEffect, useCallback } from "react";

export interface Conversation {
  id: string;
  title: string | null;
  messageCount: number;
  createdAt: Date;
  updatedAt: Date;
}

interface UseConversationsOptions {
  limit?: number;
}

export function useConversations(options: UseConversationsOptions = {}) {
  const { limit = 10 } = options;
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/conversations?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch conversations");
      }

      const data = await response.json();
      
      // Transform API response to frontend format
      const transformed: Conversation[] = data.conversations.map(
        (conv: {
          id: string;
          title: string | null;
          message_count: number;
          created_at: string;
          updated_at: string;
        }) => ({
          id: conv.id,
          title: conv.title,
          messageCount: conv.message_count,
          createdAt: new Date(conv.created_at),
          updatedAt: new Date(conv.updated_at),
        })
      );

      setConversations(transformed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  // Fetch on mount
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return {
    conversations,
    isLoading,
    error,
    refetch: fetchConversations,
  };
}

