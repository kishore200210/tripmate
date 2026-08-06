"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Plane, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

// ── Constants ──────────────────────────────────────────────────────────────────

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "ai",
  content:
    "Hello! I'm your TripMate AI Concierge. I can help you plan an itinerary, check weather for your destinations, or suggest places based on your budget. How can I help you today?",
};

// ── Component ──────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isStreaming, setIsStreaming] = useState(false);

  // Generate a stable session UUID for this page visit.
  // useRef ensures the same UUID persists across re-renders without causing re-renders.
  const sessionId = useRef<string>("");
  if (!sessionId.current) {
    // crypto.randomUUID() is available in all modern browsers and Node.js 15+
    sessionId.current = crypto.randomUUID();
  }

  // Ref to the invisible anchor div at the bottom of the message list
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message whenever messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── handleSend ─────────────────────────────────────────────────────────────

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const userInput = input.trim();
    if (!userInput || isStreaming) return;

    // 1. Immediately render the user message and clear the input field
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    // 2. Add an empty AI placeholder — it will be filled progressively by the stream
    const aiMsgId = `ai-${Date.now()}`;
    setMessages((prev) => [...prev, { id: aiMsgId, role: "ai", content: "" }]);

    try {
      // Backend: POST /api/v1/ai/sessions/{session_id}/stream
      // Request body: { content: string }
      // Response: text/plain, raw streaming chunks (not SSE)
      const API_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("auth_token")
          : null;

      const response = await fetch(
        `${API_URL}/ai/sessions/${sessionId.current}/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content: userInput }),
        }
      );

      if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      // 3. Read the plain-text stream chunk by chunk and append to the AI bubble
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId ? { ...m, content: m.content + chunk } : m
          )
        );
      }
    } catch {
      // If an error occurs before any content arrived, show an error in the bubble
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId && m.content === ""
            ? {
                ...m,
                content:
                  "Sorry, I couldn't reach the AI Concierge. Please check your connection and try again.",
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto border rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Header — unchanged */}
      <div className="bg-blue-600 px-6 py-4 flex items-center gap-3 text-white">
        <div className="bg-white/20 p-2 rounded-lg">
          <Plane className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold">AI Travel Concierge</h2>
          <p className="text-blue-100 text-xs">Powered by OpenAI GPT</p>
        </div>
      </div>

      {/* Messages — unchanged layout, added typing indicator and scroll anchor */}
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
                {msg.role === "ai" ? (
                  <>
                    <AvatarFallback className="bg-blue-100 text-blue-600">
                      <Bot className="w-4 h-4" />
                    </AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarImage src="https://ui.shadcn.com/avatars/01.png" />
                    <AvatarFallback>
                      <User className="w-4 h-4" />
                    </AvatarFallback>
                  </>
                )}
              </Avatar>

              <div
                className={`rounded-2xl px-5 py-3 max-w-[80%] ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm"
                    : "bg-neutral-100 text-neutral-900 rounded-tl-sm"
                }`}
              >
                {msg.content ? (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </p>
                ) : (
                  /* Animated typing indicator shown while the stream hasn't sent any content yet */
                  <div className="flex gap-1 items-center py-1">
                    <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:300ms]" />
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Invisible anchor — scrolled into view automatically when messages update */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input — unchanged layout, disabled while streaming */}
      <div className="p-4 border-t bg-neutral-50">
        <form onSubmit={handleSend} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="E.g., What's the weather like in Paris next week?"
            className="flex-1 bg-white"
            disabled={isStreaming}
          />
          <Button type="submit" disabled={!input.trim() || isStreaming}>
            {isStreaming ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            {isStreaming ? "Thinking..." : "Send"}
          </Button>
        </form>
      </div>
    </div>
  );
}
