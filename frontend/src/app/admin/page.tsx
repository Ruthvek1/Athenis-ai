"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Upload, FileText, CheckCircle, Loader2, ArrowLeft, RefreshCw, XCircle } from "lucide-react";
import axios from "axios";

interface Document {
  id: number;
  filename: string;
  status: string;
  created_at: string;
}

export default function AdminDashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isDemoWelcome, setIsDemoWelcome] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const router = useRouter();

  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/documents/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setDocuments(response.data);
      return response.data;
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        router.push("/");
      }
    }
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/");
      return;
    } else if (localStorage.getItem("role") !== "admin") {
      router.push("/chat");
      return;
    }

    if (window.location.search.includes("demo_welcome=true")) {
      setIsDemoWelcome(true);
    }

    const checkDocs = async () => {
      const docs = await fetchDocuments();
      // Only set up polling if there are pending docs
      if (docs && docs.some((d: any) => d.status !== "Ready" && d.status !== "Failed")) {
        startPolling();
      }
    };
    checkDocs();
  }, []);

  const startPolling = () => {
    const interval = setInterval(async () => {
      const docs = await fetchDocuments();
      // Stop polling if all are ready or failed
      if (!docs || !docs.some((d: any) => d.status !== "Ready" && d.status !== "Failed")) {
        clearInterval(interval);
      }
    }, 2000);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await axios.post(`${API_URL}/api/v1/documents/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        signal: abortController.signal
      });
      startPolling();
      fetchDocuments();
    } catch (err) {
      if (axios.isCancel(err)) {
        console.log("Upload cancelled by user.");
      } else {
        console.error(err);
        alert("Failed to upload document.");
      }
    } finally {
      setUploading(false);
      abortControllerRef.current = null;
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Ready": return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case "Failed": return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => router.push("/dashboard")}
              className="p-2 bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          </div>
          <div className="flex items-center space-x-3">
            {uploading && (
              <button 
                onClick={handleCancelUpload}
                className="flex items-center space-x-2 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 px-4 py-3 rounded-xl transition-all font-medium"
              >
                <span>Cancel</span>
              </button>
            )}
            
            {isDemoMode && documents.length === 0 && (
              <button 
                onClick={async () => {
                  try {
                    setUploading(true);
                    const response = await fetch("/sample-document.txt");
                    const blob = await response.blob();
                    const file = new File([blob], "Athenis_Employee_Handbook.txt", { type: "text/plain" });
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    if (fileInputRef.current) {
                      fileInputRef.current.files = dt.files;
                      handleFileUpload({ target: { files: dt.files } } as any);
                    }
                  } catch (e) {
                    console.error("Failed to load sample document", e);
                    setUploading(false);
                  }
                }}
                disabled={uploading}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white px-6 py-3 rounded-xl transition-all font-medium border border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
              >
                <FileText className="w-5 h-5" />
                <span>{uploading ? "Loading..." : "Load Sample Data"}</span>
              </button>
            )}

            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 disabled:text-gray-500 text-white px-6 py-3 rounded-xl transition-all font-medium"
            >
              {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
              <span>{uploading ? "Uploading..." : "Upload Document"}</span>
            </button>
          </div>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".pdf,.docx,.txt,.md" 
          />
        </div>

        {isDemoWelcome && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900 border border-emerald-500/50 rounded-2xl p-8 shadow-[0_0_30px_rgba(16,185,129,0.15)] relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-2 h-full bg-emerald-500"></div>
            <h2 className="text-2xl font-bold text-white mb-4">Welcome to Athenis AI! 👋</h2>
            <p className="text-gray-300 text-lg mb-6 max-w-3xl leading-relaxed">
              Before you can start chatting with your AI knowledge assistant, you must construct a Knowledge Base. 
              Please upload one or more documents, or use the <strong>Load Sample Data</strong> button above. 
              Once document chunking, embedding, and indexing are complete, you can immediately begin asking questions.
            </p>
            
            <div className="bg-gray-950 rounded-xl p-6 border border-gray-800">
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-4">Onboarding Checklist</h3>
              <ul className="space-y-3">
                <li className="flex items-center space-x-3 text-emerald-400">
                  <CheckCircle className="w-5 h-5" /> <span>Login to Admin Dashboard</span>
                </li>
                <li className={`flex items-center space-x-3 ${documents.length > 0 ? "text-emerald-400" : "text-gray-400"}`}>
                  {documents.length > 0 ? <CheckCircle className="w-5 h-5" /> : <div className="w-5 h-5 border-2 border-gray-600 rounded-full" />} 
                  <span>Upload a document</span>
                </li>
                <li className={`flex items-center space-x-3 ${documents.some(d => d.status === "Ready") ? "text-emerald-400" : documents.length > 0 ? "text-blue-400" : "text-gray-400"}`}>
                  {documents.some(d => d.status === "Ready") ? <CheckCircle className="w-5 h-5" /> : documents.length > 0 ? <Loader2 className="w-5 h-5 animate-spin" /> : <div className="w-5 h-5 border-2 border-gray-600 rounded-full" />} 
                  <span>Wait for vector indexing</span>
                </li>
                <li className={`flex items-center space-x-3 ${documents.some(d => d.status === "Ready") ? "text-white font-medium" : "text-gray-500"}`}>
                  <div className="w-5 h-5 border-2 border-gray-600 rounded-full" /> 
                  <span>Navigate to <button onClick={() => router.push("/chat")} className="text-emerald-500 hover:underline">Chat</button> to ask questions</span>
                </li>
              </ul>
            </div>
          </motion.div>
        )}

        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
          <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/50">
            <h2 className="text-lg font-semibold text-gray-300">Document Processing Queue</h2>
            <button onClick={fetchDocuments} className="text-gray-500 hover:text-white transition-colors">
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
          <div className="divide-y divide-gray-800">
            {documents.length === 0 ? (
              <div className="p-12 text-center text-gray-500 flex flex-col items-center space-y-4">
                <FileText className="w-12 h-12 text-gray-700" />
                <p>No documents found. Upload one to get started.</p>
              </div>
            ) : (
              documents.map((doc) => (
                <motion.div 
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  key={doc.id} 
                  className="p-6 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-200">{doc.filename}</h3>
                      <p className="text-sm text-gray-500">{new Date(doc.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-400 capitalize">{doc.status}</span>
                    {getStatusIcon(doc.status)}
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
