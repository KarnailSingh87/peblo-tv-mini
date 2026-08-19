import React, { useState } from "react";
import { useLocation, Link } from "wouter";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Save, AlertCircle, Sparkles, Check } from "lucide-react";
import { api } from "../../services/api";
import { ALLOWED_SECTIONS, ALLOWED_CATEGORIES } from "../../types";

export const ShowCreatePage: React.FC = () => {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [autoSlug, setAutoSlug] = useState(true);
  const [section, setSection] = useState<string>("series");
  const [selectedCategories, setSelectedCategories] = useState<string[]>(["adventure"]);
  const [synopsis, setSynopsis] = useState("");
  const [status, setStatus] = useState<"draft" | "published">("draft");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-generate slug from title
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setTitle(val);
    if (autoSlug) {
      const generated = val
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)+/g, "");
      setSlug(generated);
    }
  };

  const toggleCategory = (cat: string) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  const createMutation = useMutation({
    mutationFn: () =>
      api.createShow({
        title: title.trim(),
        slug: slug.trim(),
        section: section || null,
        categories: selectedCategories,
        synopsis: synopsis.trim() || null,
        status
      }),
    onSuccess: (newShow) => {
      queryClient.invalidateQueries({ queryKey: ["shows"] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setLocation(`/admin/shows/${newShow.id}`);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to create show.");
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!title.trim()) {
      setErrorMsg("Please provide a show title.");
      return;
    }
    if (!slug.trim()) {
      setErrorMsg("Please provide a URL slug.");
      return;
    }
    if (status === "published" && !section) {
      setErrorMsg("A published show must have a homepage section assigned.");
      return;
    }

    createMutation.mutate();
  };

  return (
    <div className="p-8 max-w-4xl w-full mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center gap-4">
        <Link href="/admin/shows">
          <a className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </a>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Create New Show</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Add a new show entry. Season 0 (Trailers) and Season 1 will be initialized automatically.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Creation Error</p>
            <p className="text-rose-300/90 text-xs mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Form Card */}
      <form
        onSubmit={handleSubmit}
        className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-6"
      >
        {/* Title and Slug */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Show Title <span className="text-indigo-400">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={handleTitleChange}
              placeholder="e.g. Moti's Many Lives"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                URL Slug <span className="text-indigo-400">*</span>
              </label>
              <button
                type="button"
                onClick={() => setAutoSlug(!autoSlug)}
                className="text-[11px] text-indigo-400 hover:text-indigo-300"
              >
                {autoSlug ? "Manual Slug" : "Auto Slug"}
              </button>
            </div>
            <input
              type="text"
              required
              disabled={autoSlug}
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="e.g. motis-many-lives"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-60"
            />
          </div>
        </div>

        {/* Section and Status */}
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
              Initial Release Status
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setStatus("draft")}
                className={`py-2.5 px-4 rounded-xl text-xs font-semibold border transition-all ${
                  status === "draft"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm"
                    : "bg-slate-950/40 text-slate-400 border-slate-700 hover:border-slate-600"
                }`}
              >
                Draft (Hidden)
              </button>
              <button
                type="button"
                onClick={() => setStatus("published")}
                className={`py-2.5 px-4 rounded-xl text-xs font-semibold border transition-all ${
                  status === "published"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm"
                    : "bg-slate-950/40 text-slate-400 border-slate-700 hover:border-slate-600"
                }`}
              >
                Published (Live)
              </button>
            </div>
          </div>
        </div>

        {/* Categories Picker */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Categories & Themes (Allowed Reference Categories)
          </label>
          <div className="flex flex-wrap gap-2 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800">
            {ALLOWED_CATEGORIES.map((cat) => {
              const isSelected = selectedCategories.includes(cat);
              return (
                <button
                  type="button"
                  key={cat}
                  onClick={() => toggleCategory(cat)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                    isSelected
                      ? "bg-indigo-600/30 text-indigo-200 border-indigo-500 shadow-sm"
                      : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-300"
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3 text-indigo-400" />}
                  <span>{cat.charAt(0).toUpperCase() + cat.slice(1)}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Synopsis */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Synopsis / Storyline Summary
          </label>
          <textarea
            rows={3}
            value={synopsis}
            onChange={(e) => setSynopsis(e.target.value)}
            placeholder="Write a child-friendly synopsis for this show..."
            className="w-full px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          />
        </div>

        {/* Submit Buttons */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
          <Link href="/admin/shows">
            <a className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-all">
              Cancel
            </a>
          </Link>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{createMutation.isPending ? "Saving..." : "Create Show"}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
