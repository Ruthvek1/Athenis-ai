"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { MessageSquare, FileText, Activity, Database, Code, ShieldCheck, LogOut, ArrowRight, LayoutDashboard } from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    setIsMounted(true);
    if (!localStorage.getItem("token")) {
      router.push("/");
    } else if (localStorage.getItem("role") !== "admin") {
      router.push("/chat");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (!isMounted) return null;

  const interfaces = [
    {
      title: "Athenis Chat",
      description: "AI-Powered RAG Knowledge Assistant interface for users.",
      icon: MessageSquare,
      color: "bg-blue-600",
      href: "/chat",
      external: false
    },
    {
      title: "Document Management",
      description: "Admin portal to upload and manage RAG knowledge base files.",
      icon: FileText,
      color: "bg-purple-600",
      href: "/admin",
      external: false
    },
    {
      title: "System Analytics (Grafana)",
      description: "Visual dashboards for application and server performance.",
      icon: Activity,
      color: "bg-orange-600",
      href: "http://localhost:3001",
      external: true
    },
    {
      title: "Raw Metrics (Prometheus)",
      description: "Time-series database and monitoring alerts.",
      icon: Database,
      color: "bg-rose-600",
      href: "http://localhost:9090",
      external: true
    },
    {
      title: "API Documentation",
      description: "Interactive Swagger UI for the FastAPI backend.",
      icon: Code,
      color: "bg-emerald-600",
      href: `${API_URL}/docs`,
      external: true
    }
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans selection:bg-blue-500/30">
      {/* Top Navigation */}
      <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600/20 rounded-xl flex items-center justify-center border border-blue-500/30">
              <LayoutDashboard className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">Athenis Command Center</h1>
              <p className="text-xs text-gray-400">Unified System Dashboard</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
              <ShieldCheck className="w-4 h-4" />
              <span>Admin Access</span>
            </div>
            <button 
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              title="Log out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Welcome Back</h2>
          <p className="text-gray-400 max-w-2xl text-lg">
            Manage your entire enterprise AI stack from this unified control plane. Monitor system health, manage knowledge bases, and access user interfaces.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {interfaces.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="h-full"
            >
              <a
                href={item.href}
                target={item.external ? "_blank" : "_self"}
                rel={item.external ? "noopener noreferrer" : ""}
                className="block group h-full"
                onClick={(e) => {
                  if (!item.external) {
                    e.preventDefault();
                    router.push(item.href);
                  }
                }}
              >
                <div className="h-full bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:border-gray-600 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 relative overflow-hidden flex flex-col">
                  <div className={`w-12 h-12 ${item.color} rounded-xl flex items-center justify-center mb-6 shadow-lg`}>
                    <item.icon className="w-6 h-6 text-white" />
                  </div>
                  
                  <h3 className="text-xl font-bold text-gray-100 mb-2 group-hover:text-white flex items-center justify-between">
                    {item.title}
                    <ArrowRight className="w-5 h-5 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-gray-400" />
                  </h3>
                  
                  <p className="text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors flex-1">
                    {item.description}
                  </p>

                  {item.external && (
                    <div className="absolute top-6 right-6">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 bg-gray-800 px-2 py-1 rounded-md">
                        External Tool
                      </span>
                    </div>
                  )}
                </div>
              </a>
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  );
}
