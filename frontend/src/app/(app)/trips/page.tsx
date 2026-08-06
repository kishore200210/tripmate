"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Plane, Calendar, MapPin, Loader2, Plus, Search, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useTrips, useCreateTrip, useDestinations } from "@/hooks/useDataAPI";
import { Pagination } from "@/components/shared/Pagination";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import toast from "react-hot-toast";
import type { TripStatus } from "@/types";

export default function TripsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [skip, setSkip] = useState(0);
  const limit = 6; // 6 items per page fits 3 columns beautifully

  // Dialog & Form States
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [destinationId, setDestinationId] = useState("");

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setSkip(0); // Reset pagination on new search
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const {
    data: tripsData,
    isLoading,
    isError,
    refetch,
  } = useTrips({
    q: debouncedSearch || undefined,
    status: statusFilter || undefined,
    skip,
    limit,
  });

  const { data: destinationsData } = useDestinations({ limit: 100 });
  const createTripMutation = useCreateTrip();

  const trips = tripsData?.items || [];
  const total = tripsData?.total || 0;
  const destinations = destinationsData?.items || [];

  // Auto-open and pre-select destination if passed via query params
  useEffect(() => {
    const destId = searchParams.get("destinationId");
    if (destId) {
      setDestinationId(destId);
      setIsOpen(true);
    }
  }, [searchParams]);

  const handleCreateTrip = (e: React.FormEvent) => {
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
      description: description.trim() || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      budget: budget ? parseFloat(budget) : undefined,
      destination_id: destinationId || undefined,
    };

    createTripMutation.mutate(payload, {
      onSuccess: (newTrip) => {
        toast.success("Trip planned successfully!");
        setIsOpen(false);
        // Reset form
        setTitle("");
        setDescription("");
        setStartDate("");
        setEndDate("");
        setBudget("");
        setDestinationId("");

        // Redirect to newly created trip detail page
        router.push(`/trips/${newTrip.id}`);
      },
      onError: (err: any) => {
        const detail = err.response?.data?.error?.message || err.response?.data?.detail;
        if (detail && typeof detail === "string") {
          toast.error(detail);
        } else {
          toast.error("Failed to plan trip");
        }
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

  const handleStatusTabClick = (status: string) => {
    setStatusFilter(status);
    setSkip(0);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">My Trips</h1>
          <p className="text-neutral-500">Manage your upcoming and past adventures.</p>
        </div>

        {/* Dialog for Planning a New Trip */}
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger render={
            <Button className="w-full sm:w-auto" aria-label="Plan New Trip">
              <Plus className="w-4 h-4 mr-2" aria-hidden="true" />
              Plan New Trip
            </Button>
          } />
          <DialogContent className="sm:max-w-[450px] bg-white text-neutral-950">
            <form onSubmit={handleCreateTrip}>
              <DialogHeader>
                <DialogTitle className="text-xl font-bold">Plan New Trip</DialogTitle>
                <DialogDescription className="text-neutral-500">
                  Enter the details for your next adventure.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
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
                <div className="grid gap-2">
                  <Label htmlFor="description" className="font-semibold text-neutral-800">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe your trip goals or plans..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="bg-white border-neutral-200 text-neutral-900 min-h-[80px]"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createTripMutation.isPending} className="w-full sm:w-auto" aria-label="Submit Create Trip">
                  {createTripMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                      Creating...
                    </>
                  ) : (
                    "Create Trip"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters & Search Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-4">
        {/* Tab Filters */}
        <div className="flex flex-wrap gap-1.5 bg-neutral-100 p-1 rounded-lg self-start">
          {[
            { label: "All Trips", value: "" },
            { label: "Planning", value: "planning" },
            { label: "Confirmed", value: "confirmed" },
            { label: "Ongoing", value: "ongoing" },
            { label: "Completed", value: "completed" },
            { label: "Cancelled", value: "cancelled" },
          ].map((tab) => (
              <button
              key={tab.value}
              onClick={() => handleStatusTabClick(tab.value)}
              aria-label={`Filter by status ${tab.label}`}
              aria-pressed={statusFilter === tab.value}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                statusFilter === tab.value
                  ? "bg-white text-neutral-900 shadow-xs"
                  : "text-neutral-500 hover:text-neutral-950"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:max-w-xs">
          <Search className="absolute left-3 top-2.5 h-4.5 w-4.5 text-neutral-400" />
          <Input
            placeholder="Search trips by title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white border-neutral-200 text-neutral-900 w-full"
          />
        </div>
      </div>

      {/* Trips Content */}
      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-10 w-10 animate-spin text-neutral-400" />
        </div>
      ) : isError ? (
        <ErrorState message="Failed to load trips. Please try again." onRetry={refetch} />
      ) : trips.length === 0 ? (
        <EmptyState
          icon={Plane}
          title={debouncedSearch || statusFilter ? "No matching trips found" : "No trips planned yet"}
          message={
            debouncedSearch || statusFilter
              ? "Try adjusting your search query or filters to find what you are looking for."
              : "Let's organize your next adventure. Create a trip to start planning your itinerary!"
          }
          action={
            !(debouncedSearch || statusFilter) ? (
              <Button onClick={() => setIsOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Plan a Trip
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm("");
                  setDebouncedSearch("");
                  setStatusFilter("");
                  setSkip(0);
                }}
              >
                Clear Filters
              </Button>
            )
          }
        />
      ) : (
        <div className="space-y-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip: any) => (
              <Card key={trip.id} className="overflow-hidden flex flex-col transition-all hover:shadow-md border border-neutral-200 bg-white">
                <div className="aspect-video relative overflow-hidden bg-neutral-200">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={trip.cover_image_url || "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&q=80&w=800"}
                    alt={trip.title}
                    className="object-cover w-full h-full transition-transform duration-300 hover:scale-105"
                  />
                  <div className="absolute top-3 right-3 shadow-md">
                    {getStatusBadge(trip.status)}
                  </div>
                </div>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <CardTitle className="text-lg font-bold text-neutral-900 line-clamp-1">{trip.title}</CardTitle>
                      <CardDescription className="flex items-center text-xs text-neutral-500 mt-0.5">
                        <MapPin className="w-3 h-3 mr-1 text-neutral-400" />
                        {trip.destination_id ? "Linked Destination" : "Custom Route"}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pb-4 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    <p className="text-sm text-neutral-500 line-clamp-2 min-h-[2.5rem]">
                      {trip.description || "No description provided."}
                    </p>
                    <div className="flex items-center text-xs font-semibold text-neutral-600 bg-neutral-50 p-2 rounded-md border border-neutral-100">
                      <Calendar className="w-3.5 h-3.5 mr-2 text-neutral-400" />
                      {trip.start_date ? new Date(trip.start_date).toLocaleDateString() : "Flexible"} - {trip.end_date ? new Date(trip.end_date).toLocaleDateString() : "Flexible"}
                    </div>
                  </div>
                </CardContent>
                <div className="border-t border-neutral-100 p-4 bg-neutral-50 flex gap-2">
                  <Link href={`/trips/${trip.id}`} className="flex-1">
                    <Button variant="outline" className="w-full font-semibold border-neutral-200">
                      Details
                    </Button>
                  </Link>
                  <Link href={`/trips/${trip.id}/itinerary`} className="flex-1">
                    <Button className="w-full font-semibold">
                      Itinerary
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          <Pagination skip={skip} limit={limit} total={total} onSkipChange={setSkip} />
        </div>
      )}
    </div>
  );
}
