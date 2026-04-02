import type { PanelConfig } from "@/lib/config/schema";
import { fetchErrorsFromAxiom } from "./fetchers/axiom";
import type { ErrorsData } from "./types";

type ErrorsPanelConfig = Extract<PanelConfig, { type: "errors" }>;

export async function fetchErrors(panel: ErrorsPanelConfig): Promise<ErrorsData> {
  switch (panel.source) {
    case "axiom":
      return fetchErrorsFromAxiom(panel.params);
    case "google_cloud_logging":
    case "grafana_loki":
    case "logfire":
      throw new Error(`Fetcher for source "${panel.source}" is not yet implemented`);
  }
}
