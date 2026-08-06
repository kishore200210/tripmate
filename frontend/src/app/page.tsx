import Link from "next/link";
import { Plane, Compass, FileText, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col font-sans">
      <header className="px-6 py-4 flex items-center justify-between border-b bg-white">
        <div className="flex items-center gap-2 text-2xl font-bold text-neutral-900">
          <Plane className="w-8 h-8 text-blue-600" />
          TripMate
        </div>
        <nav className="flex gap-4">
          <Link href="/login">
            <Button variant="ghost">Log In</Button>
          </Link>
          <Link href="/signup">
            <Button>Sign Up</Button>
          </Link>
        </nav>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="px-6 py-24 text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-extrabold text-neutral-900 mb-6 tracking-tight">
            Plan your next adventure with the power of AI.
          </h1>
          <p className="text-xl text-neutral-600 mb-10 max-w-2xl mx-auto">
            TripMate is your all-in-one travel concierge. Generate itineraries, analyze landmarks, and manage bookings seamlessly.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="text-lg px-8">Get Started</Button>
            </Link>
            <Link href="/destinations">
              <Button size="lg" variant="outline" className="text-lg px-8">Browse Destinations</Button>
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="bg-white py-24 px-6 border-t">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Everything you need for the perfect trip</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <Card className="border-neutral-200 shadow-sm">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mb-4">
                    <Compass className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Smart Recommendations</h3>
                  <p className="text-neutral-600">Discover destinations tailored to your budget and climate preferences using our ML-powered engine.</p>
                </CardContent>
              </Card>
              
              <Card className="border-neutral-200 shadow-sm">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mb-4">
                    <Bot className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">AI Concierge</h3>
                  <p className="text-neutral-600">Chat with a dedicated AI assistant that has deep context about your trips and can fetch live weather.</p>
                </CardContent>
              </Card>

              <Card className="border-neutral-200 shadow-sm">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-red-100 text-red-600 rounded-lg flex items-center justify-center mb-4">
                    <FileText className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">PDF Itineraries</h3>
                  <p className="text-neutral-600">Instantly generate beautifully formatted PDFs of your entire itinerary, processed securely in the background.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-8 text-center text-neutral-500 text-sm border-t bg-white">
        &copy; {new Date().getFullYear()} TripMate Capstone. All rights reserved.
      </footer>
    </div>
  );
}
