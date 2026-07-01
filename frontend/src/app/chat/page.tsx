"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Bot, Loader2, LogOut, Settings } from "lucide-react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Citation {
  id: number;
  filename: string;
  chunk_index: number;
  similarity_score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [demoDocsReady, setDemoDocsReady] = useState(true);
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/");
    }
    if (localStorage.getItem("role") === "admin") {
      setIsAdmin(true);
    }

    if (isDemoMode) {
      setDemoDocsReady(false);
      
      const checkDocs = async () => {
        try {
          const res = await axios.get(`${API_URL}/api/v1/documents/`, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
          });
          
          if (res.data.some((d: any) => d.status === "Ready")) {
            setDemoDocsReady(true);
          } else if (res.data.length > 0) {
            // Docs exist but none are ready, set up polling
            startPolling();
          }
        } catch (e) {
          console.error(e);
        }
      };
      
      checkDocs();
    }
  }, [router, isDemoMode]);

  const startPolling = () => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/documents/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        });
        if (res.data.some((d: any) => d.status === "Ready")) {
          setDemoDocsReady(true);
          clearInterval(interval);
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 2000);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/chat/`,
        { query: userMessage.content, session_id: sessionId },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );

      if (!sessionId) setSessionId(response.data.session_id);

      const aiMessage: Message = {
        role: "assistant",
        content: response.data.answer,
        citations: response.data.citations,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        localStorage.removeItem("token");
        router.push("/");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h1 className="font-bold text-xl tracking-tight text-white">Athenis</h1>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <button 
            onClick={() => { setSessionId(null); setMessages([]); }}
            className="w-full bg-blue-600/10 text-blue-500 border border-blue-500/20 rounded-xl py-2 px-4 font-medium hover:bg-blue-600/20 transition-colors"
          >
            + New Chat
          </button>
        </div>
        <div className="p-4 border-t border-gray-800 space-y-2">
          {isAdmin && (
            <button 
              onClick={() => router.push("/dashboard")}
              className="w-full flex items-center space-x-2 text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800"
            >
              <Settings className="w-4 h-4" />
              <span>System Dashboard</span>
            </button>
          )}
          <button 
            onClick={handleLogout}
            className="w-full flex items-center space-x-2 text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800"
          >
            <LogOut className="w-4 h-4" />
            <span>Log out</span>
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
              <Bot className="w-16 h-16 text-gray-700" />
              <p className="text-xl font-medium">How can I help you today?</p>
            </div>
          ) : (
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`flex space-x-3 max-w-3xl ${msg.role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === "user" ? "bg-blue-600" : "bg-emerald-600"}`}>
                      {msg.role === "user" ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                    </div>
                    <div className={`p-4 rounded-2xl ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100 border border-gray-700"}`}>
                      {msg.role === "user" ? (
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                      ) : (
                        <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-gray-700 space-y-2">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sources</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.citations.map((cit, i) => (
                              <span key={i} className="text-xs bg-gray-900 border border-gray-700 px-2 py-1 rounded-md text-gray-300 flex items-center space-x-1">
                                <span>[{cit.id}] {cit.filename}</span>
                                <span className="text-emerald-500 ml-2">{(cit.similarity_score * 100).toFixed(1)}%</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="flex space-x-3 max-w-3xl">
                <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="p-4 rounded-2xl bg-gray-800 text-gray-100 border border-gray-700 flex items-center space-x-2">
                  <Loader2 className="w-5 h-5 animate-spin text-emerald-500" />
                  <span className="text-gray-400 animate-pulse">Thinking...</span>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-gray-950 border-t border-gray-900">
          <div className="max-w-4xl mx-auto relative">
            {!demoDocsReady && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-gray-950/80 backdrop-blur-sm rounded-2xl border border-red-500/30 text-red-400 font-medium">
                Document ingestion required. Please upload a document in the System Dashboard.
              </div>
            )}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && demoDocsReady && handleSend()}
              placeholder="Ask Athenis anything..."
              disabled={!demoDocsReady || loading}
              className={`w-full bg-gray-900 border border-gray-700 rounded-2xl pl-6 pr-14 py-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all shadow-xl ${!demoDocsReady ? 'opacity-50 cursor-not-allowed' : ''}`}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || !demoDocsReady}
              className="absolute right-2 top-2 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-xl transition-colors z-20"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
