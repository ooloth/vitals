import type { ErrorsData } from "./types";

const now = new Date();
const hoursAgo = (h: number) => new Date(now.getTime() - h * 60 * 60 * 1000);

export const mockErrorsData: ErrorsData = {
  timeWindow: "last 24h",
  fetchedAt: now,
  groups: [
    {
      message: "TypeError: Cannot read properties of undefined (reading 'id')",
      count: 142,
      firstSeen: hoursAgo(23),
      lastSeen: hoursAgo(0.1),
    },
    {
      message: "Error: ECONNREFUSED connect ECONNREFUSED 127.0.0.1:5432",
      count: 38,
      firstSeen: hoursAgo(18),
      lastSeen: hoursAgo(2),
    },
    {
      message: "ZodError: invalid_type at path: body.userId",
      count: 21,
      firstSeen: hoursAgo(11),
      lastSeen: hoursAgo(0.5),
    },
    {
      message: "Error: JWT expired",
      count: 9,
      firstSeen: hoursAgo(6),
      lastSeen: hoursAgo(1),
    },
    {
      message: "RangeError: Maximum call stack size exceeded",
      count: 3,
      firstSeen: hoursAgo(4),
      lastSeen: hoursAgo(4),
    },
  ],
};
