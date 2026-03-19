import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Animated,
  Dimensions,
  ImageBackground,
  Platform,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { getFighterAnalysis } from "@/lib/api";
import type {
  Analysis,
  StyleMatch,
  OpponentPattern,
} from "@/lib/api";
import {
  getAnalysisData,
  getDurationSeconds,
  setSelectedFighter,
} from "@/lib/state";

const { height: SH } = Dimensions.get("window");

// ---------------------------------------------------------------------------
// Main Screen
// ---------------------------------------------------------------------------

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
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const scaleAnim = useRef(new Animated.Value(0.92)).current;
  const translateYAnim = useRef(new Animated.Value(30)).current;
  const bgOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
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

  const openSection = (id: string) => {
    setExpandedId(id);
    scaleAnim.setValue(0.92);
    translateYAnim.setValue(30);
    bgOpacity.setValue(0);
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 100,
        friction: 9,
        useNativeDriver: true,
      }),
      Animated.timing(translateYAnim, {
        toValue: 0,
        duration: 260,
        useNativeDriver: true,
      }),
      Animated.timing(bgOpacity, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const closeSection = () => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 0.92,
        tension: 120,
        friction: 10,
        useNativeDriver: true,
      }),
      Animated.timing(translateYAnim, {
        toValue: 30,
        duration: 180,
        useNativeDriver: true,
      }),
      Animated.timing(bgOpacity, {
        toValue: 0,
        duration: 160,
        useNativeDriver: true,
      }),
    ]).start(() => setExpandedId(null));
  };

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
        <Text style={styles.emptySubtext}>
          Go back and analyze a video first.
        </Text>
      </View>
    );
  }

  const detailed = analysis.detailed_analysis;

  // Build bento sections
  const sections: BentoSectionDef[] = [
    {
      id: "guard",
      title: "Guard & Defense",
      icon: "shield-checkmark",
      accent: colors.primary,
      summary: `Score: ${Math.round(analysis.guard.score)}`,
      score: analysis.guard.score,
      renderDetail: () => (
        <>
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
        </>
      ),
    },
    {
      id: "stance",
      title: "Stance",
      icon: "body",
      accent: colors.primaryLight,
      summary: analysis.stance.dominant,
      score: analysis.stance.consistency,
      renderDetail: () => (
        <>
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
            Object.entries(analysis.stance.breakdown).map(([s, pct]) => (
              <MetricRow key={s} label={`  ${s}`} value={`${pct}%`} />
            ))}
          {detailed?.stance_analysis?.reasoning && (
            <ReasoningBlock text={detailed.stance_analysis.reasoning} />
          )}
        </>
      ),
    },
    {
      id: "footwork",
      title: "Footwork",
      icon: "footsteps",
      accent: colors.accent,
      summary: `Score: ${Math.round(analysis.footwork.score)}`,
      score: analysis.footwork.score,
      renderDetail: () => (
        <>
          <ScoreBar
            label="Overall Footwork"
            value={analysis.footwork.score}
          />
          <ScoreBar
            label="Lateral Movement"
            value={analysis.footwork.lateral_movement}
          />
          <ScoreBar
            label="Stance Width Consistency"
            value={analysis.footwork.stance_width_consistency}
          />
          {detailed?.footwork_analysis?.reasoning && (
            <ReasoningBlock text={detailed.footwork_analysis.reasoning} />
          )}
        </>
      ),
    },
    {
      id: "head_movement",
      title: "Head Movement",
      icon: "swap-horizontal",
      accent: colors.secondary,
      summary: `Score: ${Math.round(analysis.head_movement.score)}`,
      score: analysis.head_movement.score,
      renderDetail: () => (
        <>
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
        </>
      ),
    },
    {
      id: "balance",
      title: "Balance",
      icon: "scale",
      accent: "#A78BFA",
      summary: `Score: ${Math.round(analysis.balance.score)}`,
      score: analysis.balance.score,
      renderDetail: () => (
        <>
          <ScoreBar label="Overall Balance" value={analysis.balance.score} />
          <ScoreBar
            label="Center of Gravity"
            value={analysis.balance.center_of_gravity}
          />
          <ScoreBar
            label="Weight Distribution"
            value={analysis.balance.weight_distribution}
          />
          {detailed?.balance_analysis?.reasoning && (
            <ReasoningBlock text={detailed.balance_analysis.reasoning} />
          )}
        </>
      ),
    },
    ...(analysis.punches
      ? [
          {
            id: "punches",
            title: "Punch Analysis",
            icon: "flash" as const,
            accent: "#F59E0B",
            summary: `${analysis.punches.total_punches} punches`,
            score: analysis.punches.variety_score,
            renderDetail: () => (
              <>
                <MetricRow
                  label="Total Punches"
                  value={`${analysis.punches!.total_punches}`}
                />
                <MetricRow
                  label="Defensive Moves"
                  value={`${analysis.punches!.total_defensive_moves}`}
                />
                <ScoreBar
                  label="Variety"
                  value={analysis.punches!.variety_score}
                />
                <MetricRow
                  label="Jab Ratio"
                  value={`${analysis.punches!.jab_ratio}%`}
                  score={Math.min(100, analysis.punches!.jab_ratio * 2.5)}
                />
                <Text style={styles.subLabel}>Punch Distribution</Text>
                {Object.entries(analysis.punches!.distribution)
                  .filter(([, pct]) => pct > 0)
                  .sort(([, a], [, b]) => b - a)
                  .map(([move, pct]) => (
                    <ScoreBar
                      key={move}
                      label={move.replace(/_/g, " ")}
                      value={pct}
                      maxLabel={`${pct}%`}
                    />
                  ))}
                {detailed?.punch_analysis?.reasoning && (
                  <ReasoningBlock text={detailed.punch_analysis.reasoning} />
                )}
              </>
            ),
          } as BentoSectionDef,
        ]
      : []),
    ...(analysis.combinations
      ? [
          {
            id: "combinations",
            title: "Combinations",
            icon: "layers" as const,
            accent: "#22C55E",
            summary: `${analysis.combinations.total_combinations} combos`,
            score: analysis.combinations.flow_score,
            renderDetail: () => (
              <>
                <MetricRow
                  label="Combinations"
                  value={`${analysis.combinations!.total_combinations}`}
                />
                <ScoreBar
                  label="Flow Score"
                  value={analysis.combinations!.flow_score}
                />
                {analysis.combinations!.total_single_punches !== undefined && (
                  <MetricRow
                    label="Single Punches"
                    value={`${analysis.combinations!.total_single_punches}`}
                  />
                )}
                {detailed?.combination_analysis?.reasoning && (
                  <ReasoningBlock
                    text={detailed.combination_analysis.reasoning}
                  />
                )}
              </>
            ),
          } as BentoSectionDef,
        ]
      : []),
    ...(analysis.style_matches && analysis.style_matches.length > 0
      ? [
          {
            id: "style",
            title: "Style Comparison",
            icon: "trophy" as const,
            accent: "#FFD700",
            summary: `#1: ${analysis.style_matches[0].fighter}`,
            score: analysis.style_matches[0].similarity,
            wide: true,
            renderDetail: () => (
              <>
                {analysis.style_matches.map((match, i) => (
                  <StyleMatchCard key={i} match={match} rank={i + 1} />
                ))}
                {detailed?.style_comparison?.reasoning && (
                  <ReasoningBlock text={detailed.style_comparison.reasoning} />
                )}
              </>
            ),
          } as BentoSectionDef,
        ]
      : []),
    ...(analysis.event_timeline && analysis.event_timeline.length > 0
      ? [
          {
            id: "timeline",
            title: "Event Timeline",
            icon: "time" as const,
            accent: colors.accent,
            summary: `${analysis.event_timeline.length} events`,
            renderDetail: () => (
              <>
                {analysis.event_timeline!.slice(0, 30).map((event, i) => (
                  <View key={i} style={styles.timelineRow}>
                    <Text style={styles.timelineTs}>{event.timestamp}</Text>
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
                {analysis.event_timeline!.length > 30 && (
                  <Text style={styles.timelineMore}>
                    ... and {analysis.event_timeline!.length - 30} more events
                  </Text>
                )}
              </>
            ),
          } as BentoSectionDef,
        ]
      : []),
    ...(detailed?.improvement_plan?.reasoning
      ? [
          {
            id: "improvement",
            title: "Improvement Plan",
            icon: "rocket" as const,
            accent: "#E879F9",
            summary: "View your plan",
            wide: true,
            renderDetail: () => (
              <ReasoningBlock text={detailed.improvement_plan!.reasoning} />
            ),
          } as BentoSectionDef,
        ]
      : []),
    {
      id: "summary",
      title: "Quick Summary",
      icon: "list",
      accent: colors.success,
      summary: `${analysis.strengths.length} strengths · ${analysis.improvements.length} to improve`,
      wide: true,
      renderDetail: () => (
        <>
          <Text style={styles.subLabel}>Strengths</Text>
          {analysis.strengths.map((s, i) => (
            <FeedbackItem key={`s-${i}`} text={s} type="strength" />
          ))}
          <Text style={[styles.subLabel, { marginTop: 14 }]}>
            Areas to Improve
          </Text>
          {analysis.improvements.map((s, i) => (
            <FeedbackItem key={`i-${i}`} text={s} type="improvement" />
          ))}
        </>
      ),
    },
  ];

  // Build rows from sections
  const rows: BentoSectionDef[][] = [];
  let si = 0;
  while (si < sections.length) {
    if (sections[si].wide) {
      rows.push([sections[si]]);
      si++;
    } else {
      const pair: BentoSectionDef[] = [sections[si]];
      if (si + 1 < sections.length && !sections[si + 1].wide) {
        pair.push(sections[si + 1]);
        si += 2;
      } else {
        si++;
      }
      rows.push(pair);
    }
  }

  const expandedSection = sections.find((s) => s.id === expandedId);

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Score Hero Card */}
        <View style={styles.scoreHero}>
          <ImageBackground
            source={require("../../assets/boxing-bg.png")}
            style={StyleSheet.absoluteFill}
            imageStyle={{ opacity: 0.06 }}
            resizeMode="cover"
          />
          <View style={styles.scoreCircle}>
            <Text style={styles.scoreValue}>{analysis.overall_score}</Text>
            <Text style={styles.scoreLabel}>/ 100</Text>
          </View>
          <View style={styles.scoreInfo}>
            <Text style={styles.scoreTitle}>Overall Score</Text>
            <Text style={styles.scoreMeta}>
              {analysis.frames_analyzed} frames · {duration}s
            </Text>
            {detailed?.overall_summary?.interpretation && (
              <Text style={styles.scoreInterpretation} numberOfLines={3}>
                {detailed.overall_summary.interpretation}
              </Text>
            )}
          </View>
        </View>

        {/* Guard type banner */}
        {analysis.guard.guard_type &&
          analysis.guard.guard_type !== "unknown" && (
            <View style={styles.guardBanner}>
              <Ionicons name="shield" size={20} color={colors.primary} />
              <Text style={styles.guardBannerText}>
                Guard:{" "}
                {detailed?.guard_analysis?.guard_type_name ||
                  analysis.guard.guard_type}
              </Text>
            </View>
          )}

        {/* Opponent Patterns */}
        {analysis.opponent_patterns &&
          analysis.opponent_patterns.length > 0 && (
            <TouchableOpacity
              style={[styles.opponentBento, styles.bentoCard]}
              onPress={() => openSection("__opponent__")}
              activeOpacity={0.75}
            >
              <View style={styles.bentoBadgeRow}>
                <Ionicons name="eye" size={20} color={colors.warning} />
                <Text style={styles.bentoCardTitle}>Opponent Patterns</Text>
                <View style={styles.expandBadge}>
                  <Text style={styles.expandBadgeText}>
                    {analysis.opponent_patterns.length}
                  </Text>
                </View>
              </View>
              <Text style={styles.bentoCardSummary}>
                Tap to view opponent habits & counter advice
              </Text>
              <Ionicons
                name="chevron-forward"
                size={13}
                color={colors.textMuted}
                style={styles.cardCaret}
              />
            </TouchableOpacity>
          )}

        {/* Bento Grid */}
        <Text style={styles.gridLabel}>Analysis Breakdown</Text>
        <View style={styles.bentoGrid}>
          {rows.map((row, ri) => (
            <View key={ri} style={styles.bentoRow}>
              {row.map((section) => (
                <TouchableOpacity
                  key={section.id}
                  style={[
                    styles.bentoCard,
                    row.length === 1 ? styles.bentoFull : styles.bentoHalf,
                  ]}
                  onPress={() => openSection(section.id)}
                  activeOpacity={0.75}
                >
                  <View
                    style={[
                      styles.bentoIconBadge,
                      { borderColor: section.accent + "55" },
                    ]}
                  >
                    <Ionicons
                      name={section.icon}
                      size={20}
                      color={section.accent}
                    />
                  </View>
                  <Text style={styles.bentoCardTitle}>{section.title}</Text>
                  <Text style={styles.bentoCardSummary} numberOfLines={1}>
                    {section.summary}
                  </Text>
                  {section.score !== undefined && (
                    <View style={styles.miniBarTrack}>
                      <View
                        style={[
                          styles.miniBarFill,
                          {
                            width: `${Math.min(100, Math.max(0, section.score))}%` as any,
                            backgroundColor:
                              section.score >= 70
                                ? colors.success
                                : section.score >= 45
                                ? colors.warning
                                : colors.danger,
                          },
                        ]}
                      />
                    </View>
                  )}
                  <Ionicons
                    name="chevron-forward"
                    size={13}
                    color={colors.textMuted}
                    style={styles.cardCaret}
                  />
                </TouchableOpacity>
              ))}
            </View>
          ))}
        </View>

        <View style={{ height: 48 }} />
      </ScrollView>

      {/* Expand Modal */}
      <Modal
        visible={expandedId !== null}
        transparent
        animationType="none"
        onRequestClose={closeSection}
        statusBarTranslucent
      >
        <Animated.View
          style={[styles.modalOverlay, { opacity: bgOpacity }]}
        >
          <TouchableOpacity
            style={StyleSheet.absoluteFill}
            activeOpacity={1}
            onPress={closeSection}
          />
        </Animated.View>

        <View style={styles.modalWrapper} pointerEvents="box-none">
          <Animated.View
            style={[
              styles.modalSheet,
              {
                transform: [
                  { scale: scaleAnim },
                  { translateY: translateYAnim },
                ],
                opacity: bgOpacity,
              },
            ]}
          >
            {/* Header */}
            <View style={styles.modalHeader}>
              {expandedId === "__opponent__" ? (
                <Ionicons name="eye" size={22} color={colors.warning} />
              ) : (
                <Ionicons
                  name={expandedSection?.icon ?? "analytics"}
                  size={22}
                  color={expandedSection?.accent ?? colors.primary}
                />
              )}
              <Text
                style={[
                  styles.modalTitle,
                  {
                    color:
                      expandedId === "__opponent__"
                        ? colors.warning
                        : (expandedSection?.accent ?? colors.primary),
                  },
                ]}
              >
                {expandedId === "__opponent__"
                  ? "Opponent Patterns"
                  : expandedSection?.title}
              </Text>
              <TouchableOpacity
                onPress={closeSection}
                style={styles.modalCloseBtn}
                hitSlop={{ top: 12, right: 12, bottom: 12, left: 12 }}
              >
                <Ionicons name="close" size={20} color={colors.textMuted} />
              </TouchableOpacity>
            </View>

            <ScrollView
              style={styles.modalBody}
              contentContainerStyle={{ paddingBottom: 24 }}
              showsVerticalScrollIndicator={false}
            >
              {expandedId === "__opponent__"
                ? analysis.opponent_patterns?.map((p, i) => (
                    <OpponentPatternCard key={i} pattern={p} />
                  ))
                : expandedSection?.renderDetail()}
            </ScrollView>
          </Animated.View>
        </View>
      </Modal>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BentoSectionDef {
  id: string;
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  accent: string;
  summary: string;
  score?: number;
  wide?: boolean;
  renderDetail: () => React.ReactNode;
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
      <View style={styles.opponentCardHead}>
        <Ionicons name={iconName} size={18} color={colors.warning} />
        <Text style={styles.opponentCardTitle}>{pattern.title}</Text>
      </View>
      <Text style={styles.opponentCardDesc}>{pattern.description}</Text>
      <View style={styles.counterAdvice}>
        <Ionicons name="flash" size={14} color={colors.accent} />
        <Text style={styles.counterAdviceText}>{pattern.counter_advice}</Text>
      </View>
    </View>
  );
}

