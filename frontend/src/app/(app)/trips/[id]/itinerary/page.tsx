"use client";

import { use, useState, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  MapPin,
  Clock,
  Loader2,
  CalendarDays,
  CloudRain,
  Utensils,
  CheckSquare,
  Sparkles,
  Navigation,
  RefreshCw,
  FileText
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  useItinerary,
  useTrip,
  useAIItineraryDetails,
  useRegenerateDayPlan,
  useGenerateItinerary
} from "@/hooks/useDataAPI";
import toast from "react-hot-toast";

// ── Types ───────────────────────────────────────────────────────────────────

interface ItineraryItem {
  id: string;
  trip_id: string;
  day_no: number;
  activity: string;
  scheduled_time: string | null;
  notes: string | null;
  location: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTime(timeStr: string | null): string {
  if (!timeStr) return "—";
  const [hoursStr, minutesStr] = timeStr.split(":");
  const hours = parseInt(hoursStr, 10);
  const minutes = parseInt(minutesStr, 10);
  const period = hours >= 12 ? "PM" : "AM";
  const h = hours % 12 || 12;
  const m = String(minutes).padStart(2, "0");
  return `${h}:${m} ${period}`;
}

function getDayDate(startDate: string | null | undefined, dayNo: number): string {
  if (!startDate) return "";
  const date = new Date(startDate);
  date.setDate(date.getDate() + dayNo - 1);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ItineraryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const { data: timeline, isLoading: isTimelineLoading, isError: isTimelineError } = useItinerary(id);
  const { data: trip } = useTrip(id);
  const { data: aiDetails, isLoading: isAiDetailsLoading } = useAIItineraryDetails(id);
  
  const generateItineraryMutation = useGenerateItinerary(id);
  const regenerateDayMutation = useRegenerateDayPlan(id, 0); // we will pass dynamic day in mutate

  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false);
  const [preferences, setPreferences] = useState("");
  const [activeRegenerateDay, setActiveRegenerateDay] = useState<number | null>(null);

  const isLoading = isTimelineLoading || isAiDetailsLoading;

  const grouped = useMemo(() => {
    return (timeline?.items ?? []).reduce(
      (acc: Record<number, ItineraryItem[]>, item: ItineraryItem) => {
        if (!acc[item.day_no]) acc[item.day_no] = [];
        acc[item.day_no].push(item);
        return acc;
      },
      {}
    );
  }, [timeline?.items]);
  
  // Create an array of days based on grouped items or aiDetails day_plans
  const days = useMemo(() => {
    const dayPlansSet = new Set<number>();
    Object.keys(grouped).forEach(k => dayPlansSet.add(Number(k)));
    (aiDetails?.day_plans || []).forEach((dp: any) => dayPlansSet.add(dp.day_no));
    return Array.from(dayPlansSet).sort((a, b) => a - b);
  }, [grouped, aiDetails?.day_plans]);

  const handleGenerateFull = () => {
    generateItineraryMutation.mutate({ preferences }, {
      onSuccess: () => {
        toast.success("AI Itinerary generated successfully!");
        setIsGenerateDialogOpen(false);
        setPreferences("");
      },
      onError: (err: any) => {
        const msg = err.response?.data?.error?.message || "Failed to generate itinerary";
        toast.error(msg);
      }
    });
  };

  const handleRegenerateDay = (dayNo: number) => {
    regenerateDayMutation.mutateAsync({ preferences }).then(() => {
        toast.success(`Day ${dayNo} regenerated successfully!`);
        setActiveRegenerateDay(null);
        setPreferences("");
    }).catch((err: any) => {
        const msg = err.response?.data?.error?.message || `Failed to regenerate Day ${dayNo}`;
        toast.error(msg);
    });
  };

