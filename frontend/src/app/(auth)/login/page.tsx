"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Plane } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

import { useLogin } from "@/hooks/useAuthAPI";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const loginMutation = useLogin();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);
    loginMutation.mutate(params);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <Link href="/" className="flex items-center gap-2 mb-8 text-2xl font-bold text-gray-900">
        <Plane className="w-8 h-8 text-blue-600" />
        TripMate
      </Link>
      
      <Card className="w-full max-w-md shadow-md border border-gray-200 bg-white">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center text-gray-900">Welcome back</CardTitle>
          <CardDescription className="text-center text-gray-500">
            Enter your email and password to log in
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-700">Email</Label>
              <Input 
                id="email" 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                placeholder="m@example.com" 
                required 
                className="text-gray-900 border-gray-300 placeholder:text-gray-400 rounded-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent bg-white" 
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-gray-700">Password</Label>
                <Link href="#" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
                  Forgot password?
                </Link>
              </div>
              <Input 
                id="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                className="text-gray-900 border-gray-300 placeholder:text-gray-400 rounded-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent bg-white" 
              />
            </div>
            {loginMutation.isError && (
              <p className="text-sm text-red-600 font-medium">Invalid email or password.</p>
            )}
            <Button 
              type="submit" 
              className="w-full bg-blue-600 text-white hover:bg-blue-700 rounded-md" 
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Logging in..." : "Log In"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center bg-white border-t border-gray-100 rounded-b-xl">
          <p className="text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-blue-600 hover:text-blue-700 hover:underline font-medium">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