function ReasoningBlock({ text }: { text: string }) {
  if (!text) return null;
  const lines = text.split("\n").filter((l) => l.trim() !== "");
  return (
    <View style={styles.reasoning}>
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
            {line.replace(/\*\*/g, "").replace(/^_/, "").replace(/_$/, "")}
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
          style={[
            styles.scoreBarFill,
            { width: `${pct}%`, backgroundColor: barColor },
          ]}
        />
      </View>
      <Text style={styles.scoreBarValue}>
        {maxLabel || `${Math.round(pct)}`}
      </Text>
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
  const medalColor =
    rank === 1 ? "#FFD700" : rank === 2 ? "#C0C0C0" : "#CD7F32";

  return (
    <View style={styles.styleCard}>
      <View style={styles.styleCardHead}>
        <Ionicons name={medal} size={22} color={medalColor} />
        <View style={styles.styleCardInfo}>
          <Text style={styles.styleFighter}>
            {match.fighter}{" "}
            <Text style={styles.styleNickname}>"{match.nickname}"</Text>
          </Text>
          <Text style={styles.styleType}>{match.style}</Text>
        </View>
        <View style={styles.simBadge}>
          <Text style={styles.simText}>{match.similarity}%</Text>
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
  const iconColor = type === "strength" ? colors.success : colors.accent;

  return (
    <View style={styles.feedbackRow}>
      <Ionicons name={icon} size={18} color={iconColor} />
      <Text style={styles.feedbackText}>{text}</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const CARD_GAP = 10;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  centered: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  emptyText: { color: colors.textSecondary, fontSize: 17, marginTop: 12 },
  emptySubtext: { color: colors.textMuted, fontSize: 13, marginTop: 4 },

  // Score hero
  scoreHero: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderRadius: 18,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    gap: 16,
    overflow: "hidden",
  },
  scoreCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 3,
    borderColor: colors.primary,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: colors.primary,
    shadowOpacity: 0.4,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 6,
  },
  scoreValue: {
    fontSize: 30,
    fontWeight: "800",
    color: colors.primary,
  },
  scoreLabel: { fontSize: 12, color: colors.textMuted },
  scoreInfo: { flex: 1 },
  scoreTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: colors.text,
    marginBottom: 2,
  },
  scoreMeta: { fontSize: 12, color: colors.textMuted, marginBottom: 6 },
  scoreInterpretation: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 19,
  },

  // Guard banner
  guardBanner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.primary + "60",
    gap: 8,
  },
  guardBannerText: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.text,
  },

  gridLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.textMuted,
    letterSpacing: 1.1,
    textTransform: "uppercase",
    marginBottom: 10,
    marginTop: 4,
  },

  // Bento grid
  bentoGrid: { gap: CARD_GAP },
  bentoRow: {
    flexDirection: "row",
    gap: CARD_GAP,
  },
  bentoCard: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    minHeight: 100,
    overflow: "hidden",
  },
  bentoFull: { flex: 1 },
  bentoHalf: { flex: 1 },
  opponentBento: { marginBottom: 4 },

  bentoBadgeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  expandBadge: {
    backgroundColor: colors.warning + "30",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginLeft: "auto",
  },
  expandBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.warning,
  },

  bentoIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    borderWidth: 1,
    backgroundColor: "rgba(139,92,246,0.1)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  bentoCardTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.text,
    marginBottom: 3,
  },
  bentoCardSummary: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 8,
  },
  miniBarTrack: {
    height: 4,
    backgroundColor: "#2A1B4E",
    borderRadius: 2,
    overflow: "hidden",
    marginTop: "auto" as any,
  },
  miniBarFill: {
    height: "100%",
    borderRadius: 2,
  },
  cardCaret: {
    position: "absolute",
    bottom: 10,
    right: 10,
    opacity: 0.5,
  },

  // Modal
  modalOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(8, 4, 18, 0.88)",
  },
  modalWrapper: {
    flex: 1,
    justifyContent: "flex-end",
    paddingHorizontal: 12,
    paddingBottom: Platform.OS === "ios" ? 32 : 16,
  },
  modalSheet: {
    backgroundColor: colors.card,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    maxHeight: SH * 0.82,
    shadowColor: colors.primary,
    shadowOpacity: 0.25,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: -4 },
    elevation: 16,
    overflow: "hidden",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 18,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: "800",
    flex: 1,
  },
  modalCloseBtn: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "rgba(255,255,255,0.07)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalBody: {
    paddingHorizontal: 18,
    paddingTop: 14,
  },

  // Score bars
  scoreBarRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 8,
  },
  scoreBarLabel: {
    width: 140,
    fontSize: 13,
    color: colors.textSecondary,
    textTransform: "capitalize",
  },
  scoreBarTrack: {
    flex: 1,
    height: 8,
    backgroundColor: "#1A1030",
    borderRadius: 4,
    overflow: "hidden",
  },
  scoreBarFill: { height: "100%", borderRadius: 4 },
  scoreBarValue: {
    width: 34,
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "right",
    fontWeight: "600",
  },

  // Metric rows
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 7,
    borderBottomWidth: 1,
    borderBottomColor: "#1A1030",
  },
  metricLabel: { fontSize: 14, color: colors.textSecondary },
  metricValue: { fontSize: 14, fontWeight: "600" },

  subLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.text,
    marginTop: 12,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },

  // Timeline
  timelineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  timelineTs: {
    width: 48,
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: "600",
  },
  timelineDot: { width: 8, height: 8, borderRadius: 4 },
  timelineDetail: { flex: 1, fontSize: 13, color: colors.textSecondary },
  timelineMore: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "center",
    marginTop: 4,
  },

  // Reasoning
  reasoning: { marginTop: 12, paddingTop: 12 },
  reasoningDivider: {
    height: 1,
    backgroundColor: "#1A1030",
    marginBottom: 10,
  },
  reasoningText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 20,
    marginBottom: 5,
  },
  reasoningBold: {
    fontWeight: "700",
    color: colors.text,
    fontSize: 14,
    marginTop: 4,
  },
  reasoningIndent: { paddingLeft: 14 },

  // Style match
  styleCard: {
    backgroundColor: "#0F0A1E",
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  styleCardHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 8,
  },
  styleCardInfo: { flex: 1 },
  styleFighter: { fontSize: 15, fontWeight: "700", color: colors.text },
  styleNickname: {
    fontSize: 13,
    fontWeight: "normal",
    color: colors.secondary,
    fontStyle: "italic",
  },
  styleType: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  simBadge: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  simText: { color: colors.white, fontSize: 13, fontWeight: "700" },
  styleDesc: { fontSize: 12, color: colors.textSecondary, lineHeight: 17 },

  // Feedback
  feedbackRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 10,
    alignItems: "flex-start",
  },
  feedbackText: {
    flex: 1,
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
  },

  // Opponent pattern
  opponentCard: {
    backgroundColor: "#0F0A1E",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: colors.warning,
  },
  opponentCardHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  opponentCardTitle: {
    fontSize: 14,
    fontWeight: "700",
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
    backgroundColor: "#120E22",
    padding: 10,
    borderRadius: 8,
  },
  counterAdviceText: {
    fontSize: 13,
    color: colors.accent,
    flex: 1,
    lineHeight: 18,
  },
});
