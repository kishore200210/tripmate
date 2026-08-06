"use client";

import { User, Mail, Shield, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

export default function ProfilePage() {
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
          <Button variant="ghost" className="w-full justify-start">
            <Shield className="mr-2 h-4 w-4" />
            Security
          </Button>
          <Button variant="ghost" className="w-full justify-start">
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </Button>
        </aside>

        <div className="flex-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your profile photo and personal details.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6">
                <Avatar className="w-20 h-20 border">
                  <AvatarImage src="https://ui.shadcn.com/avatars/01.png" />
                  <AvatarFallback>JD</AvatarFallback>
                </Avatar>
                <div className="space-y-2">
                  <Button size="sm">Change Photo</Button>
                  <p className="text-xs text-neutral-500">JPG, GIF or PNG. Max size of 2MB.</p>
                </div>
              </div>
              
              <Separator />

              <div className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input id="name" defaultValue="John Doe" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-neutral-500 absolute ml-3" />
                    <Input id="email" defaultValue="demo@example.com" className="pl-9" />
                  </div>
                </div>
              </div>

              <Button>Save Changes</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