  // Helper to safely parse JSON strings returned from backend if needed
  const safeParseList = (val: string | null): string[] => {
    if (!val) return [];
    try {
      const parsed = JSON.parse(val);
      if (Array.isArray(parsed)) return parsed;
      return [val];
    } catch {
      return [val];
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between sm:items-end gap-4">
        <div>
          <Link
            href={`/trips/${id}`}
            className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Trip Overview
          </Link>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">
            {trip?.title ? `Itinerary: ${trip.title}` : "Itinerary"}
          </h1>
          <p className="text-neutral-500 mt-1">Detailed day-by-day AI schedule.</p>
        </div>
        
        {/* Generate / Regenerate Action */}
        <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
          <DialogTrigger render={
            <Button className="bg-purple-600 hover:bg-purple-700 text-white">
              <Sparkles className="w-4 h-4 mr-2" />
              {aiDetails ? "Regenerate Full Itinerary" : "Generate AI Itinerary"}
            </Button>
          } />
          <DialogContent className="bg-white text-neutral-950">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-neutral-900">
                {aiDetails ? "Regenerate AI Itinerary" : "Generate AI Itinerary"}
              </DialogTitle>
              <DialogDescription className="text-neutral-500 mt-2">
                Our AI Concierge will generate a personalized day-by-day plan for your trip.
                {aiDetails && " This will overwrite your current itinerary items."}
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4">
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Preferences (Optional)
              </label>
              <textarea
                className="w-full border border-neutral-300 rounded-md p-2 text-sm focus:ring-purple-500 focus:border-purple-500"
                rows={3}
                placeholder="e.g., Relaxing, Adventure, Vegetarian food only"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
              />
            </div>
            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setIsGenerateDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                className="bg-purple-600 hover:bg-purple-700 text-white"
                onClick={handleGenerateFull}
                disabled={generateItineraryMutation.isPending}
              >
                {generateItineraryMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading && (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
        </div>
      )}

      {isTimelineError && !isLoading && (
        <div className="text-center py-20 text-red-500">
          Failed to load itinerary. Please try again.
        </div>
      )}

      {!isLoading && !isTimelineError && days.length === 0 && (
        <div className="flex flex-col items-center py-20 text-center text-neutral-500">
          <Sparkles className="w-12 h-12 text-purple-300 mb-4" />
          <p className="font-medium text-neutral-700">No itinerary generated yet.</p>
          <p className="text-sm mt-1 mb-4">
            Let our AI Concierge plan the perfect trip for you.
          </p>
          <Button onClick={() => setIsGenerateDialogOpen(true)} className="bg-purple-600 hover:bg-purple-700 text-white">
            Generate Now
          </Button>
        </div>
      )}

      {!isLoading && aiDetails && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {aiDetails.weather_suggestions && (
            <Card className="bg-sky-50 border-sky-100">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2 text-sky-700 font-semibold">
                  <CloudRain className="w-4 h-4" /> Weather
                </div>
                <p className="text-sm text-sky-900">{aiDetails.weather_suggestions}</p>
              </CardContent>
            </Card>
          )}
          {aiDetails.packing_checklist && (
            <Card className="bg-green-50 border-green-100">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2 text-green-700 font-semibold">
                  <CheckSquare className="w-4 h-4" /> Packing
                </div>
                <ul className="text-sm text-green-900 list-disc list-inside space-y-1">
                  {safeParseList(aiDetails.packing_checklist).slice(0, 4).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
          {aiDetails.restaurant_recommendations && (
            <Card className="bg-orange-50 border-orange-100">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2 text-orange-700 font-semibold">
                  <Utensils className="w-4 h-4" /> Restaurants
                </div>
                <ul className="text-sm text-orange-900 list-disc list-inside space-y-1">
                  {safeParseList(aiDetails.restaurant_recommendations).slice(0, 4).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
          {aiDetails.local_attractions && (
            <Card className="bg-purple-50 border-purple-100">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2 text-purple-700 font-semibold">
                  <Navigation className="w-4 h-4" /> Attractions
                </div>
                <ul className="text-sm text-purple-900 list-disc list-inside space-y-1">
                  {safeParseList(aiDetails.local_attractions).slice(0, 4).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {!isLoading && !isTimelineError && days.length > 0 && (
        <div className="space-y-10">
          {days.map((dayNo) => {
            const dayPlan = aiDetails?.day_plans?.find((dp: any) => dp.day_no === dayNo);
            const items = grouped[dayNo] || [];

            return (
              <div key={dayNo} className="relative pl-8 md:pl-0">
                <div className="md:grid md:grid-cols-12 gap-8">
                  {/* Day Overview Column */}
                  <div className="md:col-span-4 pb-6 md:pb-0 relative">
                    <div className="hidden md:block absolute right-0 top-0 bottom-0 w-px bg-neutral-200" />
                    <div className="flex items-center justify-between mb-2">
                        <div>
                            <h3 className="text-2xl font-bold text-neutral-900">
                            Day {dayNo}
                            </h3>
                            <p className="text-sm text-neutral-500 font-medium mt-1">
                            {getDayDate(trip?.start_date, dayNo)}
                            </p>
                        </div>
                        {aiDetails && (
                            <Dialog 
                                open={activeRegenerateDay === dayNo} 
                                onOpenChange={(open) => {
                                    if(open) setActiveRegenerateDay(dayNo);
                                    else setActiveRegenerateDay(null);
                                }}
                            >
                                <DialogTrigger render={
                                    <Button variant="ghost" size="sm" className="text-purple-600 hover:text-purple-700 hover:bg-purple-50">
                                        <RefreshCw className="w-4 h-4 mr-2" />
                                        Regenerate
                                    </Button>
                                } />
                                <DialogContent className="bg-white text-neutral-950">
                                    <DialogHeader>
                                        <DialogTitle>Regenerate Day {dayNo}</DialogTitle>
                                        <DialogDescription>
                                            Adjust your preferences to get a new plan for this day.
                                        </DialogDescription>
                                    </DialogHeader>
                                    <div className="mt-4">
                                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                                            Preferences (Optional)
                                        </label>
                                        <textarea
                                            className="w-full border border-neutral-300 rounded-md p-2 text-sm focus:ring-purple-500 focus:border-purple-500"
                                            rows={3}
                                            placeholder="e.g., Want a late start, focus on shopping"
                                            value={preferences}
                                            onChange={(e) => setPreferences(e.target.value)}
                                        />
                                    </div>
                                    <DialogFooter className="mt-4">
                                        <Button variant="outline" onClick={() => setActiveRegenerateDay(null)}>
                                            Cancel
                                        </Button>
                                        <Button
                                            className="bg-purple-600 hover:bg-purple-700 text-white"
                                            onClick={() => handleRegenerateDay(dayNo)}
                                            disabled={regenerateDayMutation.isPending}
                                        >
                                            {regenerateDayMutation.isPending ? (
                                                <><Loader2 className="mr-2 w-4 h-4 animate-spin" /> Regenerating...</>
                                            ) : (
                                                "Regenerate"
                                            )}
                                        </Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        )}
                    </div>
                    {dayPlan && (
                      <div className="mt-4 p-4 rounded-xl bg-purple-50/50 border border-purple-100/50">
                        <h4 className="font-semibold text-purple-900 mb-2">{dayPlan.theme}</h4>
                        <p className="text-sm text-purple-800/80 leading-relaxed">
                          {dayPlan.description}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Activity List Column */}
                  <div className="md:col-span-8 space-y-4">
                    {items.length === 0 ? (
                        <div className="p-6 border border-dashed border-neutral-200 rounded-xl text-center text-neutral-500 text-sm">
                            No activities planned for this day.
                        </div>
                    ) : items.map((item: ItineraryItem) => (
                      <Card
                        key={item.id}
                        className="border-l-4 border-l-purple-500 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <CardContent className="p-4 flex flex-col sm:flex-row gap-4 sm:items-center">
                          <div className="sm:w-32 flex-shrink-0 flex items-center text-sm font-semibold text-neutral-700">
                            <Clock className="w-4 h-4 mr-1.5 text-neutral-400" />
                            {formatTime(item.scheduled_time)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-base text-neutral-900">
                                {item.activity}
                              </h4>
                              {item.notes && (
                                <Badge
                                  variant="outline"
                                  className="text-[10px] uppercase tracking-wider py-0 font-medium max-w-[150px] truncate"
                                >
                                  {item.notes}
                                </Badge>
                              )}
                            </div>
                            {item.location && (
                              <div className="flex items-center text-sm text-neutral-500 mt-2">
                                <MapPin className="w-3.5 h-3.5 mr-1" />
                                {item.location}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
