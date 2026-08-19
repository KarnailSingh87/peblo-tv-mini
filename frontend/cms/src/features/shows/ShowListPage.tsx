import React, { useState } from "react";
import { Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Plus,
  Filter,
  Film,
  Layers,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  AlertCircle,
  Clock,
  Globe2
} from "lucide-react";
import { api } from "../../services/api";
import { ALLOWED_SECTIONS, ALLOWED_CATEGORIES } from "../../types";

export const ShowListPage: React.FC = () => {
  const [search, setSearch] = useState("");
  const [sectionFilter, setSectionFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ["shows", page, search, sectionFilter, statusFilter, categoryFilter],
    queryFn: () =>
      api.listShows({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        section: sectionFilter || undefined,
        status: statusFilter || undefined,
        category: categoryFilter || undefined
      })
  });

  return (
    <div className="p-8 max-w-7xl w-full mx-auto space-y-6">
      {/* Top Title & CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Streaming Catalogue Shows</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage show metadata, seasons, language variants, and artwork assets.
          </p>
        </div>
        <Link href="/admin/shows/new">
          <a className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/25 transition-all">
            <Plus className="w-4 h-4" />
            <span>Create New Show</span>
          </a>
        </Link>
      </div>

      {/* Filter Controls Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 backdrop-blur-md shadow-xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by title, slug..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          />
        </div>

        {/* Section Dropdown */}
        <div>
          <select
            value={sectionFilter}
            onChange={(e) => {
              setSectionFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3.5 py-2 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          >
            <option value="">All Sections</option>
            {ALLOWED_SECTIONS.map((sec) => (
              <option key={sec} value={sec}>
                {sec.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Status Dropdown */}
        <div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3.5 py-2 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          >
            <option value="">All Statuses</option>
            <option value="published">Published Only</option>
            <option value="draft">Draft Only</option>
          </select>
        </div>

        {/* Category Dropdown */}
        <div>
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3.5 py-2 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          >
            <option value="">All Categories</option>
            {ALLOWED_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Shows Data Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-md shadow-2xl">
        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm font-medium">Loading shows catalog...</p>
          </div>
        ) : isError ? (
          <div className="p-12 flex flex-col items-center justify-center text-rose-400 text-center gap-2">
            <AlertCircle className="w-8 h-8" />
            <p className="font-semibold text-base">Failed to load shows</p>
            <p className="text-xs text-rose-300/80">{(error as any)?.message}</p>
            <button
              onClick={() => refetch()}
              className="mt-3 px-4 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-xs font-semibold text-rose-200 border border-rose-500/30"
            >
              Retry
            </button>
          </div>
        ) : data?.items?.length === 0 ? (
          <div className="p-16 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
              <Film className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-200">No shows found</h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              Try adjusting your search criteria or create a brand new show.
            </p>
            <Link href="/admin/shows/new">
              <a className="mt-4 inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-xs font-semibold text-indigo-300 border border-indigo-500/30">
                <Plus className="w-4 h-4" />
                <span>Create New Show</span>
              </a>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-950/40 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  <th className="py-3.5 px-6">Show Title & Slug</th>
                  <th className="py-3.5 px-4">Section</th>
                  <th className="py-3.5 px-4">Categories</th>
                  <th className="py-3.5 px-4">Episodes</th>
                  <th className="py-3.5 px-4">Languages</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {data?.items.map((show) => (
                  <tr
                    key={show.id}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    {/* Title & Slug */}
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors">
                        {show.title}
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-0.5">{show.slug}</div>
                    </td>

                    {/* Section */}
                    <td className="py-4 px-4">
                      {show.section ? (
                        <span className="inline-block px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
                          {show.section}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 italic">None</span>
                      )}
                    </td>

                    {/* Categories */}
                    <td className="py-4 px-4">
                      <div className="flex flex-wrap gap-1 max-w-[200px]">
                        {show.categories?.slice(0, 3).map((cat) => (
                          <span
                            key={cat}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700/60"
                          >
                            {cat}
                          </span>
                        ))}
                        {(show.categories?.length || 0) > 3 && (
                          <span className="text-[11px] text-slate-400 font-medium">
                            +{show.categories.length - 3}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Episodes Count */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span className="font-semibold">{show.episode_count}</span>
                        <span className="text-slate-400">eps</span>
                      </div>
                    </td>

                    {/* Languages */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1">
                        {show.languages?.map((lang) => (
                          <span
                            key={lang}
                            className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700"
                          >
                            {lang}
                          </span>
                        ))}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-4 px-4">
                      {show.status === "published" ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          Published
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          <Clock className="w-3 h-3" />
                          Draft
                        </span>
                      )}
                    </td>

                    {/* Action Button */}
                    <td className="py-4 px-6 text-right">
                      <Link href={`/admin/shows/${show.id}`}>
                        <a className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-xs font-medium text-slate-200 border border-slate-700 hover:border-indigo-500 transition-all">
                          <span>Manage</span>
                        </a>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {data && data.total_pages > 1 && (
          <div className="py-3 px-6 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing <span className="font-semibold text-slate-200">{(page - 1) * pageSize + 1}</span> to{" "}
              <span className="font-semibold text-slate-200">
                {Math.min(page * pageSize, data.total)}
              </span>{" "}
              of <span className="font-semibold text-slate-200">{data.total}</span> shows
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-medium text-slate-300">
                Page {page} of {data.total_pages}
              </span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="p-1.5 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
