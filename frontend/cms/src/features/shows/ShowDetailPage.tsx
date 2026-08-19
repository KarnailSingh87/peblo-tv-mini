import React, { useState } from "react";
import { useRoute, Link, useLocation } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Save,
  Trash2,
  Plus,
  Layers,
  Film,
  AlertCircle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Sparkles,
  ChevronRight,
  PlaySquare
} from "lucide-react";
import { api } from "../../services/api";
import { ArtworkUploadSlot } from "../../components/ArtworkUploadSlot";
import { ALLOWED_SECTIONS, ALLOWED_CATEGORIES, ALLOWED_LANGUAGES } from "../../types";

export const ShowDetailPage: React.FC = () => {
  const [, params] = useRoute("/admin/shows/:id");
  const [, setLocation] = useLocation();
  const showId = params?.id || "";
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<"content" | "artwork" | "settings">("content");
  const [selectedSeasonNum, setSelectedSeasonNum] = useState<number>(1);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Quick Episode Modal State
  const [isAddEpOpen, setIsAddEpOpen] = useState(false);
  const [epTargetSeasonId, setEpTargetSeasonId] = useState<string>("");
  const [epTitle, setEpTitle] = useState("");
  const [epNumber, setEpNumber] = useState(1);
  const [epDuration, setEpDuration] = useState<number>(300);
  const [epLang, setEpLang] = useState<"en" | "hi">("en");
  const [epContentGroup, setEpContentGroup] = useState("");
  const [epStatus, setEpStatus] = useState<"draft" | "published">("draft");

  // Show Details Query
  const { data: show, isLoading, isError, error } = useQuery({
    queryKey: ["show", showId],
    queryFn: () => api.getShow(showId),
    enabled: !!showId
  });

  // Show Form State
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [section, setSection] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);
  const [synopsis, setSynopsis] = useState("");
  const [status, setStatus] = useState<"draft" | "published">("draft");

  // Sync state when query data loads
  React.useEffect(() => {
    if (show) {
      setTitle(show.title);
      setSlug(show.slug);
      setSection(show.section || "");
      setCategories(show.categories || []);
      setSynopsis(show.synopsis || "");
      setStatus(show.status);
    }
  }, [show]);

  // Update Show Mutation
  const updateShowMutation = useMutation({
    mutationFn: () =>
      api.updateShow(showId, {
        title,
        slug,
        section: section || null,
        categories,
        synopsis: synopsis || null,
        status
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["show", showId] });
      queryClient.invalidateQueries({ queryKey: ["shows"] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setFeedback({ type: "success", message: "Show settings updated successfully!" });
    },
    onError: (err: any) => {
      setFeedback({ type: "error", message: err.message || "Failed to update show." });
    }
  });

  // Delete Show Mutation
  const deleteShowMutation = useMutation({
    mutationFn: () => api.deleteShow(showId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shows"] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setLocation("/admin/shows");
    }
  });

  // Add Season Mutation
  const addSeasonMutation = useMutation({
    mutationFn: (nextNum: number) =>
      api.createShowSeason(showId, {
        season_number: nextNum,
        title: `Season ${nextNum}`
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["show", showId] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setFeedback({ type: "success", message: "New season created!" });
    }
  });

  // Create Episode Mutation
  const createEpisodeMutation = useMutation({
    mutationFn: () =>
      api.createSeasonEpisode(epTargetSeasonId, {
        episode_title: epTitle.trim(),
        episode_number: epNumber,
        duration_seconds: epDuration > 0 ? epDuration : null,
        language: epLang,
        content_group: epContentGroup.trim(),
        status: epStatus
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["show", showId] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setIsAddEpOpen(false);
      setEpTitle("");
      setEpContentGroup("");
      setFeedback({ type: "success", message: "Episode created successfully!" });
    },
    onError: (err: any) => {
      setFeedback({ type: "error", message: err.message || "Failed to create episode." });
    }
  });

  const toggleCategory = (cat: string) => {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleOpenAddEpisode = (seasonId: string, sNum: number, nextEpNum: number) => {
    setEpTargetSeasonId(seasonId);
    setEpNumber(nextEpNum);
    setEpContentGroup(`${slug}-s0${sNum}e0${nextEpNum}`);
    setIsAddEpOpen(true);
  };

  if (isLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">Loading show details...</p>
      </div>
    );
  }

  if (isError || !show) {
    return (
      <div className="p-12 text-center text-rose-400">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">Show not found or failed to load.</p>
        <Link href="/admin/shows">
          <a className="mt-4 inline-block px-4 py-2 rounded-xl bg-slate-800 text-xs font-semibold text-slate-200">
            Back to Shows
          </a>
        </Link>
      </div>
    );
  }

  const seasonsList = show.seasons || [];
  const trailerSeason = seasonsList.find((s) => s.season_number === 0);
  const regularSeasons = seasonsList
    .filter((s) => s.season_number > 0)
    .sort((a, b) => a.season_number - b.season_number);
  const currentSeason =
    regularSeasons.find((s) => s.season_number === selectedSeasonNum) || regularSeasons[0];

  return (
    <div className="p-8 max-w-7xl w-full mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <Link href="/admin/shows">
            <a className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all">
              <ArrowLeft className="w-5 h-5" />
            </a>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">{show.title}</h1>
              {show.status === "published" ? (
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Live
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Draft
                </span>
              )}
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">{show.slug}</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800">
          <button
            onClick={() => setActiveTab("content")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "content"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Seasons & Episodes
          </button>
          <button
            onClick={() => setActiveTab("artwork")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "artwork"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Artwork Assets
          </button>
          <button
            onClick={() => setActiveTab("settings")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "settings"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Show Settings
          </button>
        </div>
      </div>

      {feedback && (
        <div
          className={`flex items-center gap-2 p-3.5 rounded-xl text-xs font-medium border ${
            feedback.type === "success"
              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/15 border-rose-500/30 text-rose-300"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* TAB 1: SEASONS & EPISODES MANAGER */}
      {activeTab === "content" && (
        <div className="space-y-6">
          {/* Season 0: Trailers Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <PlaySquare className="w-5 h-5 text-indigo-400" />
                <h3 className="font-semibold text-slate-100 text-base">Season 0 (Trailers & Previews)</h3>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Trailer content only • Excluded from regular viewer seasons
                </span>
              </div>
              {trailerSeason && (
                <button
                  type="button"
                  onClick={() =>
                    handleOpenAddEpisode(
                      trailerSeason.id,
                      0,
                      (trailerSeason.episodes?.length || 0) + 1
                    )
                  }
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold border border-indigo-500/30 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Trailer</span>
                </button>
              )}
            </div>

            {trailerSeason?.episodes?.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-2">No trailer clips uploaded yet.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {trailerSeason?.episodes?.map((ep) => (
                  <div
                    key={ep.id}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 flex items-center justify-between group transition-all"
                  >
                    <div>
                      <h5 className="font-semibold text-xs text-slate-200 group-hover:text-indigo-300 transition-colors">
                        {ep.episode_title}
                      </h5>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {ep.duration_seconds ? `${ep.duration_seconds}s` : "No duration"} •{" "}
                        <span className="uppercase font-bold text-slate-300">{ep.language}</span>
                      </p>
                    </div>
                    <Link href={`/admin/episodes/${ep.id}`}>
                      <a className="px-2.5 py-1 rounded bg-slate-800 text-[11px] text-slate-300 hover:bg-indigo-600 hover:text-white transition-all">
                        Edit
                      </a>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Numbered Seasons Navigation & Episode List */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-5">
            {/* Season Tabs and Add Season */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-2">
                {regularSeasons.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSelectedSeasonNum(s.season_number)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                      (currentSeason?.season_number || 1) === s.season_number
                        ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    <span>Season {s.season_number}</span>
                    <span className="ml-1.5 text-[10px] opacity-80">
                      ({s.episodes?.length || 0})
                    </span>
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => {
                    const nextNum =
                      regularSeasons.length > 0
                        ? Math.max(...regularSeasons.map((s) => s.season_number)) + 1
                        : 1;
                    addSeasonMutation.mutate(nextNum);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-700/60 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Season</span>
                </button>
              </div>

              {currentSeason && (
                <button
                  type="button"
                  onClick={() =>
                    handleOpenAddEpisode(
                      currentSeason.id,
                      currentSeason.season_number,
                      (currentSeason.episodes?.length || 0) + 1
                    )
                  }
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Episode to Season {currentSeason.season_number}</span>
                </button>
              )}
            </div>

            {/* Episode Rows Table */}
            {currentSeason?.episodes?.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <Layers className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <p className="text-sm font-semibold text-slate-300">No episodes in Season {currentSeason.season_number}</p>
                <p className="text-xs text-slate-400 mt-0.5">Add English or Hindi episode tracks to this season.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800/80 bg-slate-950/40 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      <th className="py-3 px-4">#</th>
                      <th className="py-3 px-4">Episode Title</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Language</th>
                      <th className="py-3 px-4">Content Group</th>
                      <th className="py-3 px-4">Artwork</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {currentSeason?.episodes?.map((ep) => (
                      <tr key={ep.id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-400 font-semibold">
                          E{ep.episode_number}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors">
                          {ep.episode_title}
                          {ep.custom_id && (
                            <span className="ml-2 text-[10px] font-mono text-slate-400 font-normal">
                              ({ep.custom_id})
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-300">
                          {ep.duration_seconds ? (
                            <span>{Math.floor(ep.duration_seconds / 60)}m {ep.duration_seconds % 60}s</span>
                          ) : (
                            <span className="text-rose-400 font-medium">Missing</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-200 border border-slate-700">
                            {ep.language}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                          {ep.content_group}
                        </td>
                        <td className="py-3.5 px-4">
                          {ep.artwork_available && ep.artwork_available.length > 0 ? (
                            <span className="text-emerald-400 text-xs font-medium flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Available</span>
                            </span>
                          ) : (
                            <span className="text-amber-400 text-xs font-medium flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              <span>No Artwork</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {ep.status === "published" ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                              Published
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                              Draft
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <Link href={`/admin/episodes/${ep.id}`}>
                            <a className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-xs font-medium text-slate-200 border border-slate-700 transition-all">
                              <span>Edit Episode</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </a>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: ARTWORK ASSETS */}
      {activeTab === "artwork" && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1">Show Visual Assets</h3>
            <p className="text-xs text-slate-400 mb-6">
              Upload promotional artwork for homepage banner displays and show catalogue cards.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ArtworkUploadSlot
                artworkType="poster"
                entityType="show"
                entityId={show.id}
              />
              <ArtworkUploadSlot
                artworkType="banner"
                entityType="show"
                entityId={show.id}
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: SHOW SETTINGS */}
      {activeTab === "settings" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            updateShowMutation.mutate();
          }}
          className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Show Title
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                URL Slug
              </label>
              <input
                type="text"
                required
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Homepage Section
              </label>
              <select
                value={section}
                onChange={(e) => setSection(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              >
                <option value="">Unassigned (Draft Only)</option>
                {ALLOWED_SECTIONS.map((sec) => (
                  <option key={sec} value={sec}>
                    {sec.toUpperCase()} Row
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Status
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setStatus("draft")}
                  className={`py-2.5 px-4 rounded-xl text-xs font-semibold border transition-all ${
                    status === "draft"
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                      : "bg-slate-950/40 text-slate-400 border-slate-700"
                  }`}
                >
                  Draft (Hidden)
                </button>
                <button
                  type="button"
                  onClick={() => setStatus("published")}
                  className={`py-2.5 px-4 rounded-xl text-xs font-semibold border transition-all ${
                    status === "published"
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-950/40 text-slate-400 border-slate-700"
                  }`}
                >
                  Published (Live)
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Categories & Themes
            </label>
            <div className="flex flex-wrap gap-2 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800">
              {ALLOWED_CATEGORIES.map((cat) => {
                const isSelected = categories.includes(cat);
                return (
                  <button
                    type="button"
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      isSelected
                        ? "bg-indigo-600/30 text-indigo-200 border-indigo-500"
                        : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Synopsis
            </label>
            <textarea
              rows={3}
              value={synopsis}
              onChange={(e) => setSynopsis(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => {
                if (confirm(`Are you sure you want to delete "${show.title}"? This cannot be undone.`)) {
                  deleteShowMutation.mutate();
                }
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-semibold border border-rose-500/20 transition-all"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Show</span>
            </button>

            <button
              type="submit"
              disabled={updateShowMutation.isPending}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{updateShowMutation.isPending ? "Saving Changes..." : "Save Settings"}</span>
            </button>
          </div>
        </form>
      )}

      {/* QUICK ADD EPISODE MODAL */}
      {isAddEpOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Add New Episode</h3>
              <button
                onClick={() => setIsAddEpOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createEpisodeMutation.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Episode Title <span className="text-indigo-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={epTitle}
                  onChange={(e) => setEpTitle(e.target.value)}
                  placeholder="e.g. The Lost Kite"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Episode Number <span className="text-indigo-400">*</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    required
                    value={epNumber}
                    onChange={(e) => setEpNumber(parseInt(e.target.value) || 1)}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Duration (Seconds)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={epDuration}
                    onChange={(e) => setEpDuration(parseInt(e.target.value) || 0)}
                    placeholder="e.g. 300"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Audio Language
                  </label>
                  <select
                    value={epLang}
                    onChange={(e) => setEpLang(e.target.value as "en" | "hi")}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="en">English (en)</option>
                    <option value="hi">Hindi (hi)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Status
                  </label>
                  <select
                    value={epStatus}
                    onChange={(e) => setEpStatus(e.target.value as "draft" | "published")}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Content Group Key <span className="text-indigo-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={epContentGroup}
                  onChange={(e) => setEpContentGroup(e.target.value)}
                  placeholder="e.g. moti-s01e01"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  English & Hindi audio variants share the exact same content group key to merge into one catalogue item.
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsAddEpOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createEpisodeMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md disabled:opacity-50"
                >
                  {createEpisodeMutation.isPending ? "Creating..." : "Save Episode"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
