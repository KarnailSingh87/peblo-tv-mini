import React from "react";
import { Link } from "wouter";
import { Layers } from "lucide-react";
import { CatalogueShow } from "../types";
import { ImageWithFallback } from "./ImageWithFallback";

interface ShowCardProps {
  show: CatalogueShow;
}

export const ShowCard: React.FC<ShowCardProps> = ({ show }) => {
  const totalEpisodes = (show.seasons || []).reduce(
    (acc, s) => acc + (s.episodes?.length || 0),
    0
  );

  return (
    <Link href={`/shows/${show.slug}`}>
      <a className="group block w-44 shrink-0 transition-transform duration-200 hover:-translate-y-1">
        {/* Poster 2:3 */}
        <div className="relative overflow-hidden rounded-xl shadow-lg border border-slate-800/80 group-hover:border-indigo-500/50 group-hover:shadow-indigo-500/10 transition-all">
          <ImageWithFallback
            src={show.artwork?.poster}
            alt={show.title}
            aspectRatio="2:3"
            fallbackTitle={show.title}
          />

          {/* Overlay Language Badges */}
          <div className="absolute top-2 right-2 flex gap-1">
            {show.available_languages?.map((lang) => (
              <span
                key={lang}
                className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-slate-950/80 backdrop-blur-xs text-indigo-300 border border-slate-700/60"
              >
                {lang}
              </span>
            ))}
          </div>

          {/* Bottom Episode count badge */}
          <div className="absolute bottom-2 left-2 flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-xs text-[10px] font-semibold text-slate-300">
            <Layers className="w-3 h-3 text-indigo-400" />
            <span>{totalEpisodes} {totalEpisodes === 1 ? "ep" : "eps"}</span>
          </div>
        </div>

        {/* Title & Metadata */}
        <div className="mt-2.5 px-0.5">
          <h4 className="font-semibold text-sm text-slate-100 group-hover:text-indigo-400 transition-colors line-clamp-1">
            {show.title}
          </h4>
          <div className="flex flex-wrap gap-1 mt-1">
            {show.categories?.slice(0, 2).map((cat) => (
              <span
                key={cat}
                className="text-[10px] text-slate-400 font-medium capitalize"
              >
                #{cat}
              </span>
            ))}
          </div>
        </div>
      </a>
    </Link>
  );
};
