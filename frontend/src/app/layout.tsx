import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import Providers from "./providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "TripMate — Your AI Travel Companion",
    template: "%s | TripMate",
  },
  description:
    "Plan your perfect trip with AI-powered itineraries, live weather, currency tools, and a personal travel concierge.",
  keywords: ["travel", "AI", "trip planner", "itinerary", "travel concierge"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans relative">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
