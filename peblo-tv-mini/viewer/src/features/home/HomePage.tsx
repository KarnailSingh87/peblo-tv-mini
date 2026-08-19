import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Tv, AlertCircle, RefreshCw, Sparkles, Film } from "lucide-react";
import { viewerApi } from "../../services/api";
import { HeroBanner } from "../../components/HeroBanner";
import { ShowRow } from "../../components/ShowRow";
import { REFERENCE_SECTIONS, CatalogueShow } from "../../types";

export const HomePage: React.FC = () => {
  const { data: catalog, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => viewerApi.getCatalog(),
    staleTime: 60000
  });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        {/* Hero Skeleton */}
        <div className="w-full h-[460px] rounded-3xl bg-slate-900 border border-slate-800" />
        {/* Row Skeletons */}
        <div className="space-y-3">
          <div className="w-48 h-6 rounded-md bg-slate-800" />
          <div className="flex gap-4 overflow-hidden">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="w-44 h-64 rounded-xl bg-slate-900 border border-slate-800 shrink-0" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !catalog) {
    const is404 = (error as any)?.status === 404;
    return (
      <div className="max-w-xl mx-auto my-20 p-8 rounded-3xl bg-slate-900/60 border border-slate-800 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto">
          <Tv className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white">
          {is404 ? "No Published Catalogue Yet" : "Unable to Load Catalogue"}
        </h2>
        <p className="text-sm text-slate-400 leading-relaxed">
          {is404
            ? "The streaming catalogue has not been published yet. Log in to the CMS studio to run a validation check and release the live catalogue."
            : (error as any)?.message || "Failed to fetch live catalogue."}
        </p>

        <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Check Again</span>
          </button>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700"
          >
            Open CMS Studio
          </a>
        </div>
      </div>
    );
  }

  // Choose hero show: first in 'featured' section or first in shows list
  const featuredShows = catalog.sections?.featured || [];
  const heroShow: CatalogueShow | undefined =
    featuredShows[0] || catalog.shows?.[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-10">
      {/* Featured Hero Banner */}
      {heroShow && <HeroBanner show={heroShow} />}

      {/* Horizontal Shelves by Section */}
      <div className="space-y-8">
        {REFERENCE_SECTIONS.map((sec) => {
          const sectionShows = catalog.sections?.[sec.key] || [];
          return (
            <ShowRow
              key={sec.key}
              title={sec.title}
              subtitle={`Explore ${sec.key} programming`}
              shows={sectionShows}
            />
          );
        })}
      </div>
    </div>
  );
};
