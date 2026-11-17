export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export type ParseError = {
  path: string;
  message: string;
};

export type TextFile = {
  path: string;
  text: string;
};

export type StoredFile = {
  path: string;
  text: string;
  json?: Json;
  jsonl?: Json[];
  error?: string;
  bytes: number;
};

export type SyscallEvent = {
  source?: string;
  timestamp?: number;
  syscall?: string;
  paths?: string[];
  write?: boolean;
  denied?: boolean;
  errno?: number | string | null;
  permission_denied?: boolean;
  rule_violation?: boolean;
  event_index?: number;
  native_stack?: string[];
  connect_disposition?: string;
};

export type RuntimeAction = {
  action?: string;
  elapsed?: number;
  pid?: number;
  model?: string;
  probability?: number;
  session_observer_input?: string;
  session_observer_input_sha256?: string;
  [key: string]: Json | undefined;
};

export type ObserverInputReceipt = {
  path?: string;
  sha256?: string;
  event_indices?: number[];
  events?: number;
  frames?: number;
};

export type WorkerRecord = {
  id: string;
  label: string;
  group: string;
  sourceFiles: string[];
  argv?: string[];
  returncode?: number | null;
  timedOut?: boolean;
  elapsedSeconds?: number | null;
  runtimeVerdict?: string | null;
  deliveryVerdict?: string | null;
  contentVerdict?: string | null;
  evidenceStatus?: string | null;
  problems: string[];
  events: SyscallEvent[];
  eventCountFromSummary?: number;
  actions: RuntimeAction[];
  observerInputs: ObserverInputReceipt[];
  nativeStacks?: boolean | null;
  terminationRequested?: boolean | null;
  finalTraceDrained?: boolean | null;
  task?: string;
  principal?: string;
  informationFlow?: Json;
  reason?: string;
  stdoutTruncated?: boolean | null;
  stderrTruncated?: boolean | null;
  stdoutText?: string;
  stderrText?: string;
  brokerAudit?: Json;
  kernelGateAudit?: Json;
  scopeNote?: string;
  observerMode?: string;
  runtimeMissing: boolean;
};

export type SessionRecord = {
  path: string;
  task?: string;
  closed?: boolean | null;
  scopeStopped?: boolean | null;
  commandTimeoutSeconds?: number | null;
  identityLedger?: string;
  identityAtStart?: Json;
  informationFlow?: Json;
  brokerAudit?: Json;
  scopeNote?: string;
  calls: WorkerRecord[];
};

export type SummaryDoc = {
  path: string;
  kind: string;
  json: Json;
};

export type ObserverDecision = {
  path: string;
  sequence?: string;
  inputSha256?: string;
  model?: string;
  probability?: number;
  sessionObserverInput?: string;
  sessionObserverInputSha256?: string;
  raw: Json;
};

export type ContentChunk = {
  input?: string;
  inputSha256?: string;
  scores?: Record<string, number>;
  usage?: Json;
  model?: string;
};

export type ContentDecision = {
  path: string;
  journal: "host" | "tool" | "handoff" | "unknown";
  sequence?: number;
  kind?: string;
  verdict?: string;
  elapsedSeconds?: number;
  chunks: ContentChunk[];
  confirmation?: {
    input?: string;
    inputSha256?: string;
    probability?: number;
    scores?: Record<string, number>;
  };
  contentSha256?: string;
  raw: Json;
};

export type ContentBody = {
  path: string;
  journal: "host" | "tool" | "handoff" | "unknown";
  kind?: string;
  json: Json;
};

export type FlowDoc = {
  path: string;
  kind: "policy" | "audit" | "summary" | "manifest";
  json: Json;
};

export type IdentityDoc = {
  path: string;
  phase: string;
  json: Json;
};

export type HistoryHit = {
  source?: string;
  sha256?: string;
  kind?: string;
  start_character?: number;
  total_characters?: number;
  excerpt?: string;
  root_relative_to_input?: string;
};

export type HistoryDoc = {
  path: string;
  json: Json;
};

export type StopEvent = {
  path: string;
  kind: string;
  json: Json;
};

export type UsageRecord = {
  path: string;
  source: string;
  json: Json;
};

export type ExtraDoc = {
  path: string;
  note: string;
  json?: Json;
};

export type RunBundle = {
  title: string;
  origin: string;
  files: Map<string, StoredFile>;
  parseErrors: ParseError[];
  notes: string[];
  summaries: SummaryDoc[];
  sessions: SessionRecord[];
  workers: WorkerRecord[];
  observerDecisions: ObserverDecision[];
  observerInputs: { path: string; json: Json }[];
  contentDecisions: ContentDecision[];
  contentBodies: ContentBody[];
  flowDocs: FlowDoc[];
  identityDocs: IdentityDoc[];
  historyDocs: HistoryDoc[];
  stopEvents: StopEvent[];
  usageRecords: UsageRecord[];
  extraDocs: ExtraDoc[];
  jsonlLogs: { path: string; records: Json[] }[];
};
