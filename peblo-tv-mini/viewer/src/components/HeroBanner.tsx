import React from "react";
import { Link } from "wouter";
import { Play, Info, Sparkles, Volume2 } from "lucide-react";
import { CatalogueShow } from "../types";

interface HeroBannerProps {
  show: CatalogueShow;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({ show }) => {
  const totalEpisodes = (show.seasons || []).reduce(
    (acc, s) => acc + (s.episodes?.length || 0),
    0
  );

  return (
    <div className="relative w-full h-[460px] sm:h-[520px] rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl">
      {/* Background Banner Artwork */}
      {show.artwork?.banner ? (
        <img
          src={show.artwork.banner}
          alt={show.title}
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
      ) : (
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-950 via-slate-900 to-slate-950" />
      )}

      {/* Deep Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950/90 via-slate-950/40 to-transparent" />

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-10 max-w-2xl space-y-4">
        {/* Category and Section Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {show.section && (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
              {show.section}
            </span>
          )}
          {show.categories?.slice(0, 3).map((cat) => (
            <span
              key={cat}
              className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-900/80 backdrop-blur-xs text-slate-300 border border-slate-700/60"
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </span>
          ))}
        </div>

        {/* Title */}
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight drop-shadow-md">
          {show.title}
        </h1>

        {/* Synopsis */}
        {show.synopsis && (
          <p className="text-sm sm:text-base text-slate-300 line-clamp-2 leading-relaxed max-w-xl">
            {show.synopsis}
          </p>
        )}

        {/* Metadata & Actions */}
        <div className="flex flex-wrap items-center gap-4 pt-2">
          <Link href={`/shows/${show.slug}`}>
            <a className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold shadow-xl shadow-indigo-600/30 transition-all hover:scale-105">
              <Play className="w-4 h-4 fill-white" />
              <span>Watch Now</span>
            </a>
          </Link>

          <Link href={`/shows/${show.slug}`}>
            <a className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 text-sm font-semibold border border-slate-700/80 backdrop-blur-xs transition-all">
              <Info className="w-4 h-4" />
              <span>Show Details</span>
            </a>
          </Link>

          {/* Languages supported */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-medium ml-2">
            <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
            <span>Audio: {show.available_languages?.map((l) => l.toUpperCase()).join(", ") || "EN"}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
