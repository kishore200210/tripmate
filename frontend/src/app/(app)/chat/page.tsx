"use client";

import { useState } from "react";
import { Send, Bot, User, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      id: "1",
      role: "ai",
      content: "Hello! I'm your TripMate AI Concierge. I can help you plan an itinerary, check weather for your destinations, or suggest places based on your budget. How can I help you today?"
    }
  ]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMsg = { id: Date.now().toString(), role: "user", content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");

    // Mock AI response
    setTimeout(() => {
      const aiMsg = { 
        id: (Date.now() + 1).toString(), 
        role: "ai", 
        content: "I'm currently running in mock mode for the frontend UI demonstration. To get actual responses, I would need to connect to the LangGraph AI Agent backend we built earlier!" 
      };
      setMessages(prev => [...prev, aiMsg]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto border rounded-xl overflow-hidden bg-white shadow-sm">
      <div className="bg-blue-600 px-6 py-4 flex items-center gap-3 text-white">
        <div className="bg-white/20 p-2 rounded-lg">
          <Plane className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold">AI Travel Concierge</h2>
          <p className="text-blue-100 text-xs">Powered by LangGraph & GPT-4o</p>
        </div>
      </div>

      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
                {msg.role === "ai" ? (
                  <>
                    <AvatarFallback className="bg-blue-100 text-blue-600"><Bot className="w-4 h-4" /></AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarImage src="https://ui.shadcn.com/avatars/01.png" />
                    <AvatarFallback><User className="w-4 h-4" /></AvatarFallback>
                  </>
                )}
              </Avatar>
              
              <div className={`rounded-2xl px-5 py-3 max-w-[80%] ${
                msg.role === "user" 
                  ? "bg-blue-600 text-white rounded-tr-sm" 
                  : "bg-neutral-100 text-neutral-900 rounded-tl-sm"
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t bg-neutral-50">
        <form onSubmit={handleSend} className="flex gap-2">
          <Input 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="E.g., What's the weather like in Paris next week?" 
            className="flex-1 bg-white"
          />
          <Button type="submit" disabled={!input.trim()}>
            <Send className="w-4 h-4 mr-2" /> Send
          </Button>
        </form>
      </div>
    </div>
  );
}
