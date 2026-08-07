"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Plane,
  Calendar,
  MapPin,
  Loader2,
  Plus,
  Search,
  DollarSign,
  AlertCircle,
} from "lucide-react";
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
import { PlaceAutocomplete } from "@/components/shared/PlaceAutocomplete";
import { useTrips, useCreateTrip } from "@/hooks/useDataAPI";
import { Pagination } from "@/components/shared/Pagination";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import toast from "react-hot-toast";
import type { PlaceResult, TripStatus } from "@/types";

// ── Error message mapper ───────────────────────────────────────────────────────
function getErrorMessage(err: any): string {
  // Try structured backend error first
  const backendMsg =
    err?.response?.data?.error?.message ||
    (typeof err?.response?.data?.detail === "string"
      ? err.response.data.detail
      : null);

  if (backendMsg && typeof backendMsg === "string") {
    return backendMsg;
  }

  const status: number | undefined = err?.response?.status;
  switch (status) {
    case 400:
      return "Invalid request. Please check your inputs and try again.";
    case 401:
      return "Your session has expired. Please log in again.";
    case 403:
      return "You don't have permission to perform this action.";
    case 404:
      return "Trip service unavailable. Please try again later.";
    case 422:
      return "Please correct the highlighted fields and try again.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 500:
    case 502:
    case 503:
      return "Something went wrong on the server. Please try again.";
    default:
      if (!err?.response) {
        return "Unable to reach the server. Please check your connection.";
      }
      return "Failed to create trip. Please try again.";
  }
}

// ── Inline field error component ───────────────────────────────────────────────
function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="flex items-center gap-1 text-xs text-red-600 mt-1">
      <AlertCircle className="h-3 w-3 shrink-0" aria-hidden="true" />
      {message}
    </p>
  );
}

// ── Status badge ───────────────────────────────────────────────────────────────
function getStatusBadge(status: TripStatus) {
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
}

// ── Form field validation errors type ─────────────────────────────────────────
interface FormErrors {
  title?: string;
  startDate?: string;
  endDate?: string;
  budget?: string;
}

