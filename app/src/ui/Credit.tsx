import type { ReactNode } from "react";
import { t } from "../i18n";
import { NLOD_URL, SODIR_FACTPAGES_URL } from "../sodir";

/** The credit to Sodir as the source, under NLOD. Always visible. */
export function Credit() {
  const links: Record<string, ReactNode> = {
    source: <a href={SODIR_FACTPAGES_URL}>{t("credit.source")}</a>,
    licence: <a href={NLOD_URL}>{t("credit.licence")}</a>,
  };
  // Split the translated sentence around its {source} and {licence} placeholders.
  const parts = t("credit.text").split(/\{(\w+)\}/);
  return (
    <footer className="credit" data-testid="sodir-credit">
      {parts.map((part, i) => (i % 2 === 1 ? <span key={i}>{links[part] ?? part}</span> : part))}
    </footer>
  );
}
