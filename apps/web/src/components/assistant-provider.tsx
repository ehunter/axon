"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useAxonRuntime } from "@/lib/assistant-ui/use-axon-runtime";

interface AssistantProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component that wraps the chat with Axon's custom runtime
 */
export function AssistantProvider({ children }: AssistantProviderProps) {
  const { runtime } = useAxonRuntime();

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}




