"use client";

import Link from "next/link";
import { useState } from "react";
import { Plane, Eye, EyeOff, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

import { useSignup } from "@/hooks/useAuthAPI";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const signupMutation = useSignup();

  const validatePassword = (pass: string) => {
    if (pass.length < 8) return "Password must be at least 8 characters long.";
    if (!/[A-Z]/.test(pass)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(pass)) return "Password must contain at least one lowercase letter.";
    if (!/\d/.test(pass)) return "Password must contain at least one number.";
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/.test(pass)) return "Password must contain at least one special character.";
    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const errorMsg = validatePassword(password);
    if (errorMsg) {
      setPasswordError(errorMsg);
      toast.error(errorMsg);
      return;
    }
    setPasswordError("");
    
    signupMutation.mutate(
      {
        email: email,
        password: password,
        name: name,
      },
      {
        onSuccess: () => {
          toast.success("Registration successful");
        },
        onError: (error: any) => {
          console.error("Registration Error:", error);
          if (error.response) {
            console.error(error.response);
            console.error(error.response.data);
            console.error(error.response.status);
          }
          
          let errorMessage = "Something went wrong on the server.";
          
          if (!error.response) {
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
              errorMessage = "Request timed out.";
            } else {
              errorMessage = "Backend server is not running.";
            }
          } else {
            const status = error.response.status;
            const data = error.response.data;
            
            if (data && data.detail) {
              if (typeof data.detail === "string") {
                errorMessage = data.detail;
              } else if (Array.isArray(data.detail)) {
                errorMessage = "Validation failed: " + data.detail.map((e: any) => e.msg).join(", ");
              } else {
                errorMessage = JSON.stringify(data.detail);
              }
            } else if (status === 409) {
              errorMessage = "Email already exists.";
            } else if (status === 422) {
              errorMessage = "Validation failed.";
            } else if (status === 400) {
              errorMessage = "Invalid request.";
            } else if (status === 401) {
              errorMessage = "Unauthorized.";
            } else if (status === 500) {
              errorMessage = "Something went wrong on the server.";
            }
          }

          toast.error(errorMessage);
        }
      }
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <Link href="/" className="flex items-center gap-2 mb-8 text-2xl font-bold text-gray-900">
        <Plane className="w-8 h-8 text-blue-600" />
        TripMate
      </Link>
      
      <Card className="w-full max-w-md shadow-md border border-gray-200 bg-white">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center text-gray-900">Create an account</CardTitle>
          <CardDescription className="text-center text-gray-500">
            Enter your details below to create your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-gray-700">Full Name</Label>
              <Input 
                id="name" 
                placeholder="John Doe" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                required 
                className="text-gray-900 border-gray-300 placeholder:text-gray-400 rounded-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent bg-white" 
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-700">Email</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="m@example.com" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
                className="text-gray-900 border-gray-300 placeholder:text-gray-400 rounded-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent bg-white" 
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-700">Password</Label>
              <div className="relative">
                <Input 
                  id="password" 
                  type={showPassword ? "text" : "password"} 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)} 
                  required 
                  className="text-gray-900 border-gray-300 placeholder:text-gray-400 rounded-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent bg-white pr-10" 
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              {passwordError && (
                <p className="text-sm text-red-500 mt-1">{passwordError}</p>
              )}
            </div>
            <Button 
              type="submit" 
              className="w-full bg-blue-600 text-white hover:bg-blue-700 rounded-md" 
              disabled={signupMutation.isPending}
            >
              {signupMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                "Sign Up"
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center bg-white border-t border-gray-100 rounded-b-xl">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <Link href="/login" className="text-blue-600 hover:text-blue-700 hover:underline font-medium">
              Log in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
