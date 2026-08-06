"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plane, LayoutDashboard, Map, Compass, MessageSquare, UserCircle } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Destinations", href: "/destinations", icon: Compass },
  { name: "My Trips", href: "/trips", icon: Map },
  { name: "Concierge", href: "/chat", icon: MessageSquare },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-white">
      <div className="container flex h-16 items-center px-4 md:px-6 mx-auto">
        <Link href="/dashboard" className="flex items-center gap-2 mr-6 text-xl font-bold text-neutral-900">
          <Plane className="w-6 h-6 text-blue-600" />
          <span className="hidden sm:inline-block">TripMate</span>
        </Link>
        <nav className="flex items-center gap-6 flex-1 overflow-x-auto text-sm font-medium">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 transition-colors hover:text-blue-600 ${
                  isActive ? "text-blue-600" : "text-neutral-600"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline-block">{item.name}</span>
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-4 ml-auto">
          <Link href="/profile">
            <Avatar className="w-8 h-8 cursor-pointer border border-neutral-200">
              <AvatarImage src="https://ui.shadcn.com/avatars/01.png" alt="User" />
              <AvatarFallback>U</AvatarFallback>
            </Avatar>
          </Link>
        </div>
      </div>
    </header>
  );
}
