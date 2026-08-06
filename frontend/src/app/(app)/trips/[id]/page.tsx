import Link from "next/link";
import { ArrowLeft, MapPin, Calendar, Clock, Plane, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default async function TripDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Link href="/trips" className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Trips
      </Link>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Paris Getaway</h1>
          <p className="text-neutral-500 flex items-center mt-1">
            <MapPin className="w-4 h-4 mr-1" /> Paris, France
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/trips/${id}/itinerary`}>
            <Button>
              <Calendar className="w-4 h-4 mr-2" />
              View Itinerary
            </Button>
          </Link>
          <Button variant="outline">
            <FileText className="w-4 h-4 mr-2" />
            Generate PDF
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Trip Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-900">Dates</p>
                  <p className="text-sm text-neutral-500">Oct 12 - Oct 18, 2026</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="bg-purple-100 p-2 rounded-lg text-purple-600">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-900">Duration</p>
                  <p className="text-sm text-neutral-500">7 Days</p>
                </div>
              </div>
            </div>
            
            <Separator />
            
            <div>
              <h3 className="font-semibold mb-2">About this trip</h3>
              <p className="text-sm text-neutral-600 leading-relaxed">
                A romantic week in Paris exploring museums, dining at classic bistros, and wandering through the historic streets. We will be visiting the Eiffel Tower, the Louvre, and taking a day trip to Versailles.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Logistics</CardTitle>
            <CardDescription>Flight & Hotel Info</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold flex items-center"><Plane className="w-4 h-4 mr-1 text-neutral-500" /> Outbound Flight</h4>
              <div className="text-sm border rounded p-3 bg-neutral-50">
                <p className="font-medium">AF1234 - Air France</p>
                <p className="text-neutral-500">Oct 12 • 08:30 AM (JFK)</p>
              </div>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-semibold flex items-center"><MapPin className="w-4 h-4 mr-1 text-neutral-500" /> Accommodation</h4>
              <div className="text-sm border rounded p-3 bg-neutral-50">
                <p className="font-medium">Hotel Le Marais</p>
                <p className="text-neutral-500">Check-in: Oct 12, 14:00</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
