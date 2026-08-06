"use client";

import { useState, useEffect } from "react";
import { User, Mail, Shield, Bell, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useProfile, useUpdateProfile } from "@/hooks/useAuthAPI";
import toast from "react-hot-toast";

export default function ProfilePage() {
  const { data: profile, isLoading, isError } = useProfile();
  const updateMutation = useUpdateProfile();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  // Sync state with profile data once loaded
  useEffect(() => {
    if (profile) {
      setName(profile.name || "");
      setEmail(profile.email || "");
    }
  }, [profile]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      toast.error("Name and Email are required");
      return;
    }

    updateMutation.mutate(
      { name, email },
      {
        onSuccess: () => {
          toast.success("Profile updated successfully");
        },
        onError: (err: any) => {
          const detail = err.response?.data?.detail;
          if (detail && typeof detail === "string") {
            toast.error(detail);
          } else if (detail && Array.isArray(detail)) {
            toast.error(detail[0].msg || "Validation error");
          } else {
            toast.error("Failed to update profile");
          }
        },
      }
    );
  };

  // Derive initials for avatar fallback
  const initials = profile?.name
    ? profile.name
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (isError || !profile) {
    return (
      <div className="text-center py-20 text-red-500">
        Failed to load profile information. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Profile</h1>
        <p className="text-neutral-500">Manage your account settings and preferences.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        <aside className="w-full md:w-64 space-y-2">
          <Button variant="secondary" className="w-full justify-start">
            <User className="mr-2 h-4 w-4" />
            General
          </Button>
          <Button variant="ghost" className="w-full justify-start" disabled>
            <Shield className="mr-2 h-4 w-4" />
            Security
          </Button>
          <Button variant="ghost" className="w-full justify-start" disabled>
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </Button>
        </aside>

        <div className="flex-1 space-y-6">
          <form onSubmit={handleSave}>
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your personal details.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-6">
                  <Avatar className="w-20 h-20 border">
                    <AvatarImage src="https://ui.shadcn.com/avatars/01.png" alt={profile.name} />
                    <AvatarFallback>{initials}</AvatarFallback>
                  </Avatar>
                  <div className="space-y-2">
                    <Button size="sm" type="button" disabled>Change Photo</Button>
                    <p className="text-xs text-neutral-500">Change photo is not supported yet.</p>
                  </div>
                </div>
                
                <Separator />

                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input 
                      id="name" 
                      value={name} 
                      onChange={(e) => setName(e.target.value)} 
                      required 
                      className="text-gray-900 bg-white"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email</Label>
                    <div className="relative flex items-center">
                      <Mail className="w-4 h-4 text-neutral-500 absolute left-3" />
                      <Input 
                        id="email" 
                        type="email"
                        value={email} 
                        onChange={(e) => setEmail(e.target.value)} 
                        required 
                        className="pl-9 text-gray-900 bg-white"
                      />
                    </div>
                  </div>
                </div>

                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </CardContent>
            </Card>
          </form>
        </div>
      </div>
    </div>
  );
}
