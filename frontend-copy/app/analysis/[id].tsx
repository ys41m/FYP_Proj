import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { getFighterAnalysis } from "@/lib/api";
import type { Analysis, StyleMatch, DetailedSection, OpponentPattern } from "@/lib/api";
import { getAnalysisData, getDurationSeconds, setSelectedFighter } from "@/lib/state";

export default function AnalysisScreen() {
  const params = useLocalSearchParams<{
    id: string;
    session_id?: string;
    fighter_id?: string;
  }>();

  const [analysis, setAnalysis] = useState<Analysis | null>(getAnalysisData());
  const [duration, setDuration] = useState(getDurationSeconds());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If we have session params but no cached data, fetch it
    if (!analysis && params.session_id && params.fighter_id) {
      setLoading(true);
      getFighterAnalysis(params.session_id, params.fighter_id)
        .then((res) => {
          setAnalysis(res.analysis);
          setDuration(res.duration_seconds);
          setSelectedFighter(params.fighter_id!, res.analysis);
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [params.session_id, params.fighter_id]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.emptyText}>Loading analysis...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Ionicons name="alert-circle" size={48} color={colors.danger} />
        <Text style={styles.emptyText}>{error}</Text>
      </View>
    );
  }

  if (!analysis) {
    return (
      <View style={styles.centered}>
        <Ionicons name="alert-circle" size={48} color={colors.textMuted} />
        <Text style={styles.emptyText}>No analysis data available.</Text>
        <Text style={styles.emptySubtext}>Go back and analyze a video first.</Text>
      </View>
    );
  }

  const detailed = analysis.detailed_analysis;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Overall Score */}
      <View style={styles.scoreSection}>
        <View style={styles.scoreCircle}>
          <Text style={styles.scoreValue}>{analysis.overall_score}</Text>
          <Text style={styles.scoreLabel}>/ 100</Text>
        </View>
        <Text style={styles.scoreTitle}>Overall Score</Text>
        <Text style={styles.scoreMeta}>
          {analysis.frames_analyzed} frames analyzed | {duration}s video
        </Text>
        {detailed?.overall_summary?.interpretation && (
          <Text style={styles.overallInterpretation}>
            {detailed.overall_summary.interpretation}
          </Text>
        )}
      </View>

      {/* Guard Type Detection */}
      {analysis.guard.guard_type && analysis.guard.guard_type !== "unknown" && (
        <View style={styles.guardTypeBanner}>
          <Ionicons name="shield" size={24} color={colors.primary} />
          <View style={{ flex: 1 }}>
            <Text style={styles.guardTypeTitle}>
              Guard Detected: {detailed?.guard_analysis?.guard_type_name || analysis.guard.guard_type}
            </Text>
          </View>
        </View>
      )}

      {/* Opponent Patterns (if sparring) */}
      {analysis.opponent_patterns && analysis.opponent_patterns.length > 0 && (
        <CollapsibleSection title="Opponent Patterns" icon="eye" defaultOpen>
          {analysis.opponent_patterns.map((pattern, i) => (
            <OpponentPatternCard key={i} pattern={pattern} />
          ))}
        </CollapsibleSection>
      )}

      {/* Guard & Defense */}
      <CollapsibleSection title="Guard & Defense" icon="shield-checkmark" defaultOpen>
        <ScoreBar label="Overall Guard" value={analysis.guard.score} />
        <ScoreBar label="Hand Position" value={analysis.guard.hand_position} />
        <ScoreBar label="Elbow Tuck" value={analysis.guard.elbow_tuck} />
        <ScoreBar label="Consistency" value={analysis.guard.consistency} />
        <MetricRow
          label="Guard Drop Rate"
          value={`${analysis.guard.guard_drop_rate}%`}
          score={100 - analysis.guard.guard_drop_rate}
        />
        {detailed?.guard_analysis?.reasoning && (
          <ReasoningBlock text={detailed.guard_analysis.reasoning} />
        )}
      </CollapsibleSection>

      {/* Stance */}
      <CollapsibleSection title="Stance" icon="body" defaultOpen>
        <MetricRow label="Dominant Stance" value={analysis.stance.dominant} highlight />
        <MetricRow
          label="Consistency"
          value={`${analysis.stance.consistency}%`}
          score={analysis.stance.consistency}
        />
        {analysis.stance.breakdown &&
          Object.entries(analysis.stance.breakdown).map(([stance, pct]) => (
            <MetricRow key={stance} label={`  ${stance}`} value={`${pct}%`} />
          ))}
        {detailed?.stance_analysis?.reasoning && (
          <ReasoningBlock text={detailed.stance_analysis.reasoning} />
        )}
      </CollapsibleSection>

      {/* Footwork */}
      <CollapsibleSection title="Footwork" icon="footsteps">
        <ScoreBar label="Overall Footwork" value={analysis.footwork.score} />
        <ScoreBar label="Lateral Movement" value={analysis.footwork.lateral_movement} />
        <ScoreBar label="Stance Width Consistency" value={analysis.footwork.stance_width_consistency} />
        {detailed?.footwork_analysis?.reasoning && (
          <ReasoningBlock text={detailed.footwork_analysis.reasoning} />
        )}
      </CollapsibleSection>

      {/* Head Movement */}
      <CollapsibleSection title="Head Movement" icon="swap-horizontal">
        <ScoreBar label="Overall" value={analysis.head_movement.score} />
        <MetricRow
          label="Horizontal Variation"
          value={`${analysis.head_movement.horizontal_variation}`}
        />
        <MetricRow
          label="Vertical Variation"
          value={`${analysis.head_movement.vertical_variation}`}
        />
        {detailed?.head_movement_analysis?.reasoning && (
          <ReasoningBlock text={detailed.head_movement_analysis.reasoning} />
        )}
      </CollapsibleSection>

      {/* Balance */}
      <CollapsibleSection title="Balance" icon="scale">
        <ScoreBar label="Overall Balance" value={analysis.balance.score} />
        <ScoreBar label="Center of Gravity" value={analysis.balance.center_of_gravity} />
        <ScoreBar label="Weight Distribution" value={analysis.balance.weight_distribution} />
        {detailed?.balance_analysis?.reasoning && (
          <ReasoningBlock text={detailed.balance_analysis.reasoning} />
        )}
      </CollapsibleSection>

      {/* Punches */}
      {analysis.punches && (
        <CollapsibleSection title="Punch Analysis" icon="flash">
          <MetricRow label="Total Punches" value={`${analysis.punches.total_punches}`} />
          <MetricRow label="Defensive Moves" value={`${analysis.punches.total_defensive_moves}`} />
          <ScoreBar label="Variety" value={analysis.punches.variety_score} />
          <MetricRow
            label="Jab Ratio"
            value={`${analysis.punches.jab_ratio}%`}
            score={Math.min(100, analysis.punches.jab_ratio * 2.5)}
          />
          <Text style={styles.subSectionTitle}>Punch Distribution</Text>
          {Object.entries(analysis.punches.distribution)
            .filter(([_, pct]) => pct > 0)
            .sort(([, a], [, b]) => b - a)
            .map(([move, pct]) => (
              <ScoreBar key={move} label={move.replace(/_/g, " ")} value={pct} maxLabel={`${pct}%`} />
            ))}
          {detailed?.punch_analysis?.reasoning && (
            <ReasoningBlock text={detailed.punch_analysis.reasoning} />
          )}
        </CollapsibleSection>
      )}

      {/* Combination Analysis */}
      {analysis.combinations && (
        <CollapsibleSection title="Combinations" icon="layers">
          <MetricRow
            label="Combinations Detected"
            value={`${analysis.combinations.total_combinations}`}
          />
          <ScoreBar label="Combination Flow" value={analysis.combinations.flow_score} />
          {analysis.combinations.total_single_punches !== undefined && (
            <MetricRow
              label="Single Punches"
              value={`${analysis.combinations.total_single_punches}`}
            />
          )}
          {detailed?.combination_analysis?.reasoning && (
            <ReasoningBlock text={detailed.combination_analysis.reasoning} />
          )}
        </CollapsibleSection>
      )}

      {/* Punch Mechanics */}
      {analysis.punch_mechanics && (
        <CollapsibleSection title="Punch Mechanics" icon="fitness">
          {detailed?.punch_mechanics_analysis?.reasoning && (
            <ReasoningBlock text={detailed.punch_mechanics_analysis.reasoning} />
          )}
        </CollapsibleSection>
      )}

      {/* Event Timeline */}
      {analysis.event_timeline && analysis.event_timeline.length > 0 && (
        <CollapsibleSection title="Event Timeline" icon="time">
          {analysis.event_timeline.slice(0, 20).map((event, i) => (
            <View key={i} style={styles.timelineRow}>
              <Text style={styles.timelineTimestamp}>{event.timestamp}</Text>
              <View
                style={[
                  styles.timelineDot,
                  {
                    backgroundColor:
                      event.type === "punch"
                        ? colors.primary
                        : event.type === "defense"
                        ? colors.accent
                        : colors.warning,
                  },
                ]}
              />
              <Text style={styles.timelineDetail}>{event.detail}</Text>
            </View>
          ))}
          {analysis.event_timeline.length > 20 && (
            <Text style={styles.timelineMore}>
              ... and {analysis.event_timeline.length - 20} more events
            </Text>
          )}
        </CollapsibleSection>
      )}

      {/* Style Comparison */}
      {analysis.style_matches && analysis.style_matches.length > 0 && (
        <CollapsibleSection title="Style Comparison" icon="trophy" defaultOpen>
          {analysis.style_matches.map((match, i) => (
            <StyleMatchCard key={i} match={match} rank={i + 1} />
          ))}
          {detailed?.style_comparison?.reasoning && (
            <ReasoningBlock text={detailed.style_comparison.reasoning} />
          )}
        </CollapsibleSection>
      )}

      {/* Improvement Plan */}
      {detailed?.improvement_plan?.reasoning && (
        <CollapsibleSection title="Improvement Plan" icon="rocket" defaultOpen>
          <ReasoningBlock text={detailed.improvement_plan.reasoning} />
        </CollapsibleSection>
      )}

      {/* Quick Strengths & Improvements */}
      <CollapsibleSection title="Quick Summary" icon="list">
        <Text style={styles.subSectionTitle}>Strengths</Text>
        {analysis.strengths.map((s, i) => (
          <FeedbackItem key={`s-${i}`} text={s} type="strength" />
        ))}
        <Text style={[styles.subSectionTitle, { marginTop: 14 }]}>Areas to Improve</Text>
        {analysis.improvements.map((s, i) => (
          <FeedbackItem key={`i-${i}`} text={s} type="improvement" />
        ))}
      </CollapsibleSection>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function OpponentPatternCard({ pattern }: { pattern: OpponentPattern }) {
  const iconName: keyof typeof Ionicons.glyphMap =
    pattern.type === "exploitable_habit"
      ? "alert-circle"
      : pattern.type === "exploitable_weakness"
      ? "trending-down"
      : pattern.type === "predictable_offense"
      ? "repeat"
      : "information-circle";

  return (
    <View style={styles.opponentCard}>
      <View style={styles.opponentCardHeader}>
        <Ionicons name={iconName} size={20} color={colors.secondary} />
        <Text style={styles.opponentCardTitle}>{pattern.title}</Text>
      </View>
      <Text style={styles.opponentCardDesc}>{pattern.description}</Text>
      <View style={styles.counterAdvice}>
        <Ionicons name="flash" size={16} color={colors.accent} />
        <Text style={styles.counterAdviceText}>{pattern.counter_advice}</Text>
      </View>
    </View>
  );
}

