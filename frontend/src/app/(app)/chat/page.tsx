"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Plane, Loader2, MessageSquare, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  tools_used?: string[];
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
  const [activeTab, setActiveTab] = useState<"concierge" | "rag" | "agent">("concierge");

  // --- Concierge State ---
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sessionId = useRef<string>("");
  if (!sessionId.current) {
    sessionId.current = crypto.randomUUID();
  }
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeTab === "concierge" || activeTab === "agent") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, activeTab]);

  // --- Smart Agent State ---
  const [agentInput, setAgentInput] = useState("");
  const [agentMessages, setAgentMessages] = useState<Message[]>([
    { id: "agent-welcome", role: "ai", content: "Hi! I am your Smart Agent. I can fetch live weather, convert currencies, generate PDF itineraries, and search our knowledge base. How can I assist you today?" }
  ]);
  const [isAgentLoading, setIsAgentLoading] = useState(false);

  // --- RAG State ---
  const [ragInput, setRagInput] = useState("");
  const [ragAnswer, setRagAnswer] = useState<{answer: string, sources: string[]} | null>(null);
  const [isRagLoading, setIsRagLoading] = useState(false);
  const [ragError, setRagError] = useState("");

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleSendConcierge = async (e: React.FormEvent) => {
    e.preventDefault();
    const userInput = input.trim();
    if (!userInput || isStreaming) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    const aiMsgId = `ai-${Date.now()}`;
    setMessages((prev) => [...prev, { id: aiMsgId, role: "ai", content: "" }]);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

      const response = await fetch(`${API_URL}/ai/sessions/${sessionId.current}/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content: userInput }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
      }

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
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId && m.content === ""
            ? {
                ...m,
                content: "Sorry, I couldn't reach the AI Concierge. Please check your connection and try again.",
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSendRag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragInput.trim() || isRagLoading) return;
    
    setIsRagLoading(true);
    setRagAnswer(null);
    setRagError("");

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      
      const res = await fetch(`${API_URL}/rag/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: ragInput.trim() }),
      });
      
      if (!res.ok) throw new Error("Failed to query knowledge base");
      const data = await res.json();
      setRagAnswer(data);
    } catch {
      setRagError("Sorry, there was an error querying the destination knowledge base.");
    } finally {
      setIsRagLoading(false);
    }
  };

  const handleSendAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    const userInput = agentInput.trim();
    if (!userInput || isAgentLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: userInput };
    setAgentMessages((prev) => [...prev, userMsg]);
    setAgentInput("");
    setIsAgentLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

      const res = await fetch(`${API_URL}/ai/agent/${sessionId.current}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userInput }),
      });

      if (!res.ok) throw new Error("Agent request failed");
      const data = await res.json();

      setAgentMessages((prev) => [
        ...prev,
        { id: `ai-${Date.now()}`, role: "ai", content: data.response, tools_used: data.tools_used }
      ]);
    } catch {
      setAgentMessages((prev) => [
        ...prev,
        { id: `ai-${Date.now()}`, role: "ai", content: "Sorry, I encountered an error while processing your request." }
      ]);
    } finally {
      setIsAgentLoading(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto border rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Header & Tabs */}
      <div className="bg-blue-600 px-6 py-4 text-white">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-white/20 p-2 rounded-lg">
            <Plane className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold">Travel Assistants</h2>
            <p className="text-blue-100 text-xs">Powered by AI</p>
          </div>
        </div>

        <div className="flex gap-2 bg-blue-700/50 p-1 rounded-lg">
          <button 
            onClick={() => setActiveTab("concierge")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "concierge" ? "bg-white text-blue-600 shadow-sm" : "text-blue-100 hover:text-white hover:bg-white/10"}`}
          >
            <MessageSquare className="w-4 h-4" />
            AI Concierge
          </button>
          <button 
            onClick={() => setActiveTab("agent")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "agent" ? "bg-white text-blue-600 shadow-sm" : "text-blue-100 hover:text-white hover:bg-white/10"}`}
          >
            <Bot className="w-4 h-4" />
            Smart Agent
          </button>
          <button 
            onClick={() => setActiveTab("rag")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "rag" ? "bg-white text-blue-600 shadow-sm" : "text-blue-100 hover:text-white hover:bg-white/10"}`}
          >
            <BookOpen className="w-4 h-4" />
            Destination Knowledge
          </button>
        </div>
      </div>

      {activeTab === "concierge" ? (
        <>
          <ScrollArea className="flex-1 p-6">
            <div className="space-y-6">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
                    {msg.role === "ai" ? (
                      <AvatarFallback className="bg-blue-100 text-blue-600">
                        <Bot className="w-4 h-4" />
                      </AvatarFallback>
                    ) : (
                      <>
                        <AvatarImage src="https://ui.shadcn.com/avatars/01.png" />
                        <AvatarFallback><User className="w-4 h-4" /></AvatarFallback>
                      </>
                    )}
                  </Avatar>
                  <div className={`rounded-2xl px-5 py-3 max-w-[80%] ${msg.role === "user" ? "bg-blue-600 text-white rounded-tr-sm" : "bg-neutral-100 text-neutral-900 rounded-tl-sm"}`}>
                    {msg.content ? (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="flex gap-1 items-center py-1">
                        <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:0ms]" />
                        <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:150ms]" />
                        <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:300ms]" />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          <div className="p-4 border-t bg-neutral-50">
            <form onSubmit={handleSendConcierge} className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="E.g., What's the weather like in Paris next week?"
                className="flex-1 bg-white"
                disabled={isStreaming}
              />
              <Button type="submit" disabled={!input.trim() || isStreaming}>
                {isStreaming ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                {isStreaming ? "Thinking..." : "Send"}
              </Button>
            </form>
          </div>
        </>
      ) : activeTab === "agent" ? (
        <>
          <ScrollArea className="flex-1 p-6">
            <div className="space-y-6">
              {agentMessages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
                    {msg.role === "ai" ? (
                      <AvatarFallback className="bg-purple-100 text-purple-600">
                        <Bot className="w-4 h-4" />
                      </AvatarFallback>
                    ) : (
                      <>
                        <AvatarImage src="https://ui.shadcn.com/avatars/01.png" />
                        <AvatarFallback><User className="w-4 h-4" /></AvatarFallback>
                      </>
                    )}
                  </Avatar>
                  <div className={`rounded-2xl px-5 py-3 max-w-[80%] ${msg.role === "user" ? "bg-blue-600 text-white rounded-tr-sm" : "bg-neutral-100 text-neutral-900 rounded-tl-sm"}`}>
                    {msg.tools_used && msg.tools_used.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-2">
                        {msg.tools_used.map((t) => (
                          <span key={t} className="inline-flex items-center px-2 py-1 rounded bg-purple-200 text-purple-800 text-[10px] font-bold uppercase tracking-wider">
                            🛠️ {t.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </p>
                  </div>
                </div>
              ))}
              {isAgentLoading && (
                <div className="flex gap-4">
                  <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
                    <AvatarFallback className="bg-purple-100 text-purple-600">
                      <Bot className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="rounded-2xl px-5 py-3 max-w-[80%] bg-neutral-100 text-neutral-900 rounded-tl-sm">
                    <div className="flex gap-1 items-center py-1">
                      <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:0ms]" />
                      <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:150ms]" />
                      <span className="w-2 h-2 rounded-full bg-neutral-400 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          <div className="p-4 border-t bg-neutral-50">
            <form onSubmit={handleSendAgent} className="flex gap-2">
              <Input
                value={agentInput}
                onChange={(e) => setAgentInput(e.target.value)}
                placeholder="E.g., Convert $500 to EUR"
                className="flex-1 bg-white"
                disabled={isAgentLoading}
              />
              <Button type="submit" disabled={!agentInput.trim() || isAgentLoading}>
                {isAgentLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                {isAgentLoading ? "Thinking..." : "Send"}
              </Button>
            </form>
          </div>
        </>
      ) : (
        <>
          <ScrollArea className="flex-1 p-6 bg-neutral-50/50">
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="text-center py-8">
                <div className="bg-blue-100 text-blue-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Destination Knowledge Assistant</h3>
                <p className="text-neutral-500 text-sm">
                  Ask grounded questions about travel destinations. Answers are generated exclusively from our verified knowledge base.
                </p>
              </div>

              {ragError && (
                <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm text-center">
                  {ragError}
                </div>
              )}

              {ragAnswer && (
                <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
                  <div className="p-5 border-b">
                    <p className="text-sm leading-relaxed text-neutral-800 whitespace-pre-wrap">{ragAnswer.answer}</p>
                  </div>
                  <div className="bg-neutral-50 p-4">
                    <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Sources Used</p>
                    {ragAnswer.sources && ragAnswer.sources.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {ragAnswer.sources.map((source, idx) => (
                          <span key={idx} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {source}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-400 italic">No direct sources were referenced.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
          <div className="p-4 border-t bg-neutral-50">
            <form onSubmit={handleSendRag} className="flex gap-2 max-w-2xl mx-auto">
              <Input
                value={ragInput}
                onChange={(e) => setRagInput(e.target.value)}
                placeholder="E.g., What food should I try in Japan?"
                className="flex-1 bg-white"
                disabled={isRagLoading}
              />
              <Button type="submit" disabled={!ragInput.trim() || isRagLoading}>
                {isRagLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                {isRagLoading ? "Searching..." : "Ask"}
              </Button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
