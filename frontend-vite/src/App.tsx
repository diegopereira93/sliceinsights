import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

import Home from "@/pages/Home";
import Quiz from "@/pages/Quiz";
import Chat from "@/pages/Chat";
import Stats from "@/pages/Stats";
import NotFound from "@/pages/not-found";

import { BottomNav } from "@/components/BottomNav";
import { BattleProvider } from "@/components/BattleContext";
import { BattleOverlay } from "@/components/BattleOverlay";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    }
  }
});

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/recommend" component={Quiz} />
      <Route path="/chat" component={Chat} />
      <Route path="/statistics" component={Stats} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BattleProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <div className="min-h-screen bg-background text-foreground relative">
              <Router />
              <BottomNav />
              <BattleOverlay />
            </div>
          </WouterRouter>
        </BattleProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
