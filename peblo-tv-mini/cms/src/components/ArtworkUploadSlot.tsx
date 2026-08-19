import React, { useState, useRef } from "react";
import { Upload, CheckCircle2, AlertCircle, RefreshCw, Image as ImageIcon } from "lucide-react";
import { api } from "../services/api";

interface ArtworkUploadSlotProps {
  artworkType: "poster" | "banner" | "thumbnail";
  entityType: "show" | "episode";
  entityId: string;
  currentUrl?: string | null;
  onUploadSuccess?: (newUrl: string) => void;
}

const SPEC_MAP = {
  poster: {
    title: "Vertical Poster",
    aspect: "2:3",
    dimensions: "~600 × 900 px",
    minDim: "400 × 600 px",
    maxSize: "200 KB",
    previewClass: "aspect-[2/3] max-w-[180px]"
  },
  banner: {
    title: "Hero Banner",
    aspect: "16:9",
    dimensions: "~1280 × 720 px",
    minDim: "800 × 450 px",
    maxSize: "200 KB",
    previewClass: "aspect-[16/9] max-w-[320px]"
  },
  thumbnail: {
    title: "Episode Thumbnail",
    aspect: "16:9",
    dimensions: "~640 × 360 px",
    minDim: "480 × 270 px",
    maxSize: "200 KB",
    previewClass: "aspect-[16/9] max-w-[240px]"
  }
};

export const ArtworkUploadSlot: React.FC<ArtworkUploadSlotProps> = ({
  artworkType,
  entityType,
  entityId,
  currentUrl,
  onUploadSuccess
}) => {
  const spec = SPEC_MAP[artworkType];
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [preview, setPreview] = useState<string | null>(currentUrl || null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = async (file: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);

    // Initial check (200 KB warning)
    if (file.size > 200 * 1024) {
      setErrorMsg(`File is ${(file.size / 1024).toFixed(1)} KB. Maximum allowed size is 200 KB.`);
      return;
    }

    const formData = new FormData();
    formData.append("artwork_type", artworkType);
    formData.append("entity_type", entityType);
    formData.append("entity_id", entityId);
    formData.append("file", file);

    setIsUploading(true);
    try {
      const res = await api.uploadArtwork(formData);
      setPreview(res.url);
      setSuccessMsg("Artwork uploaded successfully!");
      if (onUploadSuccess) {
        onUploadSuccess(res.url);
      }
    } catch (err: any) {
      if (err.data?.detail?.reasons) {
        setErrorMsg(err.data.detail.reasons.join(" "));
      } else {
        setErrorMsg(err.message || "Failed to upload artwork.");
      }
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-semibold text-slate-100 text-sm">{spec.title}</h4>
          <p className="text-xs text-slate-400">
            Ratio <span className="text-indigo-400 font-medium">{spec.aspect}</span> • Target{" "}
            <span className="text-slate-300">{spec.dimensions}</span> (Max {spec.maxSize})
          </p>
        </div>
        <span className="text-[11px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700">
          {artworkType}
        </span>
      </div>

      {/* Upload Zone / Preview */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-lg p-4 cursor-pointer transition-all duration-200 flex flex-col items-center justify-center min-h-[160px] ${
          isDragging
            ? "border-indigo-500 bg-indigo-500/10"
            : "border-slate-700/80 hover:border-slate-500 bg-slate-950/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileChange(e.target.files[0]);
            }
          }}
        />

        {preview ? (
          <div className="relative group flex flex-col items-center">
            <img
              src={preview}
              alt={`${artworkType} preview`}
              className={`rounded shadow-md object-cover border border-slate-700 ${spec.previewClass}`}
            />
            <div className="absolute inset-0 bg-slate-950/70 rounded opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-xs text-slate-200">
              <RefreshCw className="w-5 h-5 mb-1 text-indigo-400 animate-spin-slow" />
              <span>Click to replace</span>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-2 text-slate-400">
              <Upload className="w-5 h-5" />
            </div>
            <p className="text-xs font-medium text-slate-300">
              Drop image here, or <span className="text-indigo-400">browse</span>
            </p>
            <p className="text-[11px] text-slate-500 mt-1">JPG, PNG, or WebP up to 200 KB</p>
          </div>
        )}

        {isUploading && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs rounded-lg flex flex-col items-center justify-center text-xs text-indigo-300">
            <RefreshCw className="w-6 h-6 animate-spin mb-2 text-indigo-400" />
            <span>Validating & uploading...</span>
          </div>
        )}
      </div>

      {/* Feedback Messages */}
      {errorMsg && (
        <div className="mt-3 flex items-start gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Validation Issue</p>
            <p className="text-rose-300/90 leading-relaxed">{errorMsg}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="mt-3 flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2 rounded-lg">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
