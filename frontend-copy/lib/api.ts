import * as FileSystem from "expo-file-system";
import { Platform } from "react-native";

// Update this to your backend URL (use your machine's local IP for Expo Go)
const API_BASE = "http://100.65.31.76:5000";

// ---------------------------------------------------------------------------
// Video analysis (session-based)
// ---------------------------------------------------------------------------

export async function analyzeVideo(
  videoUri: string,
  onProgress?: (pct: number) => void,
): Promise<AnalyzeSessionResponse> {
  if (Platform.OS === "web") {
    return _analyzeVideoWeb(videoUri, onProgress);
  }
  return _analyzeVideoNative(videoUri, onProgress);
}

export async function analyzeVideoUrl(
  url: string,
  onProgress?: (pct: number) => void,
): Promise<AnalyzeSessionResponse> {
  onProgress?.(5);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  onProgress?.(90);

  let body: any = {};
  try {
    body = await response.json();
  } catch {}

  if (!response.ok) {
    throw new Error(body.error || "Analysis failed");
  }

  onProgress?.(100);
  return body as AnalyzeSessionResponse;
}

async function _analyzeVideoNative(
  videoUri: string,
  onProgress?: (pct: number) => void,
): Promise<AnalyzeSessionResponse> {
  const filename = videoUri.split("/").pop() || "video.mp4";
  const match = /\.(\w+)$/.exec(filename);
  const mimeType = match ? `video/${match[1]}` : "video/mp4";

  onProgress?.(10);

  const result = await FileSystem.uploadAsync(`${API_BASE}/analyze`, videoUri, {
    httpMethod: "POST",
    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
    fieldName: "video",
    mimeType,
  });

  onProgress?.(90);

  let body: any = {};
  try {
    body = JSON.parse(result.body);
  } catch {}

  if (result.status < 200 || result.status >= 300) {
    throw new Error(body.error || "Analysis failed");
  }

  onProgress?.(100);
  return body as AnalyzeSessionResponse;
}

