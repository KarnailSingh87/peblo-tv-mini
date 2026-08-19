import React, { useState } from "react";
import { Link } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UploadCloud,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  RefreshCw,
  Clock,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  Film,
  Layers,
  Image as ImageIcon,
  History,
  Info,
  ChevronDown,
  ChevronUp,
  XCircle,
  FileCheck2,
  ExternalLink
} from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../auth/AuthContext";
import { ValidationIssue, PublishRun } from "../../types";

export const PublishPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isAdmin = user?.role === "admin";

  const [activeGroup, setActiveGroup] = useState<"all" | "shows" | "seasons" | "episodes" | "artwork">("all");
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [publishFeedback, setPublishFeedback] = useState<{
    type: "success" | "error";
    title: string;
    message: string;
    blockers?: string[];
  } | null>(null);

  // 1. Fetch Validation Report (Accessible to Editor and Admin)
  const {
    data: report,
    isLoading: isReportLoading,
    isError: isReportError,
    error: reportError,
    isRefetching: isReportRefetching,
    refetch: refetchReport
  } = useQuery({
    queryKey: ["validationReport"],
    queryFn: () => api.getValidationReport(),
    refetchInterval: 12000
  });

  // 2. Fetch Publish History (Admin Only - gracefully handles 403 for editor)
  const {
    data: publishRuns,
    isLoading: isHistoryLoading,
    isError: isHistoryError,
    error: historyError,
    refetch: refetchHistory
  } = useQuery({
    queryKey: ["publishRuns"],
    queryFn: () => api.getPublishRuns(),
    enabled: isAdmin,
    retry: false
  });

  // 3. Publish Mutation (Admin Only)
  const publishMutation = useMutation({
    mutationFn: () => api.publishCatalog(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["publishRuns"] });
      queryClient.invalidateQueries({ queryKey: ["validationReport"] });
      setPublishFeedback({
        type: "success",
        title: "Catalogue Successfully Published!",
        message: `Version ${data.publish_run.catalogue_version} is now live with ${data.publish_run.show_count} shows and ${data.publish_run.episode_count} episodes.`
      });
    },
    onError: (err: any) => {
      const blockers = err.data?.detail?.blockers || [];
      setPublishFeedback({
        type: "error",
        title: "Publishing Rejected by Pre-Flight Audit",
        message: err.message || "Failed to publish catalogue due to validation blockers.",
        blockers: blockers.length > 0 ? blockers : undefined
      });
    }
  });

  const blockingCount = report?.blocking_count ?? 0;
  const warningCount = report?.warning_count ?? 0;
  const canPublish = isAdmin && blockingCount === 0 && !isReportLoading;

  // Compute disabled reason tooltip / banner
  const getDisabledReason = () => {
    if (!isAdmin) {
      return "Publishing is restricted to Administrator accounts. As an Editor, you can review issues and fix content.";
    }
    if (isReportLoading) {
      return "Running pre-flight audit...";
    }
    if (blockingCount > 0) {
      return `Publishing is disabled because there ${
        blockingCount === 1 ? "is 1 blocking error" : `are ${blockingCount} blocking errors`
      } in the catalogue that must be resolved first.`;
    }
    return null;
  };

  const disabledReason = getDisabledReason();

  const getFilteredIssues = (): ValidationIssue[] => {
    if (!report) return [];
    if (activeGroup === "all") return report.all_issues;
    return report.grouped_by_entity[activeGroup] || [];
  };

  const filteredIssues = getFilteredIssues();

  return (
    <div className="p-8 max-w-7xl w-full mx-auto space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">Catalogue Publishing & Validation</h1>
            <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              Release Studio
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Pre-flight data integrity audit, zero-downtime atomic catalogue release, and publishing audit logs.
          </p>
        </div>

        <button
          onClick={() => {
            refetchReport();
            if (isAdmin) refetchHistory();
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition-all shadow-sm self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isReportRefetching ? "animate-spin text-indigo-400" : ""}`} />
          <span>Re-run Validation Audit</span>
        </button>
      </div>

      {/* Action Feedback Banner (Success / Error) */}
      {publishFeedback && (
        <div
          className={`flex items-start justify-between gap-3 p-5 rounded-2xl text-sm font-medium border shadow-lg transition-all animate-in fade-in duration-200 ${
            publishFeedback.type === "success"
              ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
              : "bg-rose-950/40 border-rose-500/40 text-rose-200"
          }`}
        >
          <div className="flex items-start gap-3.5">
            {publishFeedback.type === "success" ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-bold text-base text-white">{publishFeedback.title}</p>
              <p className="text-xs mt-1 opacity-90 leading-relaxed">{publishFeedback.message}</p>
              {publishFeedback.blockers && (
                <ul className="mt-2.5 space-y-1 list-disc list-inside text-xs text-rose-300 font-mono">
                  {publishFeedback.blockers.map((b, idx) => (
                    <li key={idx}>{b}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <button
            onClick={() => setPublishFeedback(null)}
            className="text-xs opacity-60 hover:opacity-100 p-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* KPI & Status Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Release Health Card */}
        <div
          className={`p-6 rounded-2xl border backdrop-blur-md shadow-xl transition-all ${
            isReportLoading
              ? "bg-slate-900/60 border-slate-800 text-slate-300"
              : report?.can_publish
              ? "bg-emerald-950/25 border-emerald-500/40 text-emerald-300"
              : "bg-rose-950/25 border-rose-500/40 text-rose-300"
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Release Status</span>
            {isReportLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
            ) : report?.can_publish ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertOctagon className="w-5 h-5 text-rose-400" />
            )}
          </div>
          <h3 className="text-xl font-bold text-white">
            {isReportLoading
              ? "Auditing Catalog..."
              : report?.can_publish
              ? "Ready for Publication"
              : "Publication Blocked"}
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            {isReportLoading
              ? "Scanning shows, episodes, and artwork..."
              : report?.can_publish
              ? "All active published shows and episodes pass reference constraints."
              : `${blockingCount} blocking validation ${
                  blockingCount === 1 ? "issue" : "issues"
                } prevent compiling the live catalogue.`}
          </p>
        </div>

        {/* Blocking Errors Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Blocking Errors</span>
            <AlertOctagon className="w-5 h-5 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{blockingCount}</div>
          <p className="text-xs text-slate-400 mt-1.5">
            Missing sections, missing durations, missing artwork, or duplicate language tracks
          </p>
        </div>

        {/* Editorial Warnings Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Editorial Warnings</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{warningCount}</div>
          <p className="text-xs text-slate-400 mt-1.5">
            Draft shows, draft episodes, and empty season notices (non-blocking)
          </p>
        </div>
      </div>

      {/* PUBLISH TRIGGER ACTION PANEL */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-xl">
          <div className="flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-indigo-400" />
            <h3 className="text-lg font-bold text-white">Live Catalogue Release</h3>
            {isAdmin ? (
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Admin Authorized
              </span>
            ) : (
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Editor (Read-Only)
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Atomic release compiles all valid published shows into <code className="text-indigo-300 font-mono">catalogue.json</code>.
            Existing viewers will experience zero downtime or partial payloads.
          </p>

          {/* Explanation if disabled */}
          {disabledReason && (
            <div className="flex items-center gap-2 text-xs text-amber-300/90 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg mt-2">
              <Info className="w-3.5 h-3.5 shrink-0 text-amber-400" />
              <span>{disabledReason}</span>
            </div>
          )}
        </div>

        <div className="shrink-0 w-full md:w-auto">
          <button
            onClick={() => publishMutation.mutate()}
            disabled={!canPublish || publishMutation.isPending}
            className="w-full md:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold shadow-xl shadow-indigo-600/30 transition-all"
          >
            {publishMutation.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-indigo-200" />
                <span>Compiling & Publishing...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                <span>Publish Streaming Catalogue</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* VALIDATION REPORT PANEL */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h3 className="text-base font-bold text-white">Pre-Flight Validation Audit</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Identifies data integrity violations across shows, seasons, episodes, and artwork.
            </p>
          </div>

          {/* Group Filter Tabs */}
          <div className="flex flex-wrap items-center p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">
            {[
              { key: "all", label: `All Issues (${report?.total_issues || 0})` },
              { key: "shows", label: `Shows (${report?.grouped_by_entity.shows.length || 0})` },
              { key: "seasons", label: `Seasons (${report?.grouped_by_entity.seasons.length || 0})` },
              { key: "episodes", label: `Episodes (${report?.grouped_by_entity.episodes.length || 0})` },
              { key: "artwork", label: `Artwork (${report?.grouped_by_entity.artwork.length || 0})` }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveGroup(tab.key as any)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  activeGroup === tab.key
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading State */}
        {isReportLoading ? (
          <div className="py-16 flex flex-col items-center justify-center text-slate-400 gap-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm font-medium">Running validation audit checks...</p>
          </div>
        ) : isReportError ? (
          <div className="py-12 text-center text-rose-400">
            <AlertOctagon className="w-8 h-8 mx-auto mb-2" />
            <p className="font-semibold text-sm">Failed to retrieve validation report</p>
            <p className="text-xs text-rose-300/80 mt-1">{(reportError as any)?.message}</p>
            <button
              onClick={() => refetchReport()}
              className="mt-3 px-3.5 py-1.5 rounded-lg bg-rose-500/20 text-xs font-semibold text-rose-200 border border-rose-500/30"
            >
              Retry Audit
            </button>
          </div>
        ) : filteredIssues.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2.5" />
            <h4 className="text-sm font-bold text-slate-200">No issues found in this category</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              All content records in this group satisfy streaming catalogue constraints.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredIssues.map((issue, idx) => {
              const isBlocking = issue.severity === "blocking";
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all ${
                    isBlocking
                      ? "bg-rose-500/5 border-rose-500/20 hover:border-rose-500/30 shadow-xs"
                      : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {isBlocking ? (
                      <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                            isBlocking
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          }`}
                        >
                          {issue.severity}
                        </span>
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                          {issue.entity_type} • <span className="font-mono text-slate-300">{issue.entity_id}</span>
                        </span>
                        {issue.title && (
                          <span className="text-xs font-semibold text-slate-200">
                            ({issue.title})
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-200 font-medium mt-1 leading-relaxed">
                        {issue.problem}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        <span className="text-indigo-400 font-medium">Suggested Action:</span>{" "}
                        {issue.action}
                      </p>
                    </div>
                  </div>

                  {/* Direct Fix Jump Links */}
                  <div className="shrink-0 self-end sm:self-center">
                    {issue.entity_type === "show" && (
                      <Link href={`/admin/shows/${issue.entity_id}`}>
                        <a className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-xs font-medium text-slate-300 transition-all">
                          <span>Fix Show</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </Link>
                    )}
                    {issue.entity_type === "episode" && (
                      <Link href={`/admin/episodes/${issue.entity_id}`}>
                        <a className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-xs font-medium text-slate-300 transition-all">
                          <span>Fix Episode</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </Link>
                    )}
                    {issue.entity_type === "artwork" && issue.show_id && (
                      <Link href={`/admin/shows/${issue.show_id}`}>
                        <a className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-xs font-medium text-slate-300 transition-all">
                          <span>Upload Artwork</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* PUBLISH AUDIT HISTORY SECTION */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-2.5">
            <History className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Publish Audit History</h3>
          </div>
          {isAdmin && (
            <button
              onClick={() => refetchHistory()}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh History</span>
            </button>
          )}
        </div>

        {/* Permission Denied Notice for Editors */}
        {!isAdmin ? (
          <div className="py-8 px-4 rounded-xl bg-slate-950/50 border border-slate-800 text-center">
            <ShieldAlert className="w-8 h-8 text-amber-400/80 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-300">Publish History Restricted to Administrators</p>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Editors can audit validation issues and update content. Log in with an administrator account to view historical release runs.
            </p>
          </div>
        ) : isHistoryLoading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs">Loading publish history...</p>
          </div>
        ) : isHistoryError ? (
          <div className="py-8 text-center text-rose-400">
            <p className="text-xs font-semibold">Failed to load publish history: {(historyError as any)?.message}</p>
          </div>
        ) : publishRuns?.length === 0 ? (
          <div className="py-8 text-center text-slate-400 italic text-xs">
            No publish runs have been executed yet. Click "Publish Streaming Catalogue" once all validation checks pass.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-950/40 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Triggered By</th>
                  <th className="py-3 px-4">Shows / Episodes</th>
                  <th className="py-3 px-4">File Size</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {publishRuns?.map((run: PublishRun) => {
                  const isExpanded = expandedRunId === run.id;
                  const isSuccess = run.status === "success";
                  const durationSec = run.completed_at
                    ? Math.max(
                        0,
                        Math.round(
                          (new Date(run.completed_at).getTime() -
                            new Date(run.started_at).getTime()) /
                            1000
                        )
                      )
                    : null;

                  return (
                    <React.Fragment key={run.id}>
                      <tr className="hover:bg-slate-800/30 transition-colors group">
                        <td className="py-3.5 px-4 font-mono font-bold text-indigo-300">
                          v{run.version ?? run.catalogue_version ?? 1}
                        </td>
                        <td className="py-3.5 px-4">
                          {isSuccess ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3" />
                              Success
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                              <XCircle className="w-3 h-3" />
                              Failed
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-slate-300">
                          {new Date(run.started_at).toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-200">
                          {run.triggered_by}
                        </td>
                        <td className="py-3.5 px-4 text-slate-300">
                          <span className="font-semibold text-slate-100">{run.show_count}</span> shows •{" "}
                          <span className="font-semibold text-slate-100">{run.episode_count}</span> eps
                        </td>
                        <td className="py-3.5 px-4 font-mono text-slate-400">
                          {run.file_size_bytes
                            ? `${(run.file_size_bytes / 1024).toFixed(1)} KB`
                            : "—"}
                        </td>
                        <td className="py-3.5 px-4 text-slate-400">
                          {durationSec !== null ? `${durationSec}s` : "In Progress"}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          {run.error_message ? (
                            <button
                              onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
                              className="inline-flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 font-medium"
                            >
                              <span>View Error</span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </button>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                      </tr>

                      {/* Collapsible Error Reason Box */}
                      {isExpanded && run.error_message && (
                        <tr className="bg-rose-500/5 border-b border-rose-500/20">
                          <td colSpan={8} className="p-4">
                            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-200 text-xs">
                              <p className="font-bold flex items-center gap-1.5 text-rose-300 mb-1">
                                <AlertOctagon className="w-4 h-4" />
                                <span>Failure Diagnostics:</span>
                              </p>
                              <p className="font-mono text-[11px] leading-relaxed">{run.error_message}</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
