import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { getFighterAnalysis } from "@/lib/api";
import type { FighterPreview } from "@/lib/api";
import { getSessionResponse, setSelectedFighter } from "@/lib/state";

export default function SelectFighterScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ session_id: string }>();
  const sessionId = params.session_id;

  const sessionResponse = getSessionResponse();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!sessionResponse || !sessionId) {
    return (
      <View style={styles.centered}>
        <Ionicons name="alert-circle" size={48} color={colors.textMuted} />
        <Text style={styles.emptyText}>No analysis session found.</Text>
        <Text style={styles.emptySubtext}>Go back and analyze a video first.</Text>
      </View>
    );
  }

  const fighters = sessionResponse.fighters;
  const overviewImage = sessionResponse.overview_frame_base64;

  const handleSelectFighter = async (fighter: FighterPreview) => {
    setLoading(true);
    setError(null);

    try {
      const response = await getFighterAnalysis(sessionId, fighter.id);
      setSelectedFighter(fighter.id, response.analysis);

      router.push({
        pathname: "/analysis/[id]",
        params: {
          id: "result",
          session_id: sessionId,
          fighter_id: fighter.id,
        },
      });
    } catch (err: any) {
      setError(err.message || "Failed to load fighter analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Who Are You?</Text>
      <Text style={styles.subheader}>
        We detected {fighters.length} fighter{fighters.length > 1 ? "s" : ""} in
        the video. Select yourself to get personalized coaching feedback.
      </Text>

      {/* Overview frame with bounding boxes */}
      {overviewImage ? (
        <View style={styles.overviewContainer}>
          <Image
            source={{ uri: `data:image/jpeg;base64,${overviewImage}` }}
            style={styles.overviewImage}
            resizeMode="contain"
          />
          <Text style={styles.overviewCaption}>
            Fighters identified in your video
          </Text>
        </View>
      ) : null}

      {/* Fighter selection cards */}
      <View style={styles.fighterRow}>
        {fighters.map((fighter) => (
          <TouchableOpacity
            key={fighter.id}
            style={[
              styles.fighterCard,
              { borderColor: fighter.color || colors.cardBorder },
            ]}
            onPress={() => handleSelectFighter(fighter)}
            disabled={loading}
            activeOpacity={0.7}
          >
            {fighter.thumbnail_base64 ? (
              <Image
                source={{
                  uri: `data:image/jpeg;base64,${fighter.thumbnail_base64}`,
                }}
                style={styles.thumbnail}
                resizeMode="cover"
              />
            ) : (
              <View style={[styles.thumbnail, styles.thumbnailPlaceholder]}>
                <Ionicons name="person" size={40} color={colors.textMuted} />
              </View>
            )}

            <View style={styles.fighterInfo}>
              <View
                style={[
                  styles.colorDot,
                  { backgroundColor: fighter.color || colors.primary },
                ]}
              />
              <Text style={styles.fighterLabel}>{fighter.label}</Text>
            </View>

            <View style={styles.fighterMeta}>
              <Text style={styles.metaText}>
                Score: {fighter.overall_score ?? "—"}
              </Text>
              <Text style={styles.metaText}>
                Stance: {fighter.stance ?? "—"}
              </Text>
            </View>

            <View
              style={[
                styles.selectButton,
                { backgroundColor: fighter.color || colors.primary },
              ]}
            >
              <Text style={styles.selectButtonText}>Analyse this fighter</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading your analysis...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Ionicons name="alert-circle" size={20} color={colors.danger} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingBottom: 40 },
  centered: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  emptyText: { color: colors.textSecondary, fontSize: 18, marginTop: 12 },
  emptySubtext: { color: colors.textMuted, fontSize: 14, marginTop: 4 },

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
    marginBottom: 20,
    lineHeight: 20,
  },

  // Overview frame
  overviewContainer: {
    marginBottom: 20,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  overviewImage: {
    width: "100%",
    height: 220,
    backgroundColor: "#000",
  },
  overviewCaption: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "center",
    paddingVertical: 8,
  },

  // Fighter cards
  fighterRow: {
    flexDirection: "row",
    gap: 12,
    flexWrap: "wrap",
  },
  fighterCard: {
    flex: 1,
    minWidth: 150,
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: 2,
    overflow: "hidden",
  },
  thumbnail: {
    width: "100%",
    height: 160,
    backgroundColor: "#0A0A12",
  },
  thumbnailPlaceholder: {
    justifyContent: "center",
    alignItems: "center",
  },
  fighterInfo: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    paddingBottom: 4,
    gap: 8,
  },
  colorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  fighterLabel: {
    fontSize: 16,
    fontWeight: "bold",
    color: colors.text,
  },
  fighterMeta: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    gap: 2,
  },
  metaText: {
    fontSize: 12,
    color: colors.textMuted,
    textTransform: "capitalize",
  },
  selectButton: {
    paddingVertical: 12,
    alignItems: "center",
  },
  selectButtonText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: "bold",
  },

  // Loading / error
  loadingOverlay: {
    alignItems: "center",
    marginTop: 20,
    gap: 10,
  },
  loadingText: {
    color: colors.textSecondary,
    fontSize: 14,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2D1215",
    padding: 12,
    borderRadius: 8,
    gap: 8,
    marginTop: 16,
  },
  errorText: { color: colors.danger, fontSize: 14, flex: 1 },
});
