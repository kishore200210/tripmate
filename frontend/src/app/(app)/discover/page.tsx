"use client";

import { useState, useRef } from "react";
import { Camera, Image as ImageIcon, Loader2, MapPin, UploadCloud, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { getSafeImageUrl } from "@/lib/imageUtils";

interface RelatedDestination {
  id: string;
  name: string;
  country: string;
  image_url: string | null;
}

interface CVResult {
  landmark: string;
  confidence: number;
  description: string;
  related_destinations: RelatedDestination[];
}

export default function DiscoverPage() {
  const router = useRouter();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CVResult | null>(null);
  const [error, setError] = useState("");
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError("");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("image/")) {
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(file));
        setResult(null);
        setError("");
      } else {
        setError("Please upload a valid image file (JPG, PNG).");
      }
    }
  };

  const analyzeImage = async () => {
    if (!selectedFile) return;
    
    setIsLoading(true);
    setError("");
    
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      
      const res = await fetch(`${API_URL}/computer-vision/analyze`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error("Failed to analyze image.");
      }
      
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Sorry, our vision model failed to process this image. Please try another.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <div className="bg-gradient-to-r from-teal-500 to-emerald-600 rounded-3xl p-8 text-white shadow-lg flex flex-col md:flex-row items-center gap-8">
        <div className="flex-1 space-y-4">
          <div className="inline-flex items-center gap-2 bg-white/20 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-sm">
            <Camera className="w-4 h-4 text-emerald-100" />
            Computer Vision
          </div>
          <h1 className="text-3xl font-bold">Discover From Photo</h1>
          <p className="text-teal-50 max-w-lg leading-relaxed">
            Upload a photo of a landmark, monument, or beautiful scenery. Our AI will identify it and suggest amazing TripMate destinations for you to visit.
          </p>
        </div>
        <div className="hidden md:block w-32 h-32 relative">
          <div className="absolute inset-0 bg-white/10 rounded-full animate-pulse" />
          <ImageIcon className="w-full h-full text-white/50 p-6" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Col: Upload Zone */}
        <div className="space-y-6">
          <h2 className="font-semibold text-xl text-neutral-800">Upload Image</h2>
          
          {!previewUrl ? (
            <div 
              className="border-2 border-dashed border-neutral-300 rounded-3xl bg-neutral-50 hover:bg-neutral-100 transition-colors cursor-pointer flex flex-col items-center justify-center p-12 text-center h-[400px]"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="w-16 h-16 text-neutral-400 mb-4" />
              <h3 className="text-lg font-medium text-neutral-800 mb-1">Click or drag image to upload</h3>
              <p className="text-sm text-neutral-500 max-w-xs">Supports JPG, PNG, JPEG up to 10MB.</p>
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept="image/jpeg, image/png, image/jpg" 
                onChange={handleFileSelect} 
              />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative w-full h-[400px] rounded-3xl overflow-hidden shadow-sm border bg-neutral-100">
                <Image src={previewUrl} alt="Preview" fill className="object-cover" />
              </div>
              <div className="flex gap-4">
                <Button variant="outline" className="flex-1" onClick={clearSelection} disabled={isLoading}>
                  Choose Another
                </Button>
                <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700" onClick={analyzeImage} disabled={isLoading || !!result}>
                  {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Camera className="w-4 h-4 mr-2" />}
                  {isLoading ? "Analyzing Image..." : "Analyze Image"}
                </Button>
              </div>
            </div>
          )}
          
          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100">
              {error}
            </div>
          )}
        </div>

        {/* Right Col: Results */}
        <div className="space-y-6">
          <h2 className="font-semibold text-xl text-neutral-800">Analysis Results</h2>
          
          {!result && !isLoading && (
            <div className="h-[400px] flex flex-col items-center justify-center text-center p-12 border-2 border-dashed rounded-3xl bg-neutral-50 text-neutral-400">
              <MapPin className="w-16 h-16 mb-4 text-neutral-300" />
              <h3 className="text-lg font-medium text-neutral-700 mb-2">Awaiting Image</h3>
              <p className="max-w-xs">Upload an image on the left to see what our vision model detects.</p>
            </div>
          )}
          
          {isLoading && !result && (
             <div className="h-[400px] flex flex-col items-center justify-center text-center p-12 rounded-3xl bg-white shadow-sm border">
               <Loader2 className="w-12 h-12 mb-4 text-emerald-600 animate-spin" />
               <h3 className="text-lg font-medium text-neutral-700 mb-2">Running Vision Model</h3>
               <p className="text-neutral-500 text-sm max-w-xs">Our YOLO model is classifying the landmarks and objects in your photo...</p>
             </div>
          )}

          {result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="bg-white border rounded-2xl p-6 shadow-sm space-y-4">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 uppercase tracking-wider mb-1">Detected Object</p>
                    <h3 className="text-2xl font-bold text-neutral-900">{result.landmark}</h3>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-sm font-medium text-neutral-500 mb-1">Confidence</span>
                    <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full font-bold">
                      {result.confidence}%
                    </div>
                  </div>
                </div>
                
                <p className="text-neutral-700 leading-relaxed pt-2 border-t">
                  {result.description}
                </p>
              </div>
              
              {result.related_destinations.length > 0 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg text-neutral-800">Suggested Destinations</h3>
                  <div className="grid gap-3">
                    {result.related_destinations.map((dest) => (
                      <div key={dest.id} className="bg-white border rounded-xl p-3 shadow-sm flex items-center justify-between group hover:border-emerald-200 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-neutral-100 flex-shrink-0">
                           {getSafeImageUrl(dest.image_url) !== "/globe.svg" ? (
                              <Image src={getSafeImageUrl(dest.image_url)} alt={dest.name} fill className="object-cover" />
                            ) : (
                              <div className="absolute inset-0 flex items-center justify-center bg-blue-50 text-blue-200">
                                <Plane className="w-5 h-5" />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-bold text-neutral-900">{dest.name}</p>
                            <p className="text-sm text-neutral-500">{dest.country}</p>
                          </div>
                        </div>
                        <Button 
                          onClick={() => router.push(`/trips/new?destination_id=${dest.id}`)}
                          size="sm" 
                          variant="secondary"
                          className="group-hover:bg-emerald-600 group-hover:text-white transition-colors"
                        >
                          Plan Trip
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
