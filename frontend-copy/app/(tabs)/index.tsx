import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";

export default function HomeScreen() {
  const router = useRouter();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Ionicons name="fitness" size={64} color={colors.primary} />
        <Text style={styles.title}>Strike Stream</Text>
        <Text style={styles.subtitle}>
          AI-Powered Boxing Analysis
        </Text>
        <Text style={styles.description}>
          Upload your sparring clips or famous fight footage and get instant
          feedback on technique, stance, guard, footwork, and more — powered
          by pose estimation and move classification AI.
        </Text>
      </View>

      <TouchableOpacity
        style={styles.ctaButton}
        onPress={() => router.push("/upload")}
      >
        <Ionicons name="cloud-upload" size={24} color={colors.white} />
        <Text style={styles.ctaText}>Analyze a Clip</Text>
      </TouchableOpacity>

      <View style={styles.featuresSection}>
        <Text style={styles.sectionTitle}>What We Analyze</Text>

        <FeatureCard
          icon="shield-checkmark"
          title="Guard & Defense"
          desc="Hand positioning, elbow tuck, guard consistency, and defensive movements."
        />
        <FeatureCard
          icon="footsteps"
          title="Footwork"
          desc="Lateral movement, stance width, balance, and weight distribution."
        />
        <FeatureCard
          icon="flash"
          title="Punch Detection"
          desc="Identifies jabs, crosses, hooks, uppercuts, and combination patterns."
        />
        <FeatureCard
          icon="swap-horizontal"
          title="Head Movement"
          desc="Slips, bobs, weaves — how well you move off the center line."
        />
        <FeatureCard
          icon="trophy"
          title="Style Matching"
          desc="See which legendary fighter your style resembles most: Tyson, Ali, Mayweather, and more."
        />
        <FeatureCard
          icon="analytics"
          title="Detailed Feedback"
          desc="Get specific strengths and areas to improve based on boxing fundamentals."
        />
      </View>

      <TouchableOpacity
        style={[styles.ctaButton, { backgroundColor: colors.accent }]}
        onPress={() => router.push("/presets")}
      >
        <Ionicons name="people" size={24} color={colors.white} />
        <Text style={styles.ctaText}>Explore Fighter Styles</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  desc: string;
}) {
  return (
    <View style={styles.featureCard}>
      <Ionicons name={icon} size={28} color={colors.secondary} />
      <View style={styles.featureText}>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDesc}>{desc}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20 },
  hero: { alignItems: "center", marginTop: 20, marginBottom: 30 },
  title: {
    fontSize: 36,
    fontWeight: "bold",
    color: colors.primary,
    marginTop: 12,
  },
  subtitle: {
    fontSize: 16,
    color: colors.secondary,
    marginTop: 4,
    fontWeight: "600",
  },
  description: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 12,
    lineHeight: 20,
    paddingHorizontal: 10,
  },
  ctaButton: {
    backgroundColor: colors.primary,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    borderRadius: 12,
    gap: 10,
    marginBottom: 30,
  },
  ctaText: { color: colors.white, fontSize: 18, fontWeight: "bold" },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: colors.text,
    marginBottom: 16,
  },
  featuresSection: { marginBottom: 20 },
  featureCard: {
    flexDirection: "row",
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    alignItems: "center",
    gap: 14,
  },
  featureText: { flex: 1 },
  featureTitle: { fontSize: 16, fontWeight: "bold", color: colors.text },
  featureDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    lineHeight: 18,
  },
});
