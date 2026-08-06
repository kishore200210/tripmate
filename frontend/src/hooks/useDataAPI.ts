import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Fetch all destinations from the backend
export function useDestinations() {
  return useQuery({
    queryKey: ["destinations"],
    queryFn: async () => {
      const { data } = await api.get("/destinations/");
      return data; // Array of destinations
    },
  });
}

// Fetch a single destination detail
export function useDestination(id: string) {
  return useQuery({
    queryKey: ["destinations", id],
    queryFn: async () => {
      const { data } = await api.get(`/destinations/${id}`);
      return data;
    },
    enabled: !!id, // Only run if ID is provided
  });
}

// Fetch all user trips
export function useTrips() {
  return useQuery({
    queryKey: ["trips"],
    queryFn: async () => {
      const { data } = await api.get("/trips/");
      return data;
    },
  });
}

// Fetch single trip
export function useTrip(id: string) {
  return useQuery({
    queryKey: ["trips", id],
    queryFn: async () => {
      const { data } = await api.get(`/trips/${id}`);
      return data;
    },
    enabled: !!id,
  });
}
