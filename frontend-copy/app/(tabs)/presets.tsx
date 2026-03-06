import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { getPresets, getPresetDetail, type FighterPreset } from "@/lib/api";

// Fallback data if backend is not available
const FALLBACK_PRESETS: FighterPreset[] = [
  {
    key: "mike_tyson",
    name: "Mike Tyson",
    nickname: "Iron Mike",
    style: "Peek-a-Boo / Pressure Fighter",
    stance: "orthodox",
    era: "1985-2005",
    signature_moves: ["peek-a-boo guard", "bobbing", "weaving", "lead hook", "uppercut"],
    description: "Explosive inside fighter with devastating power. Uses the peek-a-boo style with tight guard, constant head movement, and explosive combinations.",
  },
  {
    key: "muhammad_ali",
    name: "Muhammad Ali",
    nickname: "The Greatest",
    style: "Out-Fighter / Counter Puncher",
    stance: "orthodox",
    era: "1960-1981",
    signature_moves: ["jab", "straight right", "pull counter", "lateral movement"],
    description: "Graceful out-fighter who relied on speed, footwork, and reflexes. Masterful jab and exceptional lateral movement.",
  },
  {
    key: "floyd_mayweather",
    name: "Floyd Mayweather Jr.",
    nickname: "Money / Pretty Boy",
    style: "Defensive Counter Puncher",
    stance: "orthodox",
    era: "1996-2017",
    signature_moves: ["shoulder roll", "pull counter", "check hook", "lead right"],
    description: "Defensive genius using the shoulder roll / Philly shell guard. Exceptional at making opponents miss and countering with precision.",
  },
  {
    key: "manny_pacquiao",
    name: "Manny Pacquiao",
    nickname: "Pac-Man",
    style: "Aggressive Swarmer",
    stance: "southpaw",
    era: "1995-2021",
    signature_moves: ["straight left", "lead right hook", "rapid combinations", "angle changes"],
    description: "Explosive southpaw swarmer with blinding hand speed and power in both hands.",
  },
  {
    key: "canelo_alvarez",
    name: "Canelo Alvarez",
    nickname: "Canelo",
    style: "Counter Puncher / Pressure Fighter",
    stance: "orthodox",
    era: "2005-present",
    signature_moves: ["counter right hand", "body shots", "uppercut", "head movement"],
    description: "Technically elite counter puncher with devastating body work. Uses excellent head movement to slip shots.",
  },
  {
    key: "sugar_ray_leonard",
    name: "Sugar Ray Leonard",
    nickname: "Sugar Ray",
    style: "Boxer-Puncher",
    stance: "orthodox",
    era: "1977-1997",
    signature_moves: ["jab", "combinations", "lateral movement", "flurries"],
    description: "Complete boxer-puncher with dazzling hand speed and ring IQ. Could fight inside or outside.",
  },
  {
    key: "joe_frazier",
    name: "Joe Frazier",
    nickname: "Smokin' Joe",
    style: "Swarmer / Pressure Fighter",
    stance: "orthodox",
    era: "1965-1981",
    signature_moves: ["left hook", "body attack", "bobbing", "forward pressure"],
    description: "Relentless pressure fighter with a devastating left hook. Fought from a deep crouch with non-stop body work.",
  },
  {
    key: "lennox_lewis",
    name: "Lennox Lewis",
    nickname: "The Lion",
    style: "Technical Boxer / Out-Fighter",
    stance: "orthodox",
    era: "1989-2003",
    signature_moves: ["jab", "straight right", "uppercut", "distance control"],
    description: "Tall, rangy boxer who controlled fights with one of the best jabs in heavyweight history.",
  },
];

interface TraitDetail {
  traits: Record<string, number>;
}

