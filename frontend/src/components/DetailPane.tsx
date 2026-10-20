import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useChatStore } from "../store";
import { colorFor } from "../lib/colorFor";
import type { Match } from "../types";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-4">
      <div className="text-[0.7rem] text-ink-muted uppercase tracking-[0.08em] mb-1">{label}</div>
      {children}
    </div>
  );
}

function PreviewImage({ match }: { match: Match }) {
  const [failed, setFailed] = useState(false);

  return (
    <div className="rounded-xl overflow-hidden mb-5" style={{ background: colorFor(match.id) }}>
      {!failed ? (
        <img
          src={`/images/${match.id}/preview?size=full`}
          alt=""
          className="block w-full h-auto max-h-[60vh] object-contain"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="h-40" />
      )}
    </div>
  );
}

export function DetailPane() {
  const { t } = useTranslation();
  const match = useChatStore((s) => s.selectedMatch);
  const selectMatch = useChatStore((s) => s.selectMatch);
  const isOpen = match !== null;

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") selectMatch(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, selectMatch]);

  if (!match) return null;

  const fileName = match.file_path.split("/").pop();

  return (
    <aside className="fixed top-4 right-4 bottom-4 w-[46vw] max-w-[calc(100vw-2rem)] z-30 bg-canvas rounded-xl border border-line shadow-xl overflow-y-auto p-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="font-mono text-sm break-all">{fileName}</div>
        <button
          type="button"
          onClick={() => selectMatch(null)}
          className="text-sm text-ink-muted hover:text-ink cursor-pointer"
        >
          {t("pane.close")}
        </button>
      </div>
      <PreviewImage key={match.id} match={match} />
      <Row label={t("pane.path")}>
        <div className="font-mono text-[0.78rem] break-all select-text">{match.file_path}</div>
      </Row>
      <Row label={t("pane.caption")}>
        <div className="text-sm">{match.caption ? match.caption : t("match.noCaption")}</div>
      </Row>
      {match.camera_model && (
        <Row label={t("pane.camera")}>
          <div className="text-sm">{match.camera_model}</div>
        </Row>
      )}
      {match.capture_time && (
        <Row label={t("pane.captured")}>
          <div className="text-sm">{new Date(match.capture_time).toLocaleString()}</div>
        </Row>
      )}
      {match.rating != null && (
        <Row label={t("pane.rating")}>
          <div className="text-sm">{t("match.rating", { value: match.rating })}</div>
        </Row>
      )}
      {match.similarity != null && (
        <Row label={t("pane.similarity")}>
          <div className="text-sm">{t("match.similarity", { value: match.similarity })}</div>
        </Row>
      )}
      {match.keywords.length > 0 && (
        <Row label={t("pane.keywords")}>
          <div className="flex flex-wrap gap-[5px]">
            {match.keywords.map((k, i) => (
              <span
                key={i}
                className="text-[0.65rem] px-[9px] py-[3px] rounded-full bg-surface border border-line text-ink"
              >
                {k}
              </span>
            ))}
          </div>
        </Row>
      )}
      {match.collections.length > 0 && (
        <Row label={t("pane.collections")}>
          {match.collections.map((c, i) => (
            <div key={i} className="text-sm">
              {c}
            </div>
          ))}
        </Row>
      )}
    </aside>
  );
}
