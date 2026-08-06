"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plane, LayoutDashboard, Map, Compass, MessageSquare, LogOut } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Destinations", href: "/destinations", icon: Compass },
  { name: "My Trips", href: "/trips", icon: Map },
  { name: "Concierge", href: "/chat", icon: MessageSquare },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  // Derive initials from the user's name for the avatar fallback
  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

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
          <Link href="/profile" className="flex items-center gap-2">
            <Avatar className="w-8 h-8 cursor-pointer border border-neutral-200">
              <AvatarImage src="https://ui.shadcn.com/avatars/01.png" alt={user?.name ?? "User"} />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <span className="hidden md:inline-block text-sm font-medium text-neutral-700 hover:text-blue-600">{user?.name}</span>
          </Link>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={handleLogout} 
            title="Log Out" 
            className="h-8 w-8 text-neutral-500 hover:text-red-600"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