export default function PresetsScreen() {
  const [presets, setPresets] = useState<FighterPreset[]>(FALLBACK_PRESETS);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [traitDetail, setTraitDetail] = useState<TraitDetail | null>(null);
  const [loadingTraits, setLoadingTraits] = useState(false);

  useEffect(() => {
    getPresets()
      .then((res) => setPresets(res.presets))
      .catch(() => {});
  }, []);

  const handleSelect = async (key: string) => {
    if (selectedKey === key) {
      setSelectedKey(null);
      setTraitDetail(null);
      return;
    }
    setSelectedKey(key);
    setLoadingTraits(true);
    try {
      const res = await getPresetDetail(key);
      setTraitDetail({ traits: res.preset.traits });
    } catch {
      setTraitDetail(null);
    } finally {
      setLoadingTraits(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Fighter Styles</Text>
      <Text style={styles.subheader}>
        Learn about legendary boxing styles. Your analysis will be compared
        against these presets to find your closest match.
      </Text>

      {presets.map((preset) => (
        <TouchableOpacity
          key={preset.key}
          style={[
            styles.card,
            selectedKey === preset.key && styles.cardSelected,
          ]}
          onPress={() => handleSelect(preset.key)}
          activeOpacity={0.7}
        >
          <View style={styles.cardHeader}>
            <View style={styles.cardTitleRow}>
              <Text style={styles.fighterName}>{preset.name}</Text>
              <Text style={styles.nickname}>"{preset.nickname}"</Text>
            </View>
            <Ionicons
              name={selectedKey === preset.key ? "chevron-up" : "chevron-down"}
              size={20}
              color={colors.textMuted}
            />
          </View>

          <View style={styles.tagRow}>
            <Tag label={preset.style} color={colors.primary} />
            <Tag label={preset.stance} color={colors.accent} />
            <Tag label={preset.era} color={colors.textMuted} />
          </View>

          <Text style={styles.description}>{preset.description}</Text>

          <View style={styles.movesRow}>
            {preset.signature_moves.map((move, i) => (
              <View key={i} style={styles.moveBadge}>
                <Text style={styles.moveText}>{move}</Text>
              </View>
            ))}
          </View>

          {selectedKey === preset.key && (
            <View style={styles.traitsSection}>
              {loadingTraits ? (
                <ActivityIndicator color={colors.primary} />
              ) : traitDetail ? (
                <View>
                  <Text style={styles.traitsTitle}>Style Traits</Text>
                  {Object.entries(traitDetail.traits).map(([key, value]) => (
                    <TraitBar
                      key={key}
                      label={key.replace(/_/g, " ")}
                      value={value}
                    />
                  ))}
                </View>
              ) : (
                <Text style={styles.traitsFallback}>
                  Connect to backend to see detailed traits
                </Text>
              )}
            </View>
          )}
        </TouchableOpacity>
      ))}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function Tag({ label, color }: { label: string; color: string }) {
  return (
    <View style={[styles.tag, { borderColor: color }]}>
      <Text style={[styles.tagText, { color }]}>{label}</Text>
    </View>
  );
}

function TraitBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const barColor =
    pct >= 80 ? colors.success : pct >= 50 ? colors.secondary : colors.danger;
  return (
    <View style={styles.traitRow}>
      <Text style={styles.traitLabel}>{label}</Text>
      <View style={styles.traitBarBg}>
        <View
          style={[styles.traitBarFill, { width: `${pct}%`, backgroundColor: barColor }]}
        />
      </View>
      <Text style={styles.traitValue}>{pct}%</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20 },
  header: {
    fontSize: 28,
    fontWeight: "bold",
    color: colors.text,
    marginTop: 10,
  },
  subheader: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: 6,
    marginBottom: 24,
    lineHeight: 20,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  cardSelected: { borderColor: colors.primary },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  cardTitleRow: {},
  fighterName: { fontSize: 20, fontWeight: "bold", color: colors.text },
  nickname: {
    fontSize: 14,
    color: colors.secondary,
    fontStyle: "italic",
    marginTop: 2,
  },
  tagRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 10 },
  tag: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  tagText: { fontSize: 11, fontWeight: "600" },
  description: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 19,
    marginBottom: 10,
  },
  movesRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  moveBadge: {
    backgroundColor: "#1A1A2E",
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  moveText: { color: colors.primary, fontSize: 12, fontWeight: "600" },
  traitsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  traitsTitle: {
    fontSize: 15,
    fontWeight: "bold",
    color: colors.text,
    marginBottom: 12,
  },
  traitsFallback: { color: colors.textMuted, fontSize: 13 },
  traitRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 8,
  },
  traitLabel: {
    width: 120,
    fontSize: 12,
    color: colors.textSecondary,
    textTransform: "capitalize",
  },
  traitBarBg: {
    flex: 1,
    height: 8,
    backgroundColor: "#1A1A2E",
    borderRadius: 4,
    overflow: "hidden",
  },
  traitBarFill: { height: "100%", borderRadius: 4 },
  traitValue: { width: 36, fontSize: 12, color: colors.textMuted, textAlign: "right" },
});
