"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/dashboard-layout";

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/agents");
  }, [router]);

  return (
    <DashboardLayout>
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Redirecting to AI Agents...</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
