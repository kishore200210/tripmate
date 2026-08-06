import Link from "next/link";
import { ArrowLeft, MapPin, Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const MOCK_ITINERARY = [
  {
    day: 1,
    date: "Oct 12, 2026",
    activities: [
      { time: "09:00 AM", title: "Arrival at CDG", type: "Travel", location: "Charles de Gaulle Airport" },
      { time: "11:30 AM", title: "Check-in", type: "Lodging", location: "Hotel Le Marais" },
      { time: "02:00 PM", title: "Eiffel Tower Visit", type: "Sightseeing", location: "Champ de Mars" },
      { time: "07:30 PM", title: "Dinner at Le Jules Verne", type: "Dining", location: "Eiffel Tower 2nd Floor" }
    ]
  },
  {
    day: 2,
    date: "Oct 13, 2026",
    activities: [
      { time: "10:00 AM", title: "Louvre Museum", type: "Sightseeing", location: "Musée du Louvre" },
      { time: "01:00 PM", title: "Lunch at Cafe Marly", type: "Dining", location: "Louvre Pyramid" },
      { time: "03:30 PM", title: "Seine River Cruise", type: "Activity", location: "Port de la Bourdonnais" }
    ]
  }
];

export default async function ItineraryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <Link href={`/trips/${id}`} className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Trip Overview
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Itinerary: Paris Getaway</h1>
        <p className="text-neutral-500 mt-1">Detailed day-by-day schedule.</p>
      </div>

      <div className="space-y-8">
        {MOCK_ITINERARY.map((day) => (
          <div key={day.day} className="relative pl-8 md:pl-0">
            <div className="md:grid md:grid-cols-12 gap-6">
              <div className="md:col-span-3 pb-4 md:pb-0 relative">
                {/* Timeline line connecting days on desktop */}
                <div className="hidden md:block absolute right-0 top-0 bottom-0 w-px bg-neutral-200" />
                <h3 className="text-xl font-bold text-neutral-900">Day {day.day}</h3>
                <p className="text-sm text-neutral-500 font-medium">{day.date}</p>
              </div>
              
              <div className="md:col-span-9 space-y-4">
                {day.activities.map((act, idx) => (
                  <Card key={idx} className="border-l-4 border-l-blue-500 shadow-sm">
                    <CardContent className="p-4 flex flex-col sm:flex-row gap-4 sm:items-center">
                      <div className="sm:w-32 flex-shrink-0 flex items-center text-sm font-semibold text-neutral-700">
                        <Clock className="w-4 h-4 mr-1.5 text-neutral-400" />
                        {act.time}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-base">{act.title}</h4>
                          <Badge variant="outline" className="text-[10px] uppercase tracking-wider py-0 font-medium">
                            {act.type}
                          </Badge>
                        </div>
                        <div className="flex items-center text-sm text-neutral-500">
                          <MapPin className="w-3.5 h-3.5 mr-1" />
                          {act.location}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
