import { useEffect, useState } from "react";
import type { Dataset } from "../dataset";
import { t } from "../i18n";
import { Campaign } from "./Campaign";
import { Credit } from "./Credit";

type Load = { status: "loading" } | { status: "failed" } | { status: "ready"; dataset: Dataset };

export function App() {
  const [load, setLoad] = useState<Load>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetch(`${import.meta.env.BASE_URL}well_proposals.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<Dataset>;
      })
      .then((dataset) => !cancelled && setLoad({ status: "ready", dataset }))
      .catch(() => !cancelled && setLoad({ status: "failed" }));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>{t("app.title")}</h1>
      </header>
      <main>
        {load.status === "loading" && <p>{t("app.loading")}</p>}
        {load.status === "failed" && <p role="alert">{t("app.loadFailed")}</p>}
        {load.status === "ready" && <Campaign dataset={load.dataset} />}
      </main>
      <Credit />
    </div>
  );
}
