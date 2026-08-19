import React from "react";
import { Route, Switch, Redirect } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./features/auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./features/auth/LoginPage";
import { ShowListPage } from "./features/shows/ShowListPage";
import { ShowCreatePage } from "./features/shows/ShowCreatePage";
import { ShowDetailPage } from "./features/shows/ShowDetailPage";
import { EpisodeEditPage } from "./features/episodes/EpisodeEditPage";
import { PublishPage } from "./features/publish/PublishPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000
    }
  }
});

// Guarded Route Wrapper
const ProtectedRoute: React.FC<{ component: React.ComponentType }> = ({
  component: Component
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Redirect to="/login" />;
  }

  return (
    <Layout>
      <Component />
    </Layout>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Switch>
          {/* Public Login */}
          <Route path="/login" component={LoginPage} />

          {/* Admin Protected Routes */}
          <Route path="/admin/shows" component={() => <ProtectedRoute component={ShowListPage} />} />
          <Route path="/admin/shows/new" component={() => <ProtectedRoute component={ShowCreatePage} />} />
          <Route path="/admin/shows/:id" component={() => <ProtectedRoute component={ShowDetailPage} />} />
          <Route path="/admin/episodes/:id" component={() => <ProtectedRoute component={EpisodeEditPage} />} />
          <Route path="/admin/publish" component={() => <ProtectedRoute component={PublishPage} />} />

          {/* Default Redirects */}
          <Route path="/">
            <Redirect to="/admin/shows" />
          </Route>

          {/* 404 Fallback */}
          <Route>
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300 p-4">
              <h2 className="text-2xl font-bold mb-2">404 - Page Not Found</h2>
              <p className="text-sm text-slate-400 mb-4">The CMS page you requested does not exist.</p>
              <Redirect to="/admin/shows" />
            </div>
          </Route>
        </Switch>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
