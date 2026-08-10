"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { useAdminAnalytics } from "@/hooks/useDataAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/ErrorState";
import {
  Users,
  UserCheck,
  Map,
  CheckCircle2,
  DollarSign,
  TrendingUp,
  Shield,
  Lock,
  Loader2,
  MapPin,
  CalendarDays,
  Info
} from "lucide-react";

// Helper to format currency
const formatCurrency = (value: number | null) => {
  if (value === null || value === undefined) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
};

// Helper to format general integers with commas
const formatNumber = (value: number) => {
  return new Intl.NumberFormat("en-US").format(value);
};

// ── Custom SVG Donut Chart component ─────────────────────────────────────────
function DonutChart({ planning, confirmed, ongoing, completed, cancelled }: {
  planning: number; confirmed: number; ongoing: number; completed: number; cancelled: number;
}) {
  const total = planning + confirmed + ongoing + completed + cancelled;

  const data = [
    { label: "Planning", count: planning, color: "#3B82F6" },
    { label: "Confirmed", count: confirmed, color: "#6366F1" },
    { label: "Ongoing", count: ongoing, color: "#F59E0B" },
    { label: "Completed", count: completed, color: "#10B981" },
    { label: "Cancelled", count: cancelled, color: "#EF4444" },
  ].filter(item => item.count > 0);

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-neutral-400 italic">
        No trip status data to display
      </div>
    );
  }

  // Circle properties
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.159
  let accumulatedPercent = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-6 py-4">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 120 120" className="w-full h-full transform -rotate-90">
          {data.map((item, idx) => {
            const percent = (item.count / total) * 100;
            const strokeDashoffset = circumference - (percent / 100) * circumference;
            const rotation = (accumulatedPercent / 100) * 360;
            accumulatedPercent += percent;

            return (
              <circle
                key={idx}
                cx="60"
                cy="60"
                r={radius}
                fill="transparent"
                stroke={item.color}
                strokeWidth="12"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                transform={`rotate(${rotation} 60 60)`}
                className="transition-all duration-500 ease-out hover:stroke-[14px]"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-xl font-extrabold text-neutral-800">{total}</span>
          <span className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">Trips</span>
        </div>
      </div>

      <div className="flex flex-col gap-2 text-sm w-full sm:w-auto">
        {data.map((item, idx) => {
          const percent = ((item.count / total) * 100).toFixed(1);
          return (
            <div key={idx} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
              <span className="font-medium text-neutral-700 min-w-[80px]">{item.label}</span>
              <span className="text-neutral-400 font-bold text-xs">{item.count} ({percent}%)</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Custom SVG Line Chart component ──────────────────────────────────────────
function LineChart({ data }: { data: { month: string; count: number }[] }) {
  if (data.length === 0) {
    return <div className="text-sm text-neutral-400 italic py-16 text-center">No registration trend data available</div>;
  }

  const maxVal = Math.max(...data.map(d => d.count), 1);
  const width = 500;
  const height = 220;
  const paddingLeft = 40;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const points = data.map((d, index) => {
    const x = paddingLeft + (index / (data.length - 1 || 1)) * chartWidth;
    const y = paddingTop + chartHeight - (d.count / maxVal) * chartHeight;
    return { x, y, month: d.month, count: d.count };
  });

  const pathData = points.reduce((acc, p, i) => {
    return acc + `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
  }, "");

  const areaData = pathData + ` L ${points[points.length - 1].x} ${paddingTop + chartHeight} L ${points[0].x} ${paddingTop + chartHeight} Z`;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
        <defs>
          <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = paddingTop + chartHeight * ratio;
          const val = Math.round(maxVal * (1 - ratio));
          return (
            <g key={i}>
              <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#F3F4F6" strokeWidth={1} />
              <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="text-[10px] fill-neutral-400 font-semibold">{val}</text>
            </g>
          );
        })}

        {/* Shaded Area */}
        <path d={areaData} fill="url(#area-grad)" />

        {/* Connected Line */}
        <path d={pathData} fill="none" stroke="#2563EB" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />

        {/* Data Circles & Labels */}
        {points.map((p, i) => (
          <g key={i} className="group">
            <circle cx={p.x} cy={p.y} r={4} fill="#2563EB" stroke="#FFFFFF" strokeWidth={1.5} />
            {/* Show value label on top of point */}
            <text x={p.x} y={p.y - 8} textAnchor="middle" className="text-[9px] fill-neutral-600 font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-white">
              {p.count}
            </text>
            {/* X Axis Month Label */}
            {i % Math.max(1, Math.round(points.length / 5)) === 0 && (
              <text x={p.x} y={height - 10} textAnchor="middle" className="text-[10px] fill-neutral-400 font-medium">
                {p.month}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}

// ── Custom SVG Column Chart component ────────────────────────────────────────
function ColumnChart({ data }: { data: { month: string; count: number }[] }) {
  if (data.length === 0) {
    return <div className="text-sm text-neutral-400 italic py-16 text-center">No trip creation trend data available</div>;
  }

  const maxVal = Math.max(...data.map(d => d.count), 1);
  const width = 500;
  const height = 220;
  const paddingLeft = 40;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const barWidth = (chartWidth / data.length) * 0.6;
  const barGap = (chartWidth / data.length) * 0.4;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
        <defs>
          <linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4F46E5" />
            <stop offset="100%" stopColor="#6366F1" />
          </linearGradient>
        </defs>

        {/* Horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = paddingTop + chartHeight * ratio;
          const val = Math.round(maxVal * (1 - ratio));
          return (
            <g key={i}>
              <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#F3F4F6" strokeWidth={1} />
              <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="text-[10px] fill-neutral-400 font-semibold">{val}</text>
            </g>
          );
        })}

        {/* Columns */}
        {data.map((d, index) => {
          const x = paddingLeft + index * (barWidth + barGap) + barGap / 2;
          const barHeight = (d.count / maxVal) * chartHeight;
          const y = paddingTop + chartHeight - barHeight;
          return (
            <g key={index} className="group">
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={3}
                fill="url(#bar-grad)"
                className="transition-all duration-200 hover:fill-[#4338CA]"
              />
              <text x={x + barWidth / 2} y={y - 6} textAnchor="middle" className="text-[9px] fill-neutral-600 font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                {d.count}
              </text>
              {/* X Axis Month Label */}
              {index % Math.max(1, Math.round(data.length / 5)) === 0 && (
                <text x={x + barWidth / 2} y={height - 10} textAnchor="middle" className="text-[10px] fill-neutral-400 font-medium">
                  {d.month}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ── Admin Analytics Page component ───────────────────────────────────────────
export default function AdminAnalyticsPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);

  const { data: analytics, isLoading, isError, refetch } = useAdminAnalytics();
  const [isAdminChecked, setIsAdminChecked] = useState(false);

  useEffect(() => {
    // If auth state is loaded, perform the admin check
    if (user) {
      setIsAdminChecked(true);
    }
  }, [user]);

  // 1. Loading State
  if (isLoading || !isAdminChecked) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <Loader2 className="h-10 w-10 animate-spin text-[#2563EB] mb-4" />
        <p className="text-neutral-500 font-medium">Loading platform analytics...</p>
      </div>
    );
  }

  // 2. Unauthorized State
  if (user?.role !== "admin") {
    return (
      <div className="max-w-md mx-auto my-16 text-center">
        <Card className="border-red-100 shadow-xl bg-white p-8">
          <div className="flex justify-center mb-6">
            <div className="rounded-full bg-red-50 p-4 border border-red-100">
              <Lock className="w-12 h-12 text-red-500" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-neutral-900 tracking-tight mb-2">Access Denied</h2>
          <p className="text-neutral-500 mb-6">
            This module is restricted to platform administrators only. You do not have permissions to access these statistics.
          </p>
          <Button onClick={() => router.push("/dashboard")} className="w-full">
            Back to User Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  // 3. API Error State
  if (isError) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <ErrorState
          message="Failed to load site-wide admin analytics. Please check your connection and try again."
          onRetry={refetch}
        />
      </div>
    );
  }

  const {
    summary,
    status_distribution,
    top_destinations,
    monthly_user_registrations,
    monthly_trip_creations,
  } = analytics!;

  const totalDestinationsCount = top_destinations.length;
  const isEmptyData =
    summary.total_users === 0 &&
    summary.total_trips === 0 &&
    totalDestinationsCount === 0 &&
    monthly_user_registrations.length === 0 &&
    monthly_trip_creations.length === 0;

  // 4. Empty Platform Data State
  if (isEmptyData) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 pb-5">
          <div>
            <h1 className="text-3xl font-extrabold text-neutral-900 tracking-tight flex items-center gap-2">
              <Shield className="w-8 h-8 text-[#2563EB]" />
              Admin Analytics
            </h1>
            <p className="text-neutral-500 text-sm mt-1">Platform overview metrics</p>
          </div>
          <span className="self-start sm:self-center inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 ring-1 ring-inset ring-blue-700/10">
            Admin Mode
          </span>
        </div>

        <Card className="border-dashed border-2 border-neutral-200 py-16 flex flex-col items-center justify-center text-center max-w-xl mx-auto bg-neutral-50">
          <Info className="w-12 h-12 text-neutral-300 mb-4" />
          <h3 className="text-lg font-bold text-neutral-900">No Platform Data Found</h3>
          <p className="text-sm text-neutral-500 mb-6 max-w-md mt-1">
            TripMate is fully set up, but no users or trips have been registered yet. Once data enters the platform, analytics will render here automatically.
          </p>
          <Button onClick={() => refetch()} variant="outline">
            Refresh Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  // 5. Successful Render State
  const maxDestCount = Math.max(...top_destinations.map(d => d.trip_count), 1);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-neutral-900 tracking-tight flex items-center gap-2">
            <Shield className="w-8 h-8 text-[#2563EB]" />
            Admin Analytics
          </h1>
          <p className="text-neutral-500 text-sm mt-1">Monitor platform health, travel trends, and user statistics.</p>
        </div>
        <span className="self-start sm:self-center inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 ring-1 ring-inset ring-blue-700/10">
          Admin Mode
        </span>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Total Users</CardTitle>
            <Users className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-neutral-900">{formatNumber(summary.total_users)}</div>
            <p className="text-xs text-neutral-500 mt-1">All registered accounts</p>
          </CardContent>
        </Card>

        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Active Users</CardTitle>
            <UserCheck className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-[#10B981]">{formatNumber(summary.active_users)}</div>
            <p className="text-xs text-neutral-500 mt-1">Non-deleted active accounts</p>
          </CardContent>
        </Card>

        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Total Trips</CardTitle>
            <Map className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-neutral-900">{formatNumber(summary.total_trips)}</div>
            <p className="text-xs text-neutral-500 mt-1">Planned and tracked trips</p>
          </CardContent>
        </Card>

        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Completed Trips</CardTitle>
            <CheckCircle2 className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-neutral-900">{formatNumber(summary.completed_trips)}</div>
            <p className="text-xs text-neutral-500 mt-1">Completed travel itineraries</p>
          </CardContent>
        </Card>

        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Avg Trip Budget</CardTitle>
            <TrendingUp className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-neutral-900">{formatCurrency(summary.average_trip_budget)}</div>
            <p className="text-xs text-neutral-500 mt-1">Per-trip budget average</p>
          </CardContent>
        </Card>

        <Card className="bg-white hover:shadow-md transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold text-neutral-500 uppercase tracking-wider">Total Budget Vol</CardTitle>
            <DollarSign className="h-5 w-5 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-[#4F46E5]">{formatCurrency(summary.total_trip_budget)}</div>
            <p className="text-xs text-neutral-500 mt-1">Sum of all trip budgets</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Charts Sections */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Trip Status Distribution (Donut Chart) */}
        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-neutral-850">Trip Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <DonutChart
              planning={status_distribution.planning}
              confirmed={status_distribution.confirmed}
              ongoing={status_distribution.ongoing}
              completed={status_distribution.completed}
              cancelled={status_distribution.cancelled}
            />
          </CardContent>
        </Card>

        {/* Top Destinations (Horizontal Bar Chart) */}
        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-neutral-850">Popular Destinations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {top_destinations.length === 0 ? (
              <div className="text-sm text-neutral-450 italic py-12 text-center">
                No popular destination data available
              </div>
            ) : (
              <div className="space-y-4 py-2">
                {top_destinations.map((dest, i) => {
                  const percent = (dest.trip_count / maxDestCount) * 100;
                  return (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-sm font-medium">
                        <span className="flex items-center gap-1.5 text-neutral-700">
                          <MapPin className="w-3.5 h-3.5 text-neutral-400" />
                          {dest.name}, {dest.country}
                        </span>
                        <span className="text-neutral-500 text-xs font-semibold">
                          {dest.trip_count} {dest.trip_count === 1 ? "trip" : "trips"}
                        </span>
                      </div>
                      <div className="w-full bg-neutral-100 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full rounded-full transition-all duration-500"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* User Registration Trend (Line Chart) */}
        <Card className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-bold text-neutral-850">User Registrations Trend</CardTitle>
            <CalendarDays className="w-4 h-4 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <LineChart data={monthly_user_registrations} />
          </CardContent>
        </Card>

        {/* Trip Creation Trend (Column Chart) */}
        <Card className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-bold text-neutral-850">Trip Creation Trend</CardTitle>
            <CalendarDays className="w-4 h-4 text-neutral-400" />
          </CardHeader>
          <CardContent>
            <ColumnChart data={monthly_trip_creations} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
