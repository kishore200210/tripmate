"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Clock,
  Plane,
  FileText,
  Loader2,
  DollarSign,
  Edit2,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useTrip, useDestination, useDeleteTrip, useGenerateItinerary, useGeneratePDF } from "@/hooks/useDataAPI";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import type { TripStatus } from "@/types";

// Helper to compute duration in days
const getDuration = (start: string | null | undefined, end: string | null | undefined) => {
  if (!start || !end) return "Flexible Duration";
  const s = new Date(start);
  const e = new Date(end);
  const diffTime = Math.abs(e.getTime() - s.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  return `${diffDays} Day${diffDays > 1 ? "s" : ""}`;
};

export default function TripDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false);
  const [preferences, setPreferences] = useState("");

  const { data: trip, isLoading, isError } = useTrip(id);
  const { data: destination } = useDestination(trip?.destination_id || "");
  const deleteTripMutation = useDeleteTrip();
  const generateItineraryMutation = useGenerateItinerary(id);

  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const generatePdfMutation = useGeneratePDF(id);

  const handleGeneratePDF = async () => {
    if (isGeneratingPdf) return;
    setIsGeneratingPdf(true);
    const toastId = toast.loading("Preparing PDF itinerary background generation...");
    try {
      const res = await generatePdfMutation.mutateAsync();
      const taskId = res.task_id;

      toast.loading("PDF generation queued. Processing...", { id: toastId });

      const pollInterval = setInterval(async () => {
        try {
          const { data } = await api.get<{ status: string }>(`/pdf/status/${taskId}`);
          if (data.status === "SUCCESS") {
            clearInterval(pollInterval);
            toast.loading("PDF ready! Downloading...", { id: toastId });

            const response = await api.get(`/pdf/download/${taskId}`, { responseType: 'blob' });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `itinerary_${trip?.title?.replace(/\s+/g, '_') || 'trip'}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            setIsGeneratingPdf(false);
            toast.success("PDF downloaded successfully!", { id: toastId });
          } else if (data.status === "FAILURE") {
            clearInterval(pollInterval);
            setIsGeneratingPdf(false);
            toast.error("Failed to generate PDF itinerary.", { id: toastId });
          }
        } catch {
          clearInterval(pollInterval);
          setIsGeneratingPdf(false);
          toast.error("Error checking PDF generation status.", { id: toastId });
        }
      }, 1500);
    } catch (error: any) {
      setIsGeneratingPdf(false);
      const msg = error.response?.data?.error?.message || "Failed to trigger PDF generation.";
      toast.error(msg, { id: toastId });
    }
  };

  const handleGenerate = () => {
    generateItineraryMutation.mutate({ preferences }, {
      onSuccess: () => {
        toast.success("AI Itinerary generated successfully");
        setIsGenerateDialogOpen(false);
        router.push(`/trips/${id}/itinerary`);
      },
      onError: (err: any) => {
        const msg = err.response?.data?.error?.message || "Failed to generate itinerary";
        toast.error(msg);
      }
    });
  };

  const handleDelete = () => {
    deleteTripMutation.mutate(id, {
      onSuccess: () => {
        toast.success("Trip deleted successfully");
        setIsDeleteDialogOpen(false);
        router.push("/trips");
      },
      onError: (err: any) => {
        const msg = err.response?.data?.error?.message || "Failed to delete trip";
        toast.error(msg);
      },
    });
  };

  const getStatusBadge = (status: TripStatus) => {
    switch (status) {
      case "planning":
        return <Badge className="bg-neutral-100 text-neutral-800 hover:bg-neutral-200 border-neutral-300">Planning</Badge>;
      case "confirmed":
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200">Confirmed</Badge>;
      case "ongoing":
        return <Badge className="bg-green-50 text-green-700 hover:bg-green-100 border-green-200">Ongoing</Badge>;
      case "completed":
        return <Badge className="bg-teal-50 text-teal-700 hover:bg-teal-100 border-teal-200">Completed</Badge>;
      case "cancelled":
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-100 border-red-200">Cancelled</Badge>;
      default:
        return <Badge className="bg-neutral-100 text-neutral-800">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (isError || !trip) {
    return (
      <div className="text-center py-20 text-red-500">
        Failed to load trip details. Please try again.
      </div>
    );
  }

  const formattedStartDate = trip.start_date
    ? new Date(trip.start_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
    : "";
  const formattedEndDate = trip.end_date
    ? new Date(trip.end_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "";
  const dateRange = formattedStartDate && formattedEndDate
    ? `${formattedStartDate} - ${formattedEndDate}`
    : "Flexible Dates";

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Link href="/trips" className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Trips
      </Link>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-neutral-900">{trip.title}</h1>
            {getStatusBadge(trip.status)}
          </div>
          <p className="text-neutral-500 flex items-center mt-1">
            <MapPin className="w-4 h-4 mr-1 text-neutral-400" />
            {destination ? `${destination.name}, ${destination.country}` : "Custom Destination"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {/* Generate AI Itinerary Confirmation */}
          <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
            <DialogTrigger render={
              <Button className="bg-purple-600 hover:bg-purple-700 text-white">
                <FileText className="w-4 h-4 mr-2" />
                Generate AI Itinerary
              </Button>
            } />
            <DialogContent className="bg-white text-neutral-950">
              <DialogHeader>
                <DialogTitle className="text-xl font-bold text-neutral-900">Generate AI Itinerary</DialogTitle>
                <DialogDescription className="text-neutral-500 mt-2">
                  Our AI Concierge will generate a personalized day-by-day plan for your trip.
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
                <Button
                  variant="outline"
                  onClick={() => setIsGenerateDialogOpen(false)}
                  className="border-neutral-200"
                >
                  Cancel
                </Button>
                <Button
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                  onClick={handleGenerate}
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

          {/* View Itinerary */}
          <Link href={`/trips/${id}/itinerary`}>
            <Button>
              <Calendar className="w-4 h-4 mr-2" />
              View Itinerary
            </Button>
          </Link>

          {/* Edit Trip Button */}
          <Link href={`/trips/${id}/edit`}>
            <Button variant="outline" className="border-neutral-200">
              <Edit2 className="w-4 h-4 mr-2" />
              Edit
            </Button>
          </Link>

          {/* Delete Trip Confirmation */}
          <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
            <DialogTrigger render={
              <Button variant="destructive">
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            } />
            <DialogContent className="bg-white text-neutral-950">
              <DialogHeader>
                <DialogTitle className="text-xl font-bold text-neutral-900">Delete Trip</DialogTitle>
                <DialogDescription className="text-neutral-500 mt-2">
                  Are you sure you want to delete <span className="font-bold text-neutral-800">"{trip.title}"</span>? This will permanently delete the trip and all of its itinerary items. This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="mt-4">
                <Button
                  variant="outline"
                  onClick={() => setIsDeleteDialogOpen(false)}
                  className="border-neutral-200"
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={deleteTripMutation.isPending}
                >
                  {deleteTripMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    "Delete"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button
            variant="outline"
            onClick={handleGeneratePDF}
            disabled={isGeneratingPdf}
            className="border-neutral-200"
          >
            {isGeneratingPdf ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating PDF...
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 mr-2" />
                Generate PDF
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2 bg-white border border-neutral-200">
          <CardHeader>
            <CardTitle className="text-neutral-900">Trip Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-start gap-3">
                <div className="bg-blue-50 p-2 rounded-lg text-blue-600 border border-blue-100">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-900">Dates</p>
                  <p className="text-sm text-neutral-500">{dateRange}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="bg-purple-50 p-2 rounded-lg text-purple-600 border border-purple-100">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-900">Duration</p>
                  <p className="text-sm text-neutral-500">{getDuration(trip.start_date, trip.end_date)}</p>
                </div>
              </div>
              {trip.budget !== null && trip.budget !== undefined && (
                <div className="flex items-start gap-3 col-span-2 sm:col-span-1">
                  <div className="bg-green-50 p-2 rounded-lg text-green-600 border border-green-100">
                    <DollarSign className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-neutral-900">Budget</p>
                    <p className="text-sm text-neutral-500">${Number(trip.budget).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </div>

            <Separator className="bg-neutral-100" />

            <div>
              <h3 className="font-semibold text-neutral-800 mb-2">About this trip</h3>
              <p className="text-sm text-neutral-600 leading-relaxed whitespace-pre-wrap">
                {trip.description || "No description has been provided for this trip yet."}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Logistics Card — Kept visually identical as per requirement to preserve UI & styling */}
        <Card className="bg-white border border-neutral-200">
          <CardHeader>
            <CardTitle className="text-neutral-900">Logistics</CardTitle>
            <CardDescription className="text-neutral-500">Flight & Hotel Info</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold flex items-center text-neutral-800">
                <Plane className="w-4 h-4 mr-1 text-neutral-500" /> Outbound Flight
              </h4>
              <div className="text-sm border rounded-lg p-3 bg-neutral-50 border-neutral-100">
                <p className="font-medium text-neutral-400 italic">No flights added yet</p>
                <p className="text-xs text-neutral-500 mt-1">Bookings module integration required.</p>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-semibold flex items-center text-neutral-800">
                <MapPin className="w-4 h-4 mr-1 text-neutral-500" /> Accommodation
              </h4>
              <div className="text-sm border rounded-lg p-3 bg-neutral-50 border-neutral-100">
                <p className="font-medium text-neutral-400 italic">No lodging added yet</p>
                <p className="text-xs text-neutral-500 mt-1">Bookings module integration required.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
