"use client";

import Link from "next/link";
import { MessageSquare, Clock, Trash2 } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

const conversations = [
  {
    id: "1",
    title: "Alzheimer's frontal cortex samples",
    message_count: 12,
    updated_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "2",
    title: "Control samples for RNA-seq",
    message_count: 8,
    updated_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "3",
    title: "Parkinson's substantia nigra",
    message_count: 15,
    updated_at: new Date(Date.now() - 172800000).toISOString(),
  },
];

export default function HistoryPage() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Conversation History</h1>
          <p className="text-muted-foreground">
            Resume previous conversations and access your saved selections
          </p>
        </div>

        <div className="space-y-3">
          {conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/chat?conversation=${conversation.id}`}
              className="block p-4 rounded-xl border border-border bg-card hover:border-brand-500/50 hover:shadow-md transition-all group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center group-hover:bg-brand-500 transition-colors">
                    <MessageSquare className="h-5 w-5 text-brand-500 group-hover:text-white transition-colors" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{conversation.title}</h3>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{conversation.message_count} messages</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {formatRelativeTime(conversation.updated_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    // TODO: Delete conversation
                  }}
                  className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Link>
          ))}
        </div>

        {conversations.length === 0 && (
          <div className="text-center py-12">
            <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No conversations yet</h3>
            <p className="text-muted-foreground mb-4">
              Start a new chat to find brain tissue samples
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
            >
              Start New Chat
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}



