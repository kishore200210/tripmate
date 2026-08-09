"use client";

import { useState } from "react";
import { Sparkles, Map, Loader2, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import Link from "next/link";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { getSafeImageUrl } from "@/lib/imageUtils";

interface RecommendedDestination {
  id: string | null;
  name: string;
  country: string;
  image_url: string | null;
  confidence_score: number;
  reason: string;
}

export default function RecommendationsPage() {
  const router = useRouter();
  
  const [budget, setBudget] = useState("100");
  const [duration, setDuration] = useState("7");
  const [climate, setClimate] = useState("Tropical");
  const [travelStyle, setTravelStyle] = useState("Relaxation");
  const [season, setSeason] = useState("Summer");
  const [familyFriendly, setFamilyFriendly] = useState("5");
  const [adventure, setAdventure] = useState("5");
  const [luxury, setLuxury] = useState("5");
  
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<RecommendedDestination[] | null>(null);
  const [error, setError] = useState("");

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      
      const res = await fetch(`${API_URL}/recommendations/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          budget: parseFloat(budget),
          duration: parseInt(duration, 10),
          climate,
          travel_style: travelStyle,
          season,
          family_friendly: parseInt(familyFriendly, 10),
          adventure: parseInt(adventure, 10),
          luxury: parseInt(luxury, 10)
        }),
      });
      
      if (!res.ok) throw new Error("Failed to get recommendations");
      const data = await res.json();
      setResults(data.recommendations);
    } catch {
      setError("Sorry, there was an error generating your recommendations.");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlanTrip = (destId: string | null, name: string) => {
    if (destId) {
      router.push(`/trips/new?destination_id=${destId}`);
    } else {
      router.push(`/trips/new?destination_name=${encodeURIComponent(name)}`);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-3xl p-8 text-white shadow-lg flex flex-col md:flex-row items-center gap-8">
        <div className="flex-1 space-y-4">
          <div className="inline-flex items-center gap-2 bg-white/20 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-sm">
            <Sparkles className="w-4 h-4 text-yellow-300" />
            Machine Learning Engine
          </div>
          <h1 className="text-3xl font-bold">Recommended For You</h1>
          <p className="text-purple-100 max-w-lg leading-relaxed">
            Tell us about your perfect trip, and our AI model will match you with the top 5 destinations worldwide based on millions of data points.
          </p>
        </div>
        <div className="hidden md:block w-32 h-32 relative">
          <div className="absolute inset-0 bg-white/10 rounded-full animate-pulse" />
          <Map className="w-full h-full text-white/50 p-6" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Col: Form */}
        <div className="md:col-span-4 bg-white border rounded-2xl p-6 shadow-sm h-fit sticky top-24">
          <h2 className="font-semibold text-lg mb-6 border-b pb-4">Your Preferences</h2>
          <form onSubmit={handlePredict} className="space-y-5">
            <div className="space-y-2">
              <Label>Budget Per Day ($)</Label>
              <Input type="number" min="10" value={budget} onChange={(e) => setBudget(e.target.value)} required />
            </div>
            
            <div className="space-y-2">
              <Label>Duration (Days)</Label>
              <Input type="number" min="1" value={duration} onChange={(e) => setDuration(e.target.value)} required />
            </div>

            <div className="space-y-2">
              <Label>Preferred Climate</Label>
              <select 
                value={climate} 
                onChange={(e) => setClimate(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="Tropical">Tropical</option>
                <option value="Temperate">Temperate</option>
                <option value="Mediterranean">Mediterranean</option>
                <option value="Cold">Cold</option>
                <option value="Arid">Arid</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <Label>Travel Style</Label>
              <select 
                value={travelStyle} 
                onChange={(e) => setTravelStyle(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="Relaxation">Relaxation</option>
                <option value="Adventure">Adventure</option>
                <option value="Cultural">Cultural</option>
                <option value="City">City Break</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <Label>Season</Label>
              <select 
                value={season} 
                onChange={(e) => setSeason(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="Summer">Summer</option>
                <option value="Winter">Winter</option>
                <option value="Spring">Spring</option>
                <option value="Fall">Fall</option>
              </select>
            </div>
            
            <div className="pt-2 border-t space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Family Friendly</Label>
                  <span className="text-xs text-neutral-500 font-medium">{familyFriendly}/10</span>
                </div>
                <input type="range" min="1" max="10" step="1" value={familyFriendly} onChange={(e) => setFamilyFriendly(e.target.value)} className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-purple-600" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Adventure Intensity</Label>
                  <span className="text-xs text-neutral-500 font-medium">{adventure}/10</span>
                </div>
                <input type="range" min="1" max="10" step="1" value={adventure} onChange={(e) => setAdventure(e.target.value)} className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-purple-600" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Luxury Level</Label>
                  <span className="text-xs text-neutral-500 font-medium">{luxury}/10</span>
                </div>
                <input type="range" min="1" max="10" step="1" value={luxury} onChange={(e) => setLuxury(e.target.value)} className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-purple-600" />
              </div>
            </div>

            <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 h-11" disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
              {isLoading ? "Analyzing..." : "Get Recommendations"}
            </Button>
          </form>
        </div>

        {/* Right Col: Results */}
        <div className="md:col-span-8 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100">
              {error}
            </div>
          )}
          
          {!results && !isLoading && (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-center p-12 border-2 border-dashed rounded-3xl bg-neutral-50 text-neutral-400">
              <Map className="w-16 h-16 mb-4 text-neutral-300" />
              <h3 className="text-lg font-medium text-neutral-700 mb-2">Awaiting Preferences</h3>
              <p className="max-w-xs">Fill out the form on the left to see your personalized AI destination matches.</p>
            </div>
          )}
          
          {isLoading && !results && (
             <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-center p-12 rounded-3xl bg-white shadow-sm border">
               <Loader2 className="w-12 h-12 mb-4 text-purple-600 animate-spin" />
               <h3 className="text-lg font-medium text-neutral-700 mb-2">Running ML Inference</h3>
               <p className="text-neutral-500 text-sm max-w-xs">Our Random Forest model is analyzing thousands of vectors to find your perfect trip...</p>
             </div>
          )}

          {results && (
            <div className="space-y-6">
              <h2 className="font-semibold text-xl text-neutral-800 flex items-center gap-2">
                Top 5 Matches
              </h2>
              <div className="grid gap-4">
                {results.map((dest, idx) => (
                  <div key={idx} className="bg-white border rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col sm:flex-row gap-5 items-start">
                    
                    <div className="relative w-full sm:w-40 h-40 rounded-xl overflow-hidden bg-neutral-100 flex-shrink-0">
                      <Image src={getSafeImageUrl(dest.image_url)} alt={dest.name} fill className="object-cover" />
                      <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-lg shadow-sm border font-bold text-sm text-purple-700 flex items-center gap-1">
                         #{idx + 1}
                      </div>
                    </div>
                    
                    <div className="flex-1 space-y-3 min-w-0 w-full">
                      <div className="flex flex-col sm:flex-row justify-between items-start gap-2">
                        <div>
                          <h3 className="text-xl font-bold text-neutral-900 truncate">{dest.name}</h3>
                          <p className="text-neutral-500 font-medium">{dest.country}</p>
                        </div>
                        <div className="flex items-center gap-2 bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-full whitespace-nowrap">
                          <Sparkles className="w-4 h-4" />
                          <span className="font-bold text-sm">{dest.confidence_score}% Match</span>
                        </div>
                      </div>
                      
                      <div className="bg-neutral-50 p-3 rounded-lg border text-sm text-neutral-700 leading-relaxed">
                        <span className="font-semibold text-neutral-900 mr-2">Why this fits:</span>
                        {dest.reason}
                      </div>
                      
                      <div className="flex justify-end pt-2">
                         <Button 
                           onClick={() => handlePlanTrip(dest.id, dest.name)}
                           className="bg-neutral-900 hover:bg-neutral-800 rounded-full px-6"
                         >
                           Plan Trip to {dest.name}
                         </Button>
                      </div>
                    </div>
                    
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
