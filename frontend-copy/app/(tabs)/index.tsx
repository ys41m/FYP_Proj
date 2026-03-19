import React, { useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ImageBackground,
  Modal,
  Animated,
  Dimensions,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";

const { width: SW } = Dimensions.get("window");

const FEATURES = [
  {
    icon: "shield-checkmark" as const,
    title: "Guard & Defense",
    desc: "Hand positioning, elbow tuck, guard consistency.",
    detail:
      "Analyzes your guard quality frame-by-frame — hand positioning, elbow tuck, and how consistently you maintain your guard throughout the fight. Tracks guard drop rate and calculates an overall defense score.",
    accent: colors.primary,
    wide: true,
  },
  {
    icon: "footsteps" as const,
    title: "Footwork",
    desc: "Lateral movement, stance width & balance.",
    detail:
      "Measures lateral movement range, stance width consistency, and weight distribution while moving. Good footwork is the foundation of effective boxing — we score it precisely.",
    accent: colors.primaryLight,
    wide: false,
  },
  {
    icon: "flash" as const,
    title: "Punch Detection",
    desc: "Jabs, crosses, hooks, uppercuts & combos.",
    detail:
      "Identifies and classifies every punch thrown: jab, cross, hook, uppercut, and body shots. Tracks combination flow, punch variety, and overall punch output.",
    accent: colors.accent,
    wide: false,
  },
  {
    icon: "swap-horizontal" as const,
    title: "Head Movement",
    desc: "Slips, bobs, weaves off the center line.",
    detail:
      "Tracks horizontal and vertical head displacement over time — measuring slips, bobs, and weaves. A key defensive skill that separates elite boxers.",
    accent: colors.secondary,
    wide: false,
  },
  {
    icon: "trophy" as const,
    title: "Style Matching",
    desc: "Tyson, Ali, Mayweather & more.",
    detail:
      "Your overall technical profile is compared against legendary fighters: Mike Tyson, Muhammad Ali, Floyd Mayweather, Manny Pacquiao, and more. See who your style resembles most.",
    accent: "#FFD700",
    wide: false,
  },
  {
    icon: "analytics" as const,
    title: "Detailed Feedback",
    desc: "Specific strengths and areas to improve.",
    detail:
      "AI-generated detailed breakdown of every aspect of your technique — with specific strengths to build on and targeted areas for improvement based on boxing fundamentals.",
    accent: colors.success,
    wide: true,
  },
];

export default function HomeScreen() {
  const router = useRouter();
  const [selected, setSelected] = useState<(typeof FEATURES)[0] | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const scaleAnim = useRef(new Animated.Value(0.92)).current;
  const translateY = useRef(new Animated.Value(24)).current;
  const bgOpacity = useRef(new Animated.Value(0)).current;

  const openFeature = (feature: (typeof FEATURES)[0]) => {
    setSelected(feature);
    setModalVisible(true);
    scaleAnim.setValue(0.92);
    translateY.setValue(24);
    bgOpacity.setValue(0);
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 100,
        friction: 9,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
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

  const closeFeature = () => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 0.92,
        tension: 120,
        friction: 10,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 24,
        duration: 180,
        useNativeDriver: true,
      }),
      Animated.timing(bgOpacity, {
        toValue: 0,
        duration: 160,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setModalVisible(false);
      setSelected(null);
    });
  };

  // Split features into rows: wide=full, pair narrow ones
  const rows: Array<(typeof FEATURES)[number][]> = [];
  let i = 0;
  while (i < FEATURES.length) {
    if (FEATURES[i].wide) {
      rows.push([FEATURES[i]]);
      i++;
    } else {
      const pair: (typeof FEATURES)[number][] = [FEATURES[i]];
      if (i + 1 < FEATURES.length && !FEATURES[i + 1].wide) {
        pair.push(FEATURES[i + 1]);
        i += 2;
      } else {
        i++;
      }
      rows.push(pair);
    }
  }

  return (
    <View style={styles.root}>
      {/* Boxing background */}
      <ImageBackground
        source={require("../../assets/boxing-bg.png")}
        style={StyleSheet.absoluteFill}
        imageStyle={{ opacity: 0.07 }}
        resizeMode="cover"
      />

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View style={styles.hero}>
          <Image
            source={require("../../assets/logo.png")}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.subtitle}>AI-Powered Boxing Analysis</Text>
          <Text style={styles.description}>
            Upload your sparring clips or famous fight footage and get instant
            feedback on technique, stance, guard, footwork, and more.
          </Text>
        </View>

        {/* Primary CTA */}
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={() => router.push("/upload")}
          activeOpacity={0.82}
        >
          <Ionicons name="cloud-upload" size={22} color={colors.white} />
          <Text style={styles.ctaText}>Analyze a Clip</Text>
        </TouchableOpacity>

        {/* Bento Grid */}
        <Text style={styles.sectionLabel}>What We Analyze</Text>
        <View style={styles.bentoGrid}>
          {rows.map((row, ri) => (
            <View key={ri} style={styles.bentoRow}>
              {row.map((feature, fi) => (
                <TouchableOpacity
                  key={fi}
                  style={[
                    styles.bentoCard,
                    row.length === 1 ? styles.bentoFull : styles.bentoHalf,
                  ]}
                  onPress={() => openFeature(feature)}
                  activeOpacity={0.72}
                >
                  <View
                    style={[
                      styles.bentoIconWrap,
                      { borderColor: feature.accent + "55" },
                    ]}
                  >
                    <Ionicons
                      name={feature.icon}
                      size={26}
                      color={feature.accent}
                    />
                  </View>
                  <Text style={styles.bentoTitle}>{feature.title}</Text>
                  <Text style={styles.bentoDesc} numberOfLines={2}>
                    {feature.desc}
                  </Text>
                  <View style={styles.bentoCaret}>
                    <Ionicons
                      name="chevron-forward"
                      size={13}
                      color={colors.textMuted}
                    />
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          ))}
        </View>

        {/* Secondary CTA */}
        <TouchableOpacity
          style={[styles.ctaButton, styles.ctaSecondary]}
          onPress={() => router.push("/presets")}
          activeOpacity={0.82}
        >
          <Ionicons name="people" size={22} color={colors.white} />
          <Text style={styles.ctaText}>Explore Fighter Styles</Text>
        </TouchableOpacity>

        <View style={{ height: 48 }} />
      </ScrollView>

      {/* Feature Detail Modal */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="none"
        onRequestClose={closeFeature}
        statusBarTranslucent
      >
        <Animated.View style={[styles.modalOverlay, { opacity: bgOpacity }]}>
          <TouchableOpacity
            style={StyleSheet.absoluteFill}
            activeOpacity={1}
            onPress={closeFeature}
          />
        </Animated.View>

        <View style={styles.modalWrapper} pointerEvents="box-none">
          <Animated.View
            style={[
              styles.modalContent,
              {
                transform: [{ scale: scaleAnim }, { translateY: translateY }],
                opacity: bgOpacity,
              },
            ]}
          >
            <ImageBackground
              source={require("../../assets/boxing-bg.png")}
              style={styles.modalBg}
              imageStyle={{ opacity: 0.06 }}
              resizeMode="cover"
            >
              {/* Close */}
              <TouchableOpacity
                style={styles.modalClose}
                onPress={closeFeature}
                hitSlop={{ top: 12, right: 12, bottom: 12, left: 12 }}
              >
                <Ionicons name="close" size={20} color={colors.textMuted} />
              </TouchableOpacity>

              {/* Icon */}
              <View
                style={[
                  styles.modalIconWrap,
                  {
                    borderColor:
                      (selected?.accent ?? colors.primary) + "80",
                    backgroundColor:
                      (selected?.accent ?? colors.primary) + "18",
                  },
                ]}
              >
                <Ionicons
                  name={selected?.icon ?? "flash"}
                  size={36}
                  color={selected?.accent ?? colors.primary}
                />
              </View>

              <Text
                style={[
                  styles.modalTitle,
                  { color: selected?.accent ?? colors.primary },
                ]}
              >
                {selected?.title}
              </Text>
              <Text style={styles.modalDetail}>{selected?.detail}</Text>

              <TouchableOpacity
                style={[
                  styles.modalCta,
                  {
                    backgroundColor: selected?.accent ?? colors.primary,
                  },
                ]}
                onPress={() => {
                  closeFeature();
                  router.push("/upload");
                }}
                activeOpacity={0.82}
              >
                <Ionicons name="cloud-upload" size={18} color={colors.white} />
                <Text style={styles.ctaText}>Analyze Now</Text>
              </TouchableOpacity>
            </ImageBackground>
          </Animated.View>
        </View>
      </Modal>
    </View>
  );
}

const CARD_GAP = 10;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingTop: 24 },

  hero: { alignItems: "center", marginBottom: 28 },
  logo: { width: SW * 0.55, height: 80 },
  subtitle: {
    fontSize: 14,
    color: colors.secondary,
    marginTop: 10,
    fontWeight: "600",
    letterSpacing: 0.5,
    textTransform: "uppercase",
  },
  description: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: 10,
    lineHeight: 21,
    paddingHorizontal: 8,
  },

  ctaButton: {
    backgroundColor: colors.primary,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    borderRadius: 14,
    gap: 10,
    marginBottom: 28,
    shadowColor: colors.primary,
    shadowOpacity: 0.4,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  ctaSecondary: {
    backgroundColor: colors.primaryDark,
    marginTop: 10,
    marginBottom: 0,
    shadowColor: colors.primaryDark,
  },
  ctaText: { color: colors.white, fontSize: 16, fontWeight: "700" },

  sectionLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.textMuted,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 12,
  },

  bentoGrid: { gap: CARD_GAP },
  bentoRow: {
    flexDirection: "row",
    gap: CARD_GAP,
  },
  bentoCard: {
    backgroundColor: colors.card,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    minHeight: 120,
    overflow: "hidden",
  },
  bentoFull: { flex: 1 },
  bentoHalf: { flex: 1 },

  bentoIconWrap: {
    width: 46,
    height: 46,
    borderRadius: 12,
    borderWidth: 1,
    backgroundColor: "rgba(139,92,246,0.1)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 10,
  },
  bentoTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.text,
    marginBottom: 4,
  },
  bentoDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 17,
    flex: 1,
  },
  bentoCaret: {
    position: "absolute",
    bottom: 12,
    right: 12,
    opacity: 0.6,
  },

  // Modal
  modalOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(8, 4, 18, 0.85)",
  },
  modalWrapper: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContent: {
    width: "100%",
    maxWidth: 480,
    borderRadius: 20,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.cardBorder,
    shadowColor: colors.primary,
    shadowOpacity: 0.3,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 12,
  },
  modalBg: {
    padding: 24,
    backgroundColor: colors.card,
  },
  modalClose: {
    position: "absolute",
    top: 14,
    right: 14,
    zIndex: 10,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "rgba(255,255,255,0.08)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 18,
    borderWidth: 1.5,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 10,
  },
  modalDetail: {
    fontSize: 15,
    color: colors.textSecondary,
    lineHeight: 23,
    marginBottom: 22,
  },
  modalCta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 14,
    borderRadius: 12,
    gap: 8,
  },
});
