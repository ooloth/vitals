import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ErrorsData } from "@/lib/panels/errors/types";

function timeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface Props {
  projectName: string;
  data: ErrorsData;
}

export function ErrorsPanel({ projectName, data }: Props) {
  return (
    <div className="flex flex-col gap-4 p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-xl font-semibold">Errors</h1>
          <p className="text-sm text-muted-foreground">{projectName}</p>
        </div>
        <span className="text-xs text-muted-foreground">
          {data.timeWindow} · fetched {timeAgo(data.fetchedAt)}
        </span>
      </div>

      {data.groups.length === 0 ? (
        <p className="text-sm text-muted-foreground">No errors in this period.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Error</TableHead>
              <TableHead className="w-20 text-right">Count</TableHead>
              <TableHead className="w-28">First seen</TableHead>
              <TableHead className="w-28">Last seen</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.groups.map((group, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{group.message}</TableCell>
                <TableCell className="text-right">
                  <Badge variant="secondary">{group.count}</Badge>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {timeAgo(group.firstSeen)}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {timeAgo(group.lastSeen)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
