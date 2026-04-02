import { Axiom } from "@axiomhq/js";
import type { ErrorsData, ErrorGroup } from "../types";

interface AxiomParams {
  dataset: string;
  token?: string;
}

export async function fetchErrorsFromAxiom(
  params: AxiomParams,
): Promise<ErrorsData> {
  const axiom = new Axiom({ token: params.token ?? process.env.AXIOM_TOKEN ?? "" });

  // Un-named APL aggregations produce munged op keys in the response:
  // count() → "count_", min(_time) → "min__time", max(_time) → "max__time"
  const apl = `
    ['${params.dataset}']
    | where level in ("error", "ERROR", "fatal", "FATAL")
    | summarize count(), min(_time), max(_time) by message
    | order by count_ desc
    | limit 50
  `;

  // Use a 30-day window — free tier restricts how far back queries can reach
  const startTime = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  const endTime = new Date().toISOString();

  const result = await axiom.query(apl, { startTime, endTime });
  const totals = result.buckets.totals ?? [];

  const groups: ErrorGroup[] = totals
    .filter((total) => {
      const aggs = Object.fromEntries(
        (total.aggregations ?? []).map((a) => [a.op, a.value]),
      );
      return Number(aggs["count_"] ?? 0) > 0;
    })
    .map((total) => {
      const g = total.group as Record<string, unknown>;
      const aggs = Object.fromEntries(
        (total.aggregations ?? []).map((a) => [a.op, a.value]),
      );
      return {
        message: String(g["message"] ?? "(no message)"),
        count: Number(aggs["count_"] ?? 0),
        firstSeen: new Date(String(aggs["min__time"] ?? new Date())),
        lastSeen: new Date(String(aggs["max__time"] ?? new Date())),
      };
    });

  return {
    groups,
    timeWindow: "last 30 days",
    fetchedAt: new Date(),
  };
}
