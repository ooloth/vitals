import { z } from "zod";

// Resolves ${ENV_VAR} references at parse time
const envString = z.string().transform((s) =>
  s.replace(/\$\{([^}]+)\}/g, (_, name) => process.env[name] ?? ""),
);

const GCLParamsSchema = z.object({
  project_id: envString,
  log_name: envString.optional(),
});

const GrafanaLokiParamsSchema = z.object({
  base_url: envString,
  datasource_uid: envString,
  selector: z.string(),
  token: envString.optional(),
});

const AxiomParamsSchema = z.object({
  dataset: envString,
  token: envString.optional(),
});

const LogfireParamsSchema = z.object({
  project_id: envString,
  token: envString.optional(),
});

export const PanelConfigSchema = z.discriminatedUnion("source", [
  z.object({
    type: z.literal("errors"),
    source: z.literal("google_cloud_logging"),
    params: GCLParamsSchema,
  }),
  z.object({
    type: z.literal("errors"),
    source: z.literal("grafana_loki"),
    params: GrafanaLokiParamsSchema,
  }),
  z.object({
    type: z.literal("errors"),
    source: z.literal("axiom"),
    params: AxiomParamsSchema,
  }),
  z.object({
    type: z.literal("errors"),
    source: z.literal("logfire"),
    params: LogfireParamsSchema,
  }),
]);

export const ProjectConfigSchema = z.object({
  id: z.string(),
  name: z.string(),
  panels: z.array(PanelConfigSchema),
});

export const VitalsConfigSchema = z.object({
  projects: z.array(ProjectConfigSchema),
});

export type PanelConfig = z.infer<typeof PanelConfigSchema>;
export type ProjectConfig = z.infer<typeof ProjectConfigSchema>;
export type VitalsConfig = z.infer<typeof VitalsConfigSchema>;