function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={styles.sectionCard}>
      <TouchableOpacity
        style={styles.sectionHeader}
        onPress={() => setOpen(!open)}
        activeOpacity={0.7}
      >
        <Ionicons name={icon} size={22} color={colors.secondary} />
        <Text style={styles.sectionTitle}>{title}</Text>
        <View style={{ flex: 1 }} />
        <Ionicons
          name={open ? "chevron-up" : "chevron-down"}
          size={20}
          color={colors.textMuted}
        />
      </TouchableOpacity>
      {open && children}
    </View>
  );
}

function ReasoningBlock({ text }: { text: string }) {
  if (!text) return null;
  const lines = text.split("\n").filter((l) => l.trim() !== "");
  return (
    <View style={styles.reasoningBlock}>
      <View style={styles.reasoningDivider} />
      {lines.map((line, i) => {
        const isBold = line.startsWith("**") || line.includes("**");
        const isIndent = line.startsWith("  -") || line.startsWith("    -");
        return (
          <Text
            key={i}
            style={[
              styles.reasoningText,
              isBold && styles.reasoningBold,
              isIndent && styles.reasoningIndent,
            ]}
          >
            {line
              .replace(/\*\*/g, "")
              .replace(/^_/, "")
              .replace(/_$/, "")}
          </Text>
        );
      })}
    </View>
  );
}

