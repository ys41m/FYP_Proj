import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import type { Analysis, StyleMatch } from "@/lib/api";

export default function AnalysisScreen() {
  const analysis: Analysis | undefined = (global as any).__lastAnalysis;
  const duration: number = (global as any).__lastDuration || 0;

  if (!analysis) {
    return (
      <View style={styles.centered}>
        <Ionicons name="alert-circle" size={48} color={colors.textMuted} />
        <Text style={styles.emptyText}>No analysis data available.</Text>
        <Text style={styles.emptySubtext}>Go back and analyze a video first.</Text>
      </View>
    );
  }

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
      </View>

      {/* Stance */}
      <SectionCard title="Stance" icon="body">
        <MetricRow
          label="Dominant Stance"
          value={analysis.stance.dominant}
          highlight
        />
        <MetricRow
          label="Consistency"
          value={`${analysis.stance.consistency}%`}
          score={analysis.stance.consistency}
        />
        {analysis.stance.breakdown &&
          Object.entries(analysis.stance.breakdown).map(([stance, pct]) => (
            <MetricRow key={stance} label={`  ${stance}`} value={`${pct}%`} />
          ))}
      </SectionCard>

      {/* Guard */}
      <SectionCard title="Guard & Defense" icon="shield-checkmark">
        <ScoreBar label="Overall Guard" value={analysis.guard.score} />
        <ScoreBar label="Hand Position" value={analysis.guard.hand_position} />
        <ScoreBar label="Elbow Tuck" value={analysis.guard.elbow_tuck} />
        <ScoreBar label="Consistency" value={analysis.guard.consistency} />
        <MetricRow
          label="Guard Drop Rate"
          value={`${analysis.guard.guard_drop_rate}%`}
          score={100 - analysis.guard.guard_drop_rate}
        />
      </SectionCard>

      {/* Footwork */}
      <SectionCard title="Footwork" icon="footsteps">
        <ScoreBar label="Overall Footwork" value={analysis.footwork.score} />
        <ScoreBar
          label="Lateral Movement"
          value={analysis.footwork.lateral_movement}
        />
        <ScoreBar
          label="Stance Width Consistency"
          value={analysis.footwork.stance_width_consistency}
        />
      </SectionCard>

      {/* Head Movement */}
      <SectionCard title="Head Movement" icon="swap-horizontal">
        <ScoreBar label="Overall" value={analysis.head_movement.score} />
        <MetricRow
          label="Horizontal Variation"
          value={`${analysis.head_movement.horizontal_variation}`}
        />
        <MetricRow
          label="Vertical Variation"
          value={`${analysis.head_movement.vertical_variation}`}
        />
      </SectionCard>

      {/* Balance */}
      <SectionCard title="Balance" icon="scale">
        <ScoreBar label="Overall Balance" value={analysis.balance.score} />
        <ScoreBar
          label="Center of Gravity"
          value={analysis.balance.center_of_gravity}
        />
        <ScoreBar
          label="Weight Distribution"
          value={analysis.balance.weight_distribution}
        />
      </SectionCard>

      {/* Punches */}
      {analysis.punches && (
        <SectionCard title="Punch Analysis" icon="flash">
          <MetricRow
            label="Total Punches"
            value={`${analysis.punches.total_punches}`}
          />
          <MetricRow
            label="Defensive Moves"
            value={`${analysis.punches.total_defensive_moves}`}
          />
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
              <ScoreBar
                key={move}
                label={move.replace(/_/g, " ")}
                value={pct}
                maxLabel={`${pct}%`}
              />
            ))}
        </SectionCard>
      )}

      {/* Style Matches */}
      {analysis.style_matches && analysis.style_matches.length > 0 && (
        <SectionCard title="Style Comparison" icon="trophy">
          {analysis.style_matches.map((match, i) => (
            <StyleMatchCard key={i} match={match} rank={i + 1} />
          ))}
        </SectionCard>
      )}

      {/* Strengths */}
      <SectionCard title="Strengths" icon="checkmark-circle">
        {analysis.strengths.map((s, i) => (
          <FeedbackItem key={i} text={s} type="strength" />
        ))}
      </SectionCard>

      {/* Improvements */}
      <SectionCard title="Areas to Improve" icon="trending-up">
        {analysis.improvements.map((s, i) => (
          <FeedbackItem key={i} text={s} type="improvement" />
        ))}
      </SectionCard>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// -- Sub-components --

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.sectionCard}>
      <View style={styles.sectionHeader}>
        <Ionicons name={icon} size={22} color={colors.secondary} />
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      {children}
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
          style={[
            styles.scoreBarFill,
            { width: `${pct}%`, backgroundColor: barColor },
          ]}
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
  const medal =
    rank === 1 ? "medal" : rank === 2 ? "ribbon" : "star";
  const medalColor =
    rank === 1 ? "#FFD700" : rank === 2 ? "#C0C0C0" : "#CD7F32";

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

function FeedbackItem({
  text,
  type,
}: {
  text: string;
  type: "strength" | "improvement";
}) {
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

// -- Styles --

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
    marginBottom: 14,
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
