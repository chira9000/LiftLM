"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "How is my bench progressing?",
  "What should I do for bench today?",
  "Why have I stopped progressing on squat?",
];

export default function CoachPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.chat(text, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I couldn't process that. Make sure the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-5.5rem)] flex-col lg:h-[calc(100vh-4rem)]">
      <PageHeader
        title="AI Coach"
        subtitle="Ask about your training — powered by structured analytics"
      />

      <div className="panel mb-4 flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center py-10 text-center animate-fade-up">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-400">
                <Sparkles className="h-6 w-6" />
              </div>
              <p className="mb-1 font-display text-lg font-semibold text-ink">Ask your coach</p>
              <p className="mb-6 max-w-sm text-sm text-surface-muted">
                Questions are answered from your analytics — volume, e1RM trends, and progression scores.
              </p>
              <div className="flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => send(s)}
                    className="rounded-xl border border-surface-border bg-surface-raised px-3.5 py-2 text-left text-sm text-ink-soft transition-all hover:border-brand-400/35 hover:bg-brand-500/5 hover:text-ink"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed sm:max-w-[70%] ${
                  msg.role === "user"
                    ? "bg-brand-500/15 text-ink"
                    : "border border-surface-border bg-surface-raised text-ink-soft"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
              {msg.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-surface-hover text-surface-muted">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl border border-surface-border bg-surface-raised px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-surface-muted [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-surface-muted [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-surface-muted [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex gap-2.5 border-t border-surface-border p-3 sm:p-4"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your coach..."
            className="input-field flex-1"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-primary h-11 w-11 shrink-0 !px-0"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
