import { notFound } from "next/navigation";
import { loadConfig } from "@/lib/config/load";
import { ErrorsPanel } from "@/components/panels/errors/ErrorsPanel";
import { fetchErrors } from "@/lib/panels/errors/fetch";
import type { PanelConfig } from "@/lib/config/schema";

interface Props {
  params: Promise<{ id: string; panel: string }>;
}

export default async function PanelPage({ params }: Props) {
  const { id, panel } = await params;
  const { projects } = loadConfig();

  const project = projects.find((p) => p.id === id);
  if (!project) notFound();

  const panelConfig = project.panels.find((p) => p.type === panel);
  if (!panelConfig) notFound();

  if (panel === "errors") {
    const data = await fetchErrors(panelConfig as Extract<PanelConfig, { type: "errors" }>);
    return <ErrorsPanel projectName={project.name} data={data} />;
  }

  notFound();
}
