/**
 * Lightweight analysis state — replaces global.__lastAnalysis.
 *
 * Stores session data between the upload, fighter-selection, and results screens.
 * Uses a simple module-level singleton so it works across Expo Router screens
 * without needing Context or a state library.
 */

import type { AnalyzeSessionResponse, Analysis } from "./api";

interface AnalysisState {
  /** Session response from POST /analyze (fighter previews + session_id) */
  sessionResponse: AnalyzeSessionResponse | null;
  /** Selected fighter ID after the user picks "I am this fighter" */
  selectedFighterId: string | null;
  /** Full analysis data fetched for the selected fighter */
  analysisData: Analysis | null;
  /** Duration of the analyzed video */
  durationSeconds: number;
}

const state: AnalysisState = {
  sessionResponse: null,
  selectedFighterId: null,
  analysisData: null,
  durationSeconds: 0,
};

export function setSessionResponse(response: AnalyzeSessionResponse) {
  state.sessionResponse = response;
  state.durationSeconds = response.duration_seconds;
  state.selectedFighterId = null;
  state.analysisData = null;
}

export function setSelectedFighter(fighterId: string, analysis: Analysis) {
  state.selectedFighterId = fighterId;
  state.analysisData = analysis;
}

export function getSessionResponse() {
  return state.sessionResponse;
}

export function getSelectedFighterId() {
  return state.selectedFighterId;
}

export function getAnalysisData() {
  return state.analysisData;
}

export function getDurationSeconds() {
  return state.durationSeconds;
}

export function clearAnalysisState() {
  state.sessionResponse = null;
  state.selectedFighterId = null;
  state.analysisData = null;
  state.durationSeconds = 0;
}