async function _analyzeVideoWeb(
  videoUri: string,
  onProgress?: (pct: number) => void,
): Promise<AnalyzeSessionResponse> {
  const blob = await fetch(videoUri).then((r) => r.blob());
  const formData = new FormData();
  formData.append("video", blob, "video.mp4");

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/analyze`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 90));
      }
    };

    xhr.onload = () => {
      let body: any = {};
      try {
        body = JSON.parse(xhr.responseText);
      } catch {}

      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(100);
        resolve(body as AnalyzeSessionResponse);
      } else {
        reject(new Error(body.error || "Analysis failed"));
      }
    };

    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.send(formData);
  });
}

// ---------------------------------------------------------------------------
// Session-based result retrieval
// ---------------------------------------------------------------------------

export async function getFighterAnalysis(
  sessionId: string,
  fighterId: string,
): Promise<FighterAnalysisResponse> {
  const response = await fetch(
    `${API_BASE}/analysis/${sessionId}/fighter/${fighterId}`,
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as any).error || "Failed to fetch fighter analysis");
  }
  return response.json();
}

export async function getSessionSummary(
  sessionId: string,
): Promise<SessionSummaryResponse> {
  const response = await fetch(`${API_BASE}/analysis/${sessionId}/summary`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as any).error || "Failed to fetch session summary");
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

export async function getPresets(): Promise<PresetsResponse> {
  const response = await fetch(`${API_BASE}/presets`);
  if (!response.ok) throw new Error("Failed to fetch presets");
  return response.json();
}

export async function getPresetDetail(
  key: string,
): Promise<PresetDetailResponse> {
  const response = await fetch(`${API_BASE}/presets/${key}`);
  if (!response.ok) throw new Error("Failed to fetch preset");
  return response.json();
}

// ---------------------------------------------------------------------------
// Types — Session flow
// ---------------------------------------------------------------------------

export interface AnalyzeSessionResponse {
  success: boolean;
  session_id: string;
  fighters: FighterPreview[];
  overview_frame_base64: string;
  duration_seconds: number;
  fighter_count: number;
}

export interface FighterPreview {
  id: string;
  thumbnail_base64: string;
  color: string;
  label: string;
  overall_score: number;
  guard_type: string;
  stance: string;
}

export interface FighterAnalysisResponse {
  success: boolean;
  session_id: string;
  fighter_id: string;
  duration_seconds: number;
  analysis: Analysis;
}

export interface SessionSummaryResponse {
  success: boolean;
  session_id: string;
  duration_seconds: number;
  overview_frame_base64: string;
  fighters: FighterPreview[];
}

// ---------------------------------------------------------------------------
// Types — Analysis data
// ---------------------------------------------------------------------------

export interface DetailedSection {
  reasoning: string;
  guard_type?: string;
  guard_type_name?: string;
  score?: number;
  interpretation?: string;
}

export interface EventTimelineEntry {
  type: string;
  frame_idx: number;
  timestamp: string;
  detail: string;
  move?: string;
}

export interface OpponentPattern {
  type: string;
  title: string;
  description: string;
  counter_advice: string;
}

export interface CombinationDetected {
  punches: string[];
  name: string;
  start_timestamp: string;
  end_timestamp: string;
  punch_count: number;
  known_pattern: boolean;
}

export interface CombinationAnalysis {
  detected_combinations: CombinationDetected[];
  flow_score: number;
  total_combinations: number;
  total_single_punches: number;
  recommendations: string[];
}

export interface PunchMechanicsDetail {
  timestamp: string;
  extension: number;
  shoulder_engagement: number;
  guard_discipline: number;
  hip_rotation: number;
  snap_back: number;
  overall: number;
}

export interface PunchMechanicsEntry {
  name: string;
  count: number;
  average_score: number;
  best_score: number;
  worst_score: number;
  common_faults: string[];
  observed_faults: string[];
  detail_per_instance: PunchMechanicsDetail[];
}

export interface Analysis {
  overall_score: number;
  stance: {
    dominant: string;
    consistency: number;
    breakdown: Record<string, number>;
    score: number;
  };
  guard: {
    score: number;
    hand_position: number;
    elbow_tuck: number;
    guard_drop_rate: number;
    consistency: number;
    guard_type: string;
  };
  footwork: {
    score: number;
    lateral_movement: number;
    stance_width_consistency: number;
    total_movement: number;
  };
  head_movement: {
    score: number;
    horizontal_variation: number;
    vertical_variation: number;
  };
  balance: {
    score: number;
    center_of_gravity: number;
    weight_distribution: number;
  };
  punches: {
    total_punches: number;
    total_defensive_moves: number;
    distribution: Record<string, number>;
    variety_score: number;
    jab_ratio: number;
    punch_defense_ratio: number;
  } | null;
  combinations: CombinationAnalysis | null;
  punch_mechanics: Record<string, PunchMechanicsEntry> | null;
  style_matches: StyleMatch[];
  strengths: string[];
  improvements: string[];
  detailed_analysis: {
    overall_summary: DetailedSection;
    guard_analysis: DetailedSection;
    stance_analysis: DetailedSection;
    footwork_analysis: DetailedSection;
    head_movement_analysis: DetailedSection;
    balance_analysis: DetailedSection;
    punch_analysis?: DetailedSection;
    combination_analysis?: DetailedSection;
    punch_mechanics_analysis?: DetailedSection;
    style_comparison?: DetailedSection;
    improvement_plan: DetailedSection;
  };
  event_timeline: EventTimelineEntry[];
  opponent_patterns?: OpponentPattern[];
  frames_analyzed: number;
}

export interface StyleMatch {
  fighter: string;
  nickname: string;
  similarity: number;
  style: string;
  description: string;
}

export interface FighterPreset {
  key: string;
  name: string;
  nickname: string;
  style: string;
  stance: string;
  era: string;
  signature_moves: string[];
  description: string;
}

export interface PresetsResponse {
  presets: FighterPreset[];
}

export interface PresetDetailResponse {
  preset: {
    name: string;
    nickname: string;
    era: string;
    stance: string;
    style: string;
    traits: Record<string, number>;
    signature_moves: string[];
    description: string;
  };
}
