export interface ErrorGroup {
  message: string
  count: number
  firstSeen: Date
  lastSeen: Date
}

export interface ErrorsData {
  groups: ErrorGroup[]
  timeWindow: string
  fetchedAt: Date
}
