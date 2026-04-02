"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import type { ProjectConfig } from "@/lib/config/schema";

const PANEL_LABELS: Record<string, string> = {
  errors: "Errors",
};

interface Props {
  projects: Pick<ProjectConfig, "id" | "name" | "panels">[];
}

export function AppSidebar({ projects }: Props) {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarContent>
        {projects.map((project) => (
          <SidebarGroup key={project.id}>
            <SidebarGroupLabel>{project.name}</SidebarGroupLabel>
            <SidebarMenu>
              {project.panels.map((panel) => {
                const href = `/projects/${project.id}/${panel.type}`;
                return (
                  <SidebarMenuItem key={panel.type}>
                    <SidebarMenuButton
                      render={<Link href={href} />}
                      isActive={pathname === href}
                    >
                      {PANEL_LABELS[panel.type] ?? panel.type}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}
