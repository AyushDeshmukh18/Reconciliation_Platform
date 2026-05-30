import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Landing } from "@/pages/Landing";
import { Dashboard } from "@/pages/Dashboard";
import { ExceptionWorkbench } from "@/pages/ExceptionWorkbench";
import { ExceptionDetail } from "@/pages/ExceptionDetail";
import { Reports } from "@/pages/Reports";
import { AuditLog } from "@/pages/AuditLog";
import { Transactions } from "@/pages/Transactions";
import { UploadCenter } from "@/pages/UploadCenter";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ScrollRestoration() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const id = hash.replace("#", "");
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }

    window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
  }, [pathname, hash]);

  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ScrollRestoration />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route
            element={<AppShell />}
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/upload" element={<UploadCenter />} />
            <Route path="/exceptions" element={<ExceptionWorkbench />} />
            <Route path="/exceptions/:resultId" element={<ExceptionDetail />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/audit" element={<AuditLog />} />
            <Route path="/transactions" element={<Transactions />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
