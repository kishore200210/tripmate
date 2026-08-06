"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Save, Calendar, DollarSign, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useTrip, useDestinations, useUpdateTrip } from "@/hooks/useDataAPI";
import toast from "react-hot-toast";
import type { TripStatus } from "@/types";

export default function EditTripPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);

  // Fetch current data
  const { data: trip, isLoading: isTripLoading, isError: isTripError } = useTrip(id);
  const { data: destinationsData } = useDestinations({ limit: 100 });
  const updateTripMutation = useUpdateTrip(id);

  // Form States
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [status, setStatus] = useState<TripStatus>("planning");
  const [destinationId, setDestinationId] = useState("");

  const destinations = destinationsData?.items || [];

  // Populate form fields when data is loaded
  useEffect(() => {
    if (trip) {
      setTitle(trip.title);
      setDescription(trip.description || "");
      setStartDate(trip.start_date || "");
      setEndDate(trip.end_date || "");
      setBudget(trip.budget !== null && trip.budget !== undefined ? String(trip.budget) : "");
      setStatus(trip.status);
      setDestinationId(trip.destination_id || "");
    }
  }, [trip]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error("Trip title is required");
      return;
    }

    // Validation for dates if both are provided
    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      toast.error("Start date cannot be after end date");
      return;
    }

    const payload = {
      title: title.trim(),
      description: description.trim() || "",
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      budget: budget ? parseFloat(budget) : undefined,
      status: status,
      destination_id: destinationId || undefined,
    };

    updateTripMutation.mutate(payload, {
      onSuccess: () => {
        toast.success("Trip updated successfully!");
        router.push(`/trips/${id}`);
      },
      onError: (err: any) => {
        const detail = err.response?.data?.error?.message || err.response?.data?.detail;
        if (detail && typeof detail === "string") {
          toast.error(detail);
        } else {
          toast.error("Failed to update trip");
        }
      },
    });
  };

  if (isTripLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (isTripError || !trip) {
    return (
      <div className="text-center py-20 text-red-500">
        Failed to load trip. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <Link href={`/trips/${id}`} className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Trip Details
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Edit Trip</h1>
          <p className="text-neutral-500">Modify your trip details and update status.</p>
        </div>
      </div>

      <Card className="bg-white border border-neutral-200 shadow-xs">
        <CardHeader>
          <CardTitle className="text-neutral-900">Trip Details</CardTitle>
          <CardDescription className="text-neutral-500">Fill in the fields to adjust your itinerary settings.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Title */}
            <div className="grid gap-2">
              <Label htmlFor="title" className="font-semibold text-neutral-800">Trip Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Paris Getaway"
                required
                className="bg-white border-neutral-200 text-neutral-900 focus:ring-blue-500"
              />
            </div>

            {/* Destination Selector */}
            <div className="grid gap-2">
              <Label htmlFor="destination" className="font-semibold text-neutral-800">Destination</Label>
              <select
                id="destination"
                value={destinationId}
                onChange={(e) => setDestinationId(e.target.value)}
                className="flex h-9 w-full rounded-md border border-neutral-200 bg-white px-3 py-1 text-sm shadow-xs transition-colors focus:outline-hidden focus:ring-1 focus:ring-blue-500 text-neutral-900"
              >
                <option value="">Select a Destination (Optional)</option>
                {destinations.map((d: any) => (
                  <option key={d.id} value={d.id}>
                    {d.name}, {d.country}
                  </option>
                ))}
              </select>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="start_date" className="font-semibold text-neutral-800">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-white border-neutral-200 text-neutral-900"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="end_date" className="font-semibold text-neutral-800">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="bg-white border-neutral-200 text-neutral-900"
                />
              </div>
            </div>

            {/* Budget & Status */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Budget */}
              <div className="grid gap-2">
                <Label htmlFor="budget" className="font-semibold text-neutral-800">Budget ($)</Label>
                <div className="relative">
                  <DollarSign className="absolute left-2.5 top-2.5 h-4 w-4 text-neutral-400" />
                  <Input
                    id="budget"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="e.g., 1500"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    className="pl-8 bg-white border-neutral-200 text-neutral-900"
                  />
                </div>
              </div>

              {/* Status */}
              <div className="grid gap-2">
                <Label htmlFor="status" className="font-semibold text-neutral-800">Status</Label>
                <select
                  id="status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as TripStatus)}
                  className="flex h-9 w-full rounded-md border border-neutral-200 bg-white px-3 py-1 text-sm shadow-xs transition-colors focus:outline-hidden focus:ring-1 focus:ring-blue-500 text-neutral-900"
                >
                  <option value="planning">Planning</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>

            {/* Description/Notes */}
            <div className="grid gap-2">
              <Label htmlFor="description" className="font-semibold text-neutral-800">Notes / Description</Label>
              <Textarea
                id="description"
                placeholder="Describe your trip goals or plans..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="bg-white border-neutral-200 text-neutral-900 min-h-[100px]"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-4 border-t border-neutral-100">
              <Link href={`/trips/${id}`}>
                <Button variant="outline" type="button" className="border-neutral-200">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={updateTripMutation.isPending}>
                {updateTripMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
