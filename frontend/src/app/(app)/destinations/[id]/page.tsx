import Link from "next/link";
import { ArrowLeft, MapPin, Calendar, Compass, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default async function DestinationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  // Static mock based on ID
  const destName = id === "1" ? "Paris, France" : "Destination Details";
  const destImage = id === "1" 
    ? "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&q=80&w=1200"
    : "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&q=80&w=1200";

  return (
    <div className="space-y-6">
      <Link href="/destinations" className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 mb-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Destinations
      </Link>

      <div className="relative h-[300px] sm:h-[400px] rounded-xl overflow-hidden shadow-md">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={destImage} alt={destName} className="object-cover w-full h-full" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-6 left-6 text-white">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2">{destName}</h1>
          <div className="flex items-center gap-4 text-sm font-medium">
            <span className="flex items-center"><MapPin className="w-4 h-4 mr-1" /> Europe</span>
            <span className="flex items-center"><Star className="w-4 h-4 mr-1 text-yellow-400 fill-yellow-400" /> 4.8 Rating</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="attractions">Top Attractions</TabsTrigger>
              <TabsTrigger value="reviews">Reviews</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-4 pt-4 text-neutral-600 leading-relaxed">
              <p>
                Paris is the capital and most populous city of France. Since the 17th century, Paris has been one of Europe&apos;s major centres of finance, diplomacy, commerce, fashion, gastronomy, science, and arts.
              </p>
              <p>
                The city is a major railway, highway, and air-transport hub served by two international airports. The city&apos;s subway system, the Paris Métro, serves 5.23 million passengers daily.
              </p>
            </TabsContent>
            
            <TabsContent value="attractions" className="space-y-4 pt-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Eiffel Tower</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-neutral-500">
                    Iconic wrought-iron lattice tower on the Champ de Mars.
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Louvre Museum</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-neutral-500">
                    The world&apos;s most-visited museum and a historic monument in Paris.
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="reviews" className="pt-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-neutral-200 flex-shrink-0" />
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-neutral-900">Jane Smith</span>
                        <div className="flex text-yellow-400">
                          <Star className="w-3 h-3 fill-current" /><Star className="w-3 h-3 fill-current" /><Star className="w-3 h-3 fill-current" /><Star className="w-3 h-3 fill-current" /><Star className="w-3 h-3 fill-current" />
                        </div>
                      </div>
                      <p className="text-sm text-neutral-600">Absolutely magical experience! The food, the architecture, everything was perfect.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Trip Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 flex items-center"><Calendar className="w-4 h-4 mr-2" /> Best Time</span>
                <span className="font-medium">Apr - Jun</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 flex items-center"><Compass className="w-4 h-4 mr-2" /> Climate</span>
                <span className="font-medium">Temperate</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-500">Avg. Budget</span>
                <Badge variant="secondary">$$$</Badge>
              </div>
              <Button className="w-full mt-4">Plan a Trip Here</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
