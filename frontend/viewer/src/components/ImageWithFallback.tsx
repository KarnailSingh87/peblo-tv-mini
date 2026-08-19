import React, { useState } from "react";
import { Film, Image as ImageIcon } from "lucide-react";

interface ImageWithFallbackProps {
  src?: string | null;
  alt: string;
  aspectRatio: "2:3" | "16:9";
  className?: string;
  fallbackTitle?: string;
}

export const ImageWithFallback: React.FC<ImageWithFallbackProps> = ({
  src,
  alt,
  aspectRatio,
  className = "",
  fallbackTitle
}) => {
  const [loaded, setLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const aspectClass = aspectRatio === "2:3" ? "aspect-[2/3]" : "aspect-[16/9]";

  if (!src || hasError) {
    return (
      <div
        className={`w-full ${aspectClass} rounded-xl bg-gradient-to-br from-slate-800 via-indigo-950/50 to-slate-900 border border-slate-800 flex flex-col items-center justify-center p-3 text-center select-none overflow-hidden relative ${className}`}
      >
        <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-1.5 shadow-sm">
          <Film className="w-4 h-4" />
        </div>
        {fallbackTitle ? (
          <p className="text-xs font-semibold text-slate-300 line-clamp-2 px-1">{fallbackTitle}</p>
        ) : (
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Peblo TV</span>
        )}
      </div>
    );
  }

  return (
    <div className={`relative w-full ${aspectClass} overflow-hidden rounded-xl bg-slate-900 ${className}`}>
      {/* Loading Skeleton */}
      {!loaded && (
        <div className="absolute inset-0 bg-slate-800 animate-pulse flex items-center justify-center">
          <ImageIcon className="w-5 h-5 text-slate-600" />
        </div>
      )}

      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setHasError(true)}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
      />
    </div>
  );
};
