import { Axiom } from "@axiomhq/js";
import type { ErrorsData, ErrorGroup } from "../types";

interface AxiomParams {
  dataset: string;
  token?: string;
}

interface ErrorRow {
  message: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
}

export async function fetchErrorsFromAxiom(
  params: AxiomParams,
): Promise<ErrorsData> {
  const axiom = new Axiom({ token: params.token ?? process.env.AXIOM_TOKEN ?? "" });

  const apl = `
    ['${params.dataset}']
    | where level in ("error", "ERROR", "fatal", "FATAL")
    | summarize count=count(), firstSeen=min(_time), lastSeen=max(_time) by message
    | order by count desc
    | limit 50
  `;

  const startTime = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const endTime = new Date().toISOString();

  const result = await axiom.query(apl, { startTime, endTime });

  const groups: ErrorGroup[] = (result.matches ?? []).map((match) => {
    const row = match.data as ErrorRow;
    return {
      message: row.message ?? "(no message)",
      count: row.count ?? 0,
      firstSeen: new Date(row.firstSeen),
      lastSeen: new Date(row.lastSeen),
    };
  });

  return {
    groups,
    timeWindow: "last 24h",
    fetchedAt: new Date(),
  };
}