// ── Page component ─────────────────────────────────────────────────────────────
export default function TripsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [skip, setSkip] = useState(0);
  const limit = 6;

  // Dialog & Form States
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setSkip(0);
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

  const createTripMutation = useCreateTrip();

  const trips = tripsData?.items || [];
  const total = tripsData?.total || 0;

  // Auto-open and pre-select destination if passed via query params
  useEffect(() => {
    const destId = searchParams.get("destinationId");
    const plan = searchParams.get("plan");
    const placeName = searchParams.get("place_name");
    const placeCountry = searchParams.get("place_country");

    if (destId) {
      setIsOpen(true);
    } else if (plan === "true" || placeName) {
      if (placeName) {
        setSelectedPlace({
          place_id: "query_param",
          name: placeName,
          display_name: placeCountry ? `${placeName}, ${placeCountry}` : placeName,
          city: null,
          state: null,
          country: placeCountry || null,
          country_code: null,
          place_type: "City",
          latitude: null,
          longitude: null,
        });
        setTitle(`Trip to ${placeName}`);
      }
      setIsOpen(true);
    }
  }, [searchParams]);

  // ── Form reset helper ────────────────────────────────────────────────────────
  const resetForm = () => {
    setTitle("");
    setDescription("");
    setStartDate("");
    setEndDate("");
    setBudget("");
    setSelectedPlace(null);
    setFormErrors({});
  };

  const handleDialogChange = (open: boolean) => {
    setIsOpen(open);
    if (!open) resetForm();
  };

  // ── Client-side validation ───────────────────────────────────────────────────
  const validate = (): boolean => {
    const errors: FormErrors = {};

    if (!title.trim()) {
      errors.title = "Trip title is required.";
    } else if (title.trim().length < 2) {
      errors.title = "Title must be at least 2 characters.";
    }

    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      errors.endDate = "End date must be after the start date.";
    }

    if (budget) {
      const b = parseFloat(budget);
      if (isNaN(b) || b < 0) {
        errors.budget = "Budget must be a positive number.";
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // ── Submit handler ───────────────────────────────────────────────────────────
  const handleCreateTrip = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const payload = {
      title: title.trim(),
      description: description.trim() || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      budget: budget ? parseFloat(budget) : undefined,
      // Geocoded place fields — no destination_id for Nominatim results
      destination_id: undefined,
      place_name: selectedPlace?.name || undefined,
      place_country: selectedPlace?.country || undefined,
    };

    createTripMutation.mutate(payload, {
      onSuccess: (newTrip) => {
        toast.success("Trip created successfully! ✈️");
        setIsOpen(false);
        resetForm();
        router.push(`/trips/${newTrip.id}`);
      },
      onError: (err: any) => {
        toast.error(getErrorMessage(err));
      },
    });
  };

  // ── Status tabs ──────────────────────────────────────────────────────────────
  const handleStatusTabClick = (status: string) => {
    setStatusFilter(status);
    setSkip(0);
  };

  const today = new Date().toISOString().split("T")[0];

  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">My Trips</h1>
          <p className="text-neutral-500">Manage your upcoming and past adventures.</p>
        </div>

        {/* Plan New Trip Dialog */}
        <Dialog open={isOpen} onOpenChange={handleDialogChange}>
          <DialogTrigger render={
            <Button className="w-full sm:w-auto" aria-label="Plan New Trip">
              <Plus className="w-4 h-4 mr-2" aria-hidden="true" />
              Plan New Trip
            </Button>
          } />

          <DialogContent className="sm:max-w-[620px] bg-white text-neutral-950 p-0 overflow-hidden">
            <form onSubmit={handleCreateTrip} noValidate>
              {/* Dialog header with accent bar */}
              <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-5">
                <DialogHeader>
                  <DialogTitle className="text-xl font-bold text-white flex items-center gap-2">
                    <Plane className="w-5 h-5" aria-hidden="true" />
                    Plan New Trip
                  </DialogTitle>
                  <DialogDescription className="text-blue-100 text-sm">
                    Fill in the details below to start planning your next adventure.
                  </DialogDescription>
                </DialogHeader>
              </div>

              {/* Form body */}
              <div className="px-6 py-5 space-y-5">

                {/* Trip Title */}
                <div className="space-y-1.5">
                  <Label
                    htmlFor="trip-title"
                    className="text-sm font-semibold text-neutral-800"
                  >
                    Trip Title <span className="text-red-500" aria-hidden="true">*</span>
                  </Label>
                  <Input
                    id="trip-title"
                    value={title}
                    onChange={(e) => {
                      setTitle(e.target.value);
                      if (formErrors.title) setFormErrors((p) => ({ ...p, title: undefined }));
                    }}
                    placeholder="e.g., Summer in Paris, Monsoon Kerala…"
                    required
                    aria-required="true"
                    aria-invalid={!!formErrors.title}
                    aria-describedby={formErrors.title ? "title-error" : undefined}
                    className={`bg-white border-neutral-200 text-neutral-900 focus-visible:ring-blue-500 ${
                      formErrors.title ? "border-red-400 focus-visible:ring-red-400" : ""
                    }`}
                  />
                  <FieldError message={formErrors.title} />
                </div>

                {/* Destination */}
                <div className="space-y-1.5">
                  <Label
                    htmlFor="trip-destination"
                    className="text-sm font-semibold text-neutral-800 flex items-center gap-1.5"
                  >
                    <MapPin className="w-3.5 h-3.5 text-neutral-500" aria-hidden="true" />
                    Destination
                    <span className="text-xs font-normal text-neutral-400 ml-1">(optional)</span>
                  </Label>
                  <PlaceAutocomplete
                    id="trip-destination"
                    value={selectedPlace}
                    onChange={setSelectedPlace}
                    placeholder="Search any city, country or region…"
                    aria-label="Search destination"
                  />
                  <p className="text-[11px] text-neutral-400">
                    Powered by OpenStreetMap — search any place in the world.
                  </p>
                </div>

                {/* Date range */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label
                      htmlFor="trip-start-date"
                      className="text-sm font-semibold text-neutral-800 flex items-center gap-1.5"
                    >
                      <Calendar className="w-3.5 h-3.5 text-neutral-500" aria-hidden="true" />
                      Start Date
                    </Label>
                    <Input
                      id="trip-start-date"
                      type="date"
                      value={startDate}
                      min={today}
                      onChange={(e) => {
                        setStartDate(e.target.value);
                        setFormErrors((p) => ({ ...p, startDate: undefined, endDate: undefined }));
                      }}
                      aria-invalid={!!formErrors.startDate}
                      className="bg-white border-neutral-200 text-neutral-900"
                    />
                    <FieldError message={formErrors.startDate} />
                  </div>

                  <div className="space-y-1.5">
                    <Label
                      htmlFor="trip-end-date"
                      className="text-sm font-semibold text-neutral-800 flex items-center gap-1.5"
                    >
                      <Calendar className="w-3.5 h-3.5 text-neutral-500" aria-hidden="true" />
                      End Date
                    </Label>
                    <Input
                      id="trip-end-date"
                      type="date"
                      value={endDate}
                      min={startDate || today}
                      onChange={(e) => {
                        setEndDate(e.target.value);
                        setFormErrors((p) => ({ ...p, endDate: undefined }));
                      }}
                      aria-invalid={!!formErrors.endDate}
                      className={`bg-white border-neutral-200 text-neutral-900 ${
                        formErrors.endDate ? "border-red-400" : ""
                      }`}
                    />
                    <FieldError message={formErrors.endDate} />
                  </div>
                </div>

                {/* Budget */}
                <div className="space-y-1.5">
                  <Label
                    htmlFor="trip-budget"
                    className="text-sm font-semibold text-neutral-800 flex items-center gap-1.5"
                  >
                    <DollarSign className="w-3.5 h-3.5 text-neutral-500" aria-hidden="true" />
                    Estimated Budget
                    <span className="text-xs font-normal text-neutral-400 ml-1">(optional)</span>
                  </Label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-neutral-500 text-sm">
                      $
                    </span>
                    <Input
                      id="trip-budget"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="e.g., 2500"
                      value={budget}
                      onChange={(e) => {
                        setBudget(e.target.value);
                        if (formErrors.budget)
                          setFormErrors((p) => ({ ...p, budget: undefined }));
                      }}
                      aria-invalid={!!formErrors.budget}
                      className={`pl-7 bg-white border-neutral-200 text-neutral-900 ${
                        formErrors.budget ? "border-red-400" : ""
                      }`}
                    />
                  </div>
                  <FieldError message={formErrors.budget} />
                </div>

                {/* Description */}
                <div className="space-y-1.5">
                  <Label
                    htmlFor="trip-description"
                    className="text-sm font-semibold text-neutral-800"
                  >
                    Description
                    <span className="text-xs font-normal text-neutral-400 ml-1">(optional)</span>
                  </Label>
                  <Textarea
                    id="trip-description"
                    placeholder="What are your goals for this trip? Any must-see places or experiences?"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="bg-white border-neutral-200 text-neutral-900 min-h-[88px] resize-none focus-visible:ring-blue-500"
                    rows={3}
                  />
                </div>
              </div>

              {/* Footer */}
              <DialogFooter className="px-6 py-4 bg-neutral-50 border-t border-neutral-100 flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleDialogChange(false)}
                  disabled={createTripMutation.isPending}
                  className="w-full sm:w-auto border-neutral-200"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createTripMutation.isPending}
                  className="w-full sm:w-auto bg-blue-600 text-white hover:bg-blue-700"
                  aria-label="Create trip"
                >
                  {createTripMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                      Creating Trip…
                    </>
                  ) : (
                    <>
                      <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                      Create Trip
                    </>
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
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search trips by title…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white border-neutral-200 text-neutral-900 w-full"
            aria-label="Search trips"
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
              : "Let's organise your next adventure. Create a trip to start planning your itinerary!"
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
              <Card
                key={trip.id}
                className="overflow-hidden flex flex-col transition-all hover:shadow-md border border-neutral-200 bg-white"
              >
                <div className="aspect-video relative overflow-hidden bg-neutral-200">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={
                      trip.cover_image_url ||
                      "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&q=80&w=800"
                    }
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
                      <CardTitle className="text-lg font-bold text-neutral-900 line-clamp-1">
                        {trip.title}
                      </CardTitle>
                      <CardDescription className="flex items-center text-xs text-neutral-500 mt-0.5">
                        <MapPin className="w-3 h-3 mr-1 text-neutral-400" />
                        {trip.place_name
                          ? `${trip.place_name}${trip.place_country ? `, ${trip.place_country}` : ""}`
                          : trip.destination_id
                          ? "Linked Destination"
                          : "Custom Route"}
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
                      {trip.start_date
                        ? new Date(trip.start_date).toLocaleDateString()
                        : "Flexible"}{" "}
                      —{" "}
                      {trip.end_date
                        ? new Date(trip.end_date).toLocaleDateString()
                        : "Flexible"}
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
                    <Button className="w-full font-semibold">Itinerary</Button>
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
