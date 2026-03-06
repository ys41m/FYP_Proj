// Update this to your backend URL (use your machine's local IP for Expo Go)
const API_BASE = "http://192.168.1.100:5000";

export async function analyzeVideo(videoUri: string): Promise<AnalysisResponse> {
  const formData = new FormData();

  const filename = videoUri.split("/").pop() || "video.mp4";
  const match = /\.(\w+)$/.exec(filename);
  const type = match ? `video/${match[1]}` : "video/mp4";

  formData.append("video", {
    uri: videoUri,
    name: filename,
    type,
  } as any);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Analysis failed");
  }

  return response.json();
}

export async function getPresets(): Promise<PresetsResponse> {
  const response = await fetch(`${API_BASE}/presets`);
  if (!response.ok) throw new Error("Failed to fetch presets");
  return response.json();
}

export async function getPresetDetail(key: string): Promise<PresetDetailResponse> {
  const response = await fetch(`${API_BASE}/presets/${key}`);
  if (!response.ok) throw new Error("Failed to fetch preset");
  return response.json();
}

// Types

export interface AnalysisResponse {
  success: boolean;
  duration_seconds: number;
  analysis: Analysis;
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
  style_matches: StyleMatch[];
  strengths: string[];
  improvements: string[];
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