function ScoreBar({
  label,
  value,
  maxLabel,
}: {
  label: string;
  value: number;
  maxLabel?: string;
}) {
  const pct = Math.min(100, Math.max(0, value));
  const barColor =
    pct >= 70 ? colors.success : pct >= 45 ? colors.warning : colors.danger;
  return (
    <View style={styles.scoreBarRow}>
      <Text style={styles.scoreBarLabel}>{label}</Text>
      <View style={styles.scoreBarTrack}>
        <View
          style={[styles.scoreBarFill, { width: `${pct}%`, backgroundColor: barColor }]}
        />
      </View>
      <Text style={styles.scoreBarValue}>{maxLabel || `${Math.round(pct)}`}</Text>
    </View>
  );
}

function MetricRow({
  label,
  value,
  score,
  highlight,
}: {
  label: string;
  value: string;
  score?: number;
  highlight?: boolean;
}) {
  const valueColor = highlight
    ? colors.primary
    : score !== undefined
    ? score >= 70
      ? colors.success
      : score >= 45
      ? colors.warning
      : colors.danger
    : colors.text;

  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[styles.metricValue, { color: valueColor }]}>{value}</Text>
    </View>
  );
}

function StyleMatchCard({ match, rank }: { match: StyleMatch; rank: number }) {
  const medal = rank === 1 ? "medal" : rank === 2 ? "ribbon" : "star";
  const medalColor = rank === 1 ? "#FFD700" : rank === 2 ? "#C0C0C0" : "#CD7F32";

  return (
    <View style={styles.styleCard}>
      <View style={styles.styleCardHeader}>
        <Ionicons name={medal} size={24} color={medalColor} />
        <View style={styles.styleCardInfo}>
          <Text style={styles.styleFighter}>
            {match.fighter}{" "}
            <Text style={styles.styleNickname}>"{match.nickname}"</Text>
          </Text>
          <Text style={styles.styleType}>{match.style}</Text>
        </View>
        <View style={styles.similarityBadge}>
          <Text style={styles.similarityText}>{match.similarity}%</Text>
        </View>
      </View>
      <Text style={styles.styleDesc}>{match.description}</Text>
    </View>
  );
}

