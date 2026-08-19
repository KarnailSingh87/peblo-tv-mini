import React, { useState } from "react";
import { useRoute, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Play,
  Clock,
  Globe2,
  Layers,
  Sparkles,
  PlaySquare,
  Volume2,
  AlertCircle
} from "lucide-react";
import { viewerApi } from "../../services/api";
import { ImageWithFallback } from "../../components/ImageWithFallback";
import { CatalogueEpisodeGroup, CatalogueShow } from "../../types";

export const ShowDetailPage: React.FC = () => {
  const [, params] = useRoute("/shows/:slug");
  const slug = params?.slug || "";

  const [selectedSeasonNum, setSelectedSeasonNum] = useState<number>(1);
  const [preferredLang, setPreferredLang] = useState<string>("en");

  const { data: catalog, isLoading, isError } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => viewerApi.getCatalog()
  });

  const allShows = catalog?.sections ? Object.values(catalog.sections).flat() : [];
  const show: CatalogueShow | undefined = allShows.find((s) => s.slug === slug);

  // Filter regular seasons (Season 0 trailers are excluded from regular seasons)
  const regularSeasons = (show?.seasons || []).filter((s) => s.season_number > 0);
  const currentSeason =
    regularSeasons.find((s) => s.season_number === selectedSeasonNum) || regularSeasons[0];

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        <div className="w-full h-80 rounded-3xl bg-slate-900 border border-slate-800" />
        <div className="space-y-4">
          <div className="w-48 h-8 rounded-lg bg-slate-800" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-44 rounded-2xl bg-slate-900 border border-slate-800" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !show) {
    return (
      <div className="max-w-xl mx-auto my-20 p-8 rounded-3xl bg-slate-900/60 border border-slate-800 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Show Not Found</h2>
        <p className="text-sm text-slate-400">
          The show "{slug}" is not currently in the published streaming catalogue.
        </p>
        <Link href="/">
          <a className="inline-block px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold">
            Back to Home
          </a>
        </Link>
      </div>
    );
  }

  const totalEpisodes = (show.seasons || []).reduce(
    (acc, s) => acc + (s.episodes?.length || 0),
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-10">
      {/* Top Back Link */}
      <Link href="/">
        <a className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalogue</span>
        </a>
      </Link>

      {/* Hero Showcase Card */}
      <div className="relative w-full rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl p-6 sm:p-10">
        {/* Backdrop Banner Graphic */}
        {show.artwork?.banner && (
          <img
            src={show.artwork.banner}
            alt={show.title}
            className="absolute inset-0 w-full h-full object-cover object-center opacity-25 filter blur-xs"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-slate-950/60" />

        <div className="relative z-10 flex flex-col md:flex-row items-start gap-8">
          {/* Vertical Poster 2:3 */}
          <div className="w-48 sm:w-56 shrink-0 shadow-2xl rounded-2xl overflow-hidden border border-slate-700/80">
            <ImageWithFallback
              src={show.artwork?.poster}
              alt={show.title}
              aspectRatio="2:3"
              fallbackTitle={show.title}
            />
          </div>

          {/* Show Details */}
          <div className="space-y-4 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              {show.section && (
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
                  {show.section}
                </span>
              )}
              {show.categories?.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800/80 text-slate-300 border border-slate-700/60"
                >
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </span>
              ))}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              {show.title}
            </h1>

            {show.synopsis && (
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                {show.synopsis}
              </p>
            )}

            {/* Quick Metadata */}
            <div className="flex flex-wrap items-center gap-6 pt-2 text-xs font-semibold text-slate-300">
              <div className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>{regularSeasons.length} Seasons</span>
              </div>
              <div className="flex items-center gap-1.5">
                <PlaySquare className="w-4 h-4 text-indigo-400" />
                <span>{totalEpisodes} Episodes</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Volume2 className="w-4 h-4 text-indigo-400" />
                <span>
                  Audio: {show.available_languages?.map((l) => l.toUpperCase()).join(", ") || "EN"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TRAILERS & PREVIEWS SECTION (Season 0 isolation) */}
      {show.trailers && show.trailers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <PlaySquare className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Trailers & Bonus Clips</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {show.trailers.map((trailer) => {
              const activeVariant =
                trailer.variants[preferredLang] ||
                trailer.variants[trailer.available_languages[0]] ||
                Object.values(trailer.variants)[0];

              return (
                <div
                  key={trailer.content_group}
                  className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50">
                        Official Trailer
                      </span>
                      <h4 className="font-bold text-sm text-slate-100 mt-2 group-hover:text-indigo-300 transition-colors">
                        {activeVariant?.episode_title || "Official Preview"}
                      </h4>
                    </div>
                    {trailer.duration_seconds && (
                      <span className="text-xs text-slate-400 flex items-center gap-1 shrink-0">
                        <Clock className="w-3 h-3" />
                        <span>{trailer.duration_seconds}s</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                    <span className="text-slate-400 text-[11px]">
                      Languages: {trailer.available_languages.map((l) => l.toUpperCase()).join(", ")}
                    </span>
                    <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-xs transition-all">
                      <Play className="w-3 h-3 fill-white" />
                      <span>Watch Trailer</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SEASONS & EPISODES BROWSER */}
      <div className="space-y-6">
        {/* Season Tabs & Global Audio Switcher */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          {/* Season Switcher */}
          <div className="flex flex-wrap items-center gap-2">
            {regularSeasons.map((season) => (
              <button
                key={season.season_number}
                onClick={() => setSelectedSeasonNum(season.season_number)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  (currentSeason?.season_number || 1) === season.season_number
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/25"
                    : "bg-slate-900/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
                }`}
              >
                <span>Season {season.season_number}</span>
                <span className="ml-1.5 text-[11px] opacity-80">
                  ({season.episodes?.length || 0})
                </span>
              </button>
            ))}
          </div>

          {/* Global Audio Language Preference Toggle */}
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-xl self-start sm:self-auto">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
              <Globe2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Audio:</span>
            </span>
            <button
              onClick={() => setPreferredLang("en")}
              className={`px-2.5 py-0.5 rounded-md text-xs font-bold uppercase transition-all ${
                preferredLang === "en"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              English (en)
            </button>
            <button
              onClick={() => setPreferredLang("hi")}
              className={`px-2.5 py-0.5 rounded-md text-xs font-bold uppercase transition-all ${
                preferredLang === "hi"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Hindi (hi)
            </button>
          </div>
        </div>

        {/* Episode Cards Grid */}
        {currentSeason?.episodes?.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <p className="text-sm font-semibold">No episodes released in Season {currentSeason.season_number}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {currentSeason?.episodes?.map((epGroup: CatalogueEpisodeGroup) => {
              // Select active localized title for preferred language, or fallback to first available
              const activeVariant =
                epGroup.variants[preferredLang] ||
                epGroup.variants[epGroup.available_languages[0]] ||
                Object.values(epGroup.variants)[0];

              const durationMin = epGroup.duration_seconds
                ? Math.floor(epGroup.duration_seconds / 60)
                : null;
              const durationSec = epGroup.duration_seconds
                ? epGroup.duration_seconds % 60
                : null;

              return (
                <div
                  key={epGroup.content_group}
                  className="rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/40 p-4 shadow-xl backdrop-blur-xs transition-all flex flex-col justify-between group"
                >
                  {/* Thumbnail 16:9 */}
                  <div className="relative overflow-hidden rounded-xl border border-slate-800 mb-3">
                    <ImageWithFallback
                      src={epGroup.artwork?.thumbnail}
                      alt={activeVariant?.episode_title || "Episode"}
                      aspectRatio="16:9"
                      fallbackTitle={activeVariant?.episode_title}
                    />

                    {/* Episode Number badge */}
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-xs text-[10px] font-bold text-white">
                      Episode {epGroup.episode_number}
                    </div>

                    {/* Play Button Overlay */}
                    <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg shadow-indigo-600/40 group-hover:scale-110 transition-transform">
                        <Play className="w-5 h-5 fill-white ml-0.5" />
                      </div>
                    </div>
                  </div>

                  {/* Title & Metadata */}
                  <div className="space-y-1.5">
                    <h4 className="font-bold text-sm text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
                      {activeVariant?.episode_title || `Episode ${epGroup.episode_number}`}
                    </h4>

                    <div className="flex items-center justify-between text-xs text-slate-400">
                      {durationMin !== null ? (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>{durationMin}m {durationSec}s</span>
                        </span>
                      ) : (
                        <span>Standard Runtime</span>
                      )}

                      {/* Multilingual Variant Pill */}
                      <div className="flex items-center gap-1">
                        {epGroup.available_languages.map((l) => (
                          <button
                            key={l}
                            onClick={(e) => {
                              e.stopPropagation();
                              setPreferredLang(l);
                            }}
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase transition-colors ${
                              preferredLang === l
                                ? "bg-indigo-600 text-white"
                                : "bg-slate-800 text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            {l}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
