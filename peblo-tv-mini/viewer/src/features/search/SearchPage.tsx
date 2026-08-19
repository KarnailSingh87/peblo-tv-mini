import React, { useState } from "react";
import { Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Filter,
  Film,
  Layers,
  Sparkles,
  AlertCircle,
  X,
  Volume2
} from "lucide-react";
import { viewerApi } from "../../services/api";
import { ImageWithFallback } from "../../components/ImageWithFallback";
import { REFERENCE_CATEGORIES, REFERENCE_SECTIONS } from "../../types";

export const SearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [selectedSection, setSelectedSection] = useState("");
  const [page, setPage] = useState(1);

  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ["search", searchTerm, selectedCategory, selectedLanguage, selectedSection, page],
    queryFn: () =>
      viewerApi.searchCatalog({
        q: searchTerm.trim() || undefined,
        category: selectedCategory || undefined,
        language: selectedLanguage || undefined,
        section: selectedSection || undefined,
        page,
        page_size: 24
      })
  });

  const clearFilters = () => {
    setSearchTerm("");
    setSelectedCategory("");
    setSelectedLanguage("");
    setSelectedSection("");
    setPage(1);
  };

  const hasActiveFilters =
    !!searchTerm || !!selectedCategory || !!selectedLanguage || !!selectedSection;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Search Header */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Explore & Search Catalogue
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Search titles, episodes, themes, and filter by audio languages and categories.
          </p>
        </div>

        {/* Big Search Input Bar */}
        <div className="relative max-w-2xl">
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            placeholder="Search shows, episodes, topics (e.g. Moti, Patang, Math)..."
            className="w-full pl-12 pr-10 py-3 rounded-2xl bg-slate-900/80 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 shadow-xl"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Control Bars */}
      <div className="space-y-3 p-4 rounded-2xl bg-slate-900/50 border border-slate-800/80 backdrop-blur-sm">
        {/* Language Filter */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1 mr-1">
            <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
            <span>Audio Language:</span>
          </span>
          {[
            { label: "All Languages", value: "" },
            { label: "English (en)", value: "en" },
            { label: "Hindi (hi)", value: "hi" }
          ].map((lang) => (
            <button
              key={lang.value}
              onClick={() => {
                setSelectedLanguage(lang.value);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                selectedLanguage === lang.value
                  ? "bg-indigo-600 text-white border-indigo-500 shadow-sm"
                  : "bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              {lang.label}
            </button>
          ))}

          {/* Section Filter dropdown */}
          <div className="sm:ml-auto">
            <select
              value={selectedSection}
              onChange={(e) => {
                setSelectedSection(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-950/60 text-slate-300 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            >
              <option value="">All Sections</option>
              {REFERENCE_SECTIONS.map((sec) => (
                <option key={sec.key} value={sec.key}>
                  {sec.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Categories Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/60">
          <button
            onClick={() => {
              setSelectedCategory("");
              setPage(1);
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
              selectedCategory === ""
                ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                : "bg-slate-950/40 text-slate-400 border-slate-800 hover:text-slate-300"
            }`}
          >
            All Themes
          </button>
          {REFERENCE_CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => {
                  setSelectedCategory(isSelected ? "" : cat);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                  isSelected
                    ? "bg-indigo-600 text-white border-indigo-500 shadow-xs"
                    : "bg-slate-950/40 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-300"
                }`}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results Header */}
      {data && (
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div>
            Found <span className="font-semibold text-slate-200">{data.total}</span>{" "}
            {data.total === 1 ? "show" : "shows"}
          </div>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              <span>Reset All Filters</span>
            </button>
          )}
        </div>
      )}

      {/* Results Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 animate-pulse">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="aspect-[2/3] w-full rounded-xl bg-slate-900 border border-slate-800" />
              <div className="h-4 bg-slate-800 rounded w-3/4" />
              <div className="h-3 bg-slate-800/60 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="py-16 text-center text-rose-400 space-y-3">
          <AlertCircle className="w-8 h-8 mx-auto" />
          <p className="font-semibold text-sm">Search failed: {(error as any)?.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-1.5 rounded-lg bg-rose-500/20 text-xs font-semibold text-rose-200 border border-rose-500/30"
          >
            Retry Search
          </button>
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="py-16 text-center space-y-3">
          <Film className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-300">No shows matched your search</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Try adjusting your search terms, changing category filters, or switching audio language.
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-2 px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold border border-indigo-500/30 transition-all"
            >
              Clear All Filters
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {data?.items.map((item) => (
            <Link key={item.id} href={`/shows/${item.slug}`}>
              <a className="group flex flex-col transition-transform duration-200 hover:-translate-y-1">
                {/* Poster 2:3 */}
                <div className="relative overflow-hidden rounded-xl shadow-lg border border-slate-800/80 group-hover:border-indigo-500/50 transition-all">
                  <ImageWithFallback
                    src={item.artwork?.poster}
                    alt={item.title}
                    aspectRatio="2:3"
                    fallbackTitle={item.title}
                  />

                  {/* Languages overlay */}
                  <div className="absolute top-2 right-2 flex gap-1">
                    {item.languages?.map((lang) => (
                      <span
                        key={lang}
                        className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-slate-950/80 backdrop-blur-xs text-indigo-300 border border-slate-700/60"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>

                  {/* Episode count */}
                  <div className="absolute bottom-2 left-2 flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-xs text-[10px] font-semibold text-slate-300">
                    <Layers className="w-3 h-3 text-indigo-400" />
                    <span>{item.episode_count} eps</span>
                  </div>
                </div>

                {/* Title & Metadata */}
                <div className="mt-2 px-0.5">
                  <h4 className="font-semibold text-xs text-slate-100 group-hover:text-indigo-400 transition-colors line-clamp-1">
                    {item.title}
                  </h4>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {item.categories?.slice(0, 2).map((cat) => (
                      <span
                        key={cat}
                        className="text-[10px] text-slate-400 font-medium capitalize"
                      >
                        #{cat}
                      </span>
                    ))}
                  </div>

                  {/* Matched Episode Title Badge */}
                  {item.matched_episodes && item.matched_episodes.length > 0 && (
                    <div className="mt-1.5 p-1 rounded bg-indigo-950/60 border border-indigo-800/50 text-[10px] text-indigo-300 line-clamp-1">
                      Matched: {item.matched_episodes[0]}
                    </div>
                  )}
                </div>
              </a>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