function FeedbackItem({ text, type }: { text: string; type: "strength" | "improvement" }) {
  const icon: keyof typeof Ionicons.glyphMap =
    type === "strength" ? "checkmark-circle" : "arrow-up-circle";
  const iconColor = type === "strength" ? colors.success : colors.secondary;

  return (
    <View style={styles.feedbackRow}>
      <Ionicons name={icon} size={20} color={iconColor} />
      <Text style={styles.feedbackText}>{text}</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20 },
  centered: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  emptyText: { color: colors.textSecondary, fontSize: 18, marginTop: 12 },
  emptySubtext: { color: colors.textMuted, fontSize: 14, marginTop: 4 },

  // Score hero
  scoreSection: { alignItems: "center", marginBottom: 28 },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 4,
    borderColor: colors.primary,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.card,
  },
  scoreValue: { fontSize: 36, fontWeight: "bold", color: colors.primary },
  scoreLabel: { fontSize: 14, color: colors.textMuted },
  scoreTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: colors.text,
    marginTop: 12,
  },
  scoreMeta: { fontSize: 13, color: colors.textMuted, marginTop: 4 },
  overallInterpretation: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 10,
    paddingHorizontal: 16,
    lineHeight: 20,
  },

  // Guard type banner
  guardTypeBanner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.primary,
    gap: 10,
  },
  guardTypeTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: colors.text,
  },

  // Opponent patterns
  opponentCard: {
    backgroundColor: "#0F0F1A",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: colors.secondary,
  },
  opponentCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  opponentCardTitle: {
    fontSize: 14,
    fontWeight: "bold",
    color: colors.text,
    flex: 1,
  },
  opponentCardDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 19,
    marginBottom: 8,
  },
  counterAdvice: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 6,
    backgroundColor: "#141420",
    padding: 10,
    borderRadius: 8,
  },
  counterAdviceText: {
    fontSize: 13,
    color: colors.accent,
    flex: 1,
    lineHeight: 18,
  },

  // Section cards
  sectionCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  sectionTitle: { fontSize: 18, fontWeight: "bold", color: colors.text },

  // Score bars
  scoreBarRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 8,
  },
  scoreBarLabel: {
    width: 130,
    fontSize: 13,
    color: colors.textSecondary,
    textTransform: "capitalize",
  },
  scoreBarTrack: {
    flex: 1,
    height: 10,
    backgroundColor: "#1A1A2E",
    borderRadius: 5,
    overflow: "hidden",
  },
  scoreBarFill: { height: "100%", borderRadius: 5 },
  scoreBarValue: {
    width: 36,
    fontSize: 13,
    color: colors.textMuted,
    textAlign: "right",
    fontWeight: "600",
  },

  // Metric rows
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: "#1A1A2E",
  },
  metricLabel: { fontSize: 14, color: colors.textSecondary },
  metricValue: { fontSize: 14, fontWeight: "600" },

  subSectionTitle: {
    fontSize: 14,
    fontWeight: "bold",
    color: colors.text,
    marginTop: 12,
    marginBottom: 8,
  },

  // Timeline
  timelineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  timelineTimestamp: {
    width: 48,
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: "600",
    fontVariant: ["tabular-nums"],
  },
  timelineDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  timelineDetail: {
    flex: 1,
    fontSize: 13,
    color: colors.textSecondary,
  },
  timelineMore: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "center",
    marginTop: 4,
  },

  // Reasoning blocks (detailed analysis)
  reasoningBlock: {
    marginTop: 14,
    paddingTop: 12,
  },
  reasoningDivider: {
    height: 1,
    backgroundColor: "#1A1A2E",
    marginBottom: 12,
  },
  reasoningText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 20,
    marginBottom: 6,
  },
  reasoningBold: {
    fontWeight: "bold",
    color: colors.text,
    fontSize: 14,
    marginTop: 4,
  },
  reasoningIndent: {
    paddingLeft: 16,
  },

  // Style match cards
  styleCard: {
    backgroundColor: "#0F0F1A",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  styleCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 8,
  },
  styleCardInfo: { flex: 1 },
  styleFighter: { fontSize: 16, fontWeight: "bold", color: colors.text },
  styleNickname: {
    fontSize: 13,
    fontWeight: "normal",
    color: colors.secondary,
    fontStyle: "italic",
  },
  styleType: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  similarityBadge: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  similarityText: { color: colors.white, fontSize: 14, fontWeight: "bold" },
  styleDesc: { fontSize: 12, color: colors.textSecondary, lineHeight: 17 },

  // Feedback
  feedbackRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 12,
    alignItems: "flex-start",
  },
  feedbackText: { flex: 1, fontSize: 14, color: colors.textSecondary, lineHeight: 20 },
});
