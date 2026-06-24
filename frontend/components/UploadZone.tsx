"use client";

import React, { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";

export default function UploadZone() {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [statusText, setStatusText] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processUpload = async (file: File) => {
    setErrorMsg(null);
    try {
      setIsUploading(true);
      
      // Phase 1: Save the document to the server
      setStatusText("Uploading blueprint asset...");
      const uploadResponse = await api.uploadFiles([file], {});
      const projectId = uploadResponse.project.id;

      // Phase 2: Trigger the Project Intelligence Engine (Docling + Ontology)
      setStatusText("Running Docling layout analysis. This may take a minute...");
      await api.analyzeProject(projectId);

      // Phase 3: Route to populated dashboard
      setStatusText("Analysis complete! Rendering UI...");
      router.push(`/results?projectId=${projectId}`);
      
    } catch (error) {
      console.error("Upload/Analysis sequence failed:", error);
      setErrorMsg("Processing failed. Check backend terminal for Docling/OpenAI errors.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processUpload(file);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processUpload(file);
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileSelect}
        accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif"
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-16 text-center transition-all duration-200 ${
          isUploading ? "cursor-wait border-blueprint-500 bg-blueprint-900/40" : "cursor-pointer"
        } ${
          isDragging
            ? "border-signal-orange bg-blueprint-900/40"
            : "border-blueprint-700 hover:border-blueprint-600 bg-blueprint-900/20"
        }`}
      >
        <div className="space-y-4">
          <h3 className="text-xl font-medium text-blueprint-100">
            {isUploading ? statusText : "Click to upload or drag and drop"}
          </h3>
          {!isUploading && (
            <p className="text-sm text-blueprint-400">
              Supports standard PDF blueprints, scanned layout images, and specification documents.
            </p>
          )}
        </div>
      </div>
      
      {errorMsg && (
        <div className="p-4 rounded-md border border-signal-red bg-signal-red/10 text-signal-red text-sm font-mono">
          {errorMsg}
        </div>
      )}
    </div>
  );
}