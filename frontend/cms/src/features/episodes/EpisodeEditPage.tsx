import React, { useState } from "react";
import { useRoute, Link, useLocation } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Save,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Film,
  Layers,
  Clock
} from "lucide-react";
import { api } from "../../services/api";
import { ArtworkUploadSlot } from "../../components/ArtworkUploadSlot";

export const EpisodeEditPage: React.FC = () => {
  const [, params] = useRoute("/admin/episodes/:id");
  const [, setLocation] = useLocation();
  const episodeId = params?.id || "";
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [episodeNumber, setEpisodeNumber] = useState<number>(1);
  const [durationSeconds, setDurationSeconds] = useState<number | string>("");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [contentGroup, setContentGroup] = useState("");
  const [status, setStatus] = useState<"draft" | "published">("draft");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const { data: episode, isLoading, isError } = useQuery({
    queryKey: ["episode", episodeId],
    queryFn: () => api.getEpisode(episodeId),
    enabled: !!episodeId
  });

  React.useEffect(() => {
    if (episode) {
      setTitle(episode.episode_title);
      setEpisodeNumber(episode.episode_number);
      setDurationSeconds(episode.duration_seconds || "");
      setLanguage(episode.language);
      setContentGroup(episode.content_group);
      setStatus(episode.status);
    }
  }, [episode]);

  const updateMutation = useMutation({
    mutationFn: () =>
      api.updateEpisode(episodeId, {
        episode_title: title.trim(),
        episode_number: episodeNumber,
        duration_seconds: durationSeconds ? parseInt(durationSeconds.toString()) : null,
        language,
        content_group: contentGroup.trim(),
        status
      }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["episode", episodeId] });
      queryClient.invalidateQueries({ queryKey: ["show", updated.show_id] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setFeedback({ type: "success", message: "Episode updated successfully!" });
    },
    onError: (err: any) => {
      setFeedback({ type: "error", message: err.message || "Failed to update episode." });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteEpisode(episodeId),
    onSuccess: () => {
      if (episode?.show_id) {
        queryClient.invalidateQueries({ queryKey: ["show", episode.show_id] });
        queryClient.invalidateQueries({ queryKey: ["validationReport"] });
        setLocation(`/admin/shows/${episode.show_id}`);
      } else {
        setLocation("/admin/shows");
      }
    }
  });

  if (isLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">Loading episode...</p>
      </div>
    );
  }

  if (isError || !episode) {
    return (
      <div className="p-12 text-center text-rose-400">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">Episode not found.</p>
        <Link href="/admin/shows">
          <a className="mt-4 inline-block px-4 py-2 rounded-xl bg-slate-800 text-xs font-semibold text-slate-200">
            Back to Shows
          </a>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl w-full mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/admin/shows/${episode.show_id}`}>
          <a className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </a>
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Edit Episode {episode.episode_number}: {episode.episode_title}
            </h1>
            {episode.custom_id && (
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-xs font-mono border border-slate-700">
                {episode.custom_id}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure audio language, content group key, and 16:9 thumbnail artwork.
          </p>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Form Settings (2 Cols) */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            updateMutation.mutate();
          }}
          className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-5"
        >
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Episode Title <span className="text-indigo-400">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Episode Order / Number
              </label>
              <input
                type="number"
                min={0}
                required
                value={episodeNumber}
                onChange={(e) => setEpisodeNumber(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Duration (Seconds)
              </label>
              <input
                type="number"
                min={1}
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(e.target.value)}
                placeholder="e.g. 500"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Audio Language Track
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as "en" | "hi")}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              >
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as "draft" | "published")}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              >
                <option value="draft">Draft (Hidden)</option>
                <option value="published">Published (Live in Catalogue)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Content Group Key <span className="text-indigo-400">*</span>
            </label>
            <input
              type="text"
              required
              value={contentGroup}
              onChange={(e) => setContentGroup(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
            <p className="text-xs text-slate-400 mt-1">
              Episodes sharing this key in English and Hindi collapse into one single catalogue entry with language selection.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => {
                if (confirm(`Delete episode "${episode.episode_title}"?`)) {
                  deleteMutation.mutate();
                }
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-semibold border border-rose-500/20 transition-all"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>

            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{updateMutation.isPending ? "Saving..." : "Save Episode"}</span>
            </button>
          </div>
        </form>

        {/* Right Column: Thumbnail Upload (1 Col) */}
        <div className="space-y-4">
          <ArtworkUploadSlot
            artworkType="thumbnail"
            entityType="episode"
            entityId={episode.id}
          />
        </div>
      </div>
    </div>
  );
};
