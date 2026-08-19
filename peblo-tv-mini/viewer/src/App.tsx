import React from "react";
import { Route, Switch, Redirect } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navbar } from "./components/Navbar";
import { HomePage } from "./features/home/HomePage";
import { SearchPage } from "./features/search/SearchPage";
import { ShowDetailPage } from "./features/shows/ShowDetailPage";
import { Tv, ExternalLink } from "lucide-react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000,
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-indigo-600 selection:text-white">
        {/* Navigation Bar */}
        <Navbar />

        {/* Dynamic Route Content */}
        <main className="flex-1">
          <Switch>
            <Route path="/" component={HomePage} />
            <Route path="/search" component={SearchPage} />
            <Route path="/shows/:slug" component={ShowDetailPage} />
            <Route path="/show/:slug">
              {(params) => <Redirect to={`/shows/${params.slug}`} />}
            </Route>

            {/* 404 Route */}
            <Route>
              <div className="max-w-md mx-auto my-24 p-8 rounded-3xl bg-slate-900 border border-slate-800 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
                  <Tv className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-white">404 - Page Not Found</h2>
                <p className="text-xs text-slate-400">
                  The streaming page you requested does not exist.
                </p>
                <Redirect to="/" />
              </div>
            </Route>
          </Switch>
        </main>

        {/* Footer */}
        <footer className="mt-16 border-t border-slate-900 bg-slate-950 py-8 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-200">Peblo TV Mini</span>
              <span>•</span>
              <span>Child-Safe Streaming Experience</span>
            </div>

            <div className="flex items-center gap-4">
              <a
                href="http://localhost:3001"
                target="_blank"
                rel="noreferrer"
                className="hover:text-slate-200 transition-colors inline-flex items-center gap-1 text-indigo-400"
              >
                <span>CMS Content Studio</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
};

export default App;
