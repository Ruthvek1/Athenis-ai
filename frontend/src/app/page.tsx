"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import axios from "axios";

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [role, setRole] = useState("user");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const router = useRouter();

  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Pre-fill demo credentials
  useEffect(() => {
    if (isDemoMode) {
      setEmail("admin@athenis.ai");
      setPassword("demo123");
      setRole("admin");
      setIsLogin(true);
    }
  }, [isDemoMode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    
    if (isLogin) {
      try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        
        const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        
        const token = response.data.access_token;
        
        // Verify user role
        const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        const isAdmin = userResponse.data.is_admin;
        
        if (role === "admin" && !isAdmin) {
          setError("Access Denied: You do not have administrator privileges.");
          return;
        }
        
        localStorage.setItem("token", token);
        localStorage.setItem("role", role);
        
        if (isDemoMode) {
          try {
            const docsResponse = await axios.get(`${API_URL}/api/v1/documents/`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            if (docsResponse.data.length === 0) {
              router.push("/admin?demo_welcome=true");
              return;
            }
          } catch (err) {
            console.error("Failed to check documents", err);
          }
        }
        
        if (role === "admin") {
          router.push("/dashboard");
        } else {
          router.push("/chat");
        }
      } catch (err) {
        setError("Invalid credentials. Please try again.");
      }
    } else {
      try {
        await axios.post(`${API_URL}/api/v1/auth/register`, {
          email,
          password,
          is_admin: role === "admin"
        });
        setSuccess("Account created! You can now log in.");
        setIsLogin(true);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Registration failed. Try a different email.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-8"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mb-4">
            <BookOpen className="w-8 h-8 text-blue-500" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Athenis</h1>
          <p className="text-gray-400 mt-2 text-center">AI-Powered RAG Knowledge Assistant</p>
        </div>

        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/50 text-emerald-500 p-3 rounded-xl mb-6 text-sm text-center">
            {success}
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-xl mb-6 text-sm text-center">
            {error}
          </div>
        )}

        {isDemoMode && (
          <div className="bg-blue-500/10 border border-blue-500/50 text-blue-400 p-3 rounded-xl mb-6 text-sm text-center font-medium shadow-[0_0_15px_rgba(59,130,246,0.15)]">
            ✨ This is a demonstration environment. Log in using the pre-filled demo credentials.
          </div>
        )}

        {!isDemoMode && (
          <div className="flex bg-gray-800 rounded-lg p-1 mb-4">
            <button
              onClick={() => { setIsLogin(true); setError(""); setSuccess(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${isLogin ? "bg-gray-700 text-white shadow" : "text-gray-400 hover:text-gray-200"}`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(""); setSuccess(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${!isLogin ? "bg-gray-700 text-white shadow" : "text-gray-400 hover:text-gray-200"}`}
            >
              Register
            </button>
          </div>
        )}

        <div className="flex bg-gray-950 rounded-lg p-1 mb-6 border border-gray-800">
          <button
            type="button"
            onClick={() => setRole("user")}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${role === "user" ? "bg-blue-600 text-white shadow" : "text-gray-400 hover:text-gray-200"}`}
          >
            User Access
          </button>
          <button
            type="button"
            onClick={() => setRole("admin")}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${role === "admin" ? "bg-emerald-600 text-white shadow" : "text-gray-400 hover:text-gray-200"}`}
          >
            Admin Access
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              required 
              suppressHydrationWarning
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              required 
              suppressHydrationWarning
            />
          </div>
          <button 
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-xl transition-colors mt-4"
          >
            {isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
