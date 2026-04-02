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

const projects = [
  {
    id: "my-project",
    name: "My Project",
    panels: [{ type: "errors", label: "Errors" }],
  },
];

export function AppSidebar() {
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
                      {panel.label}
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
