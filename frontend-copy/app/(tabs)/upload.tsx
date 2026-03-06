import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { Video, ResizeMode } from "expo-av";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { analyzeVideo, type Analysis } from "@/lib/api";

const MAX_DURATION = 120; // 2 minutes in seconds

export default function UploadScreen() {
  const router = useRouter();
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pickVideo = async () => {
    setError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Please grant access to your media library.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["videos"],
      allowsEditing: true,
      quality: 0.8,
      videoMaxDuration: MAX_DURATION,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      if (asset.duration && asset.duration > MAX_DURATION * 1000) {
        setError("Video must be 2 minutes or less.");
        return;
      }
      setVideoUri(asset.uri);
    }
  };

  const recordVideo = async () => {
    setError(null);
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Please grant camera access.");
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ["videos"],
      allowsEditing: true,
      quality: 0.8,
      videoMaxDuration: MAX_DURATION,
    });

    if (!result.canceled && result.assets[0]) {
      setVideoUri(result.assets[0].uri);
    }
  };

  const handleAnalyze = async () => {
    if (!videoUri) return;
    setAnalyzing(true);
    setError(null);

    try {
      const response = await analyzeVideo(videoUri);
      // Store result and navigate to analysis screen
      // Using global state for simplicity (in production, use context or state management)
      (global as any).__lastAnalysis = response.analysis;
      (global as any).__lastDuration = response.duration_seconds;
      router.push("/analysis/latest");
    } catch (err: any) {
      setError(err.message || "Analysis failed. Check your connection and try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Analyze Your Boxing</Text>
      <Text style={styles.subheader}>
        Upload a sparring clip or fight footage (max 2 minutes)
      </Text>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.pickButton} onPress={pickVideo}>
          <Ionicons name="folder-open" size={28} color={colors.white} />
          <Text style={styles.pickButtonText}>Choose Video</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.pickButton, { backgroundColor: colors.accent }]}
          onPress={recordVideo}
        >
          <Ionicons name="videocam" size={28} color={colors.white} />
          <Text style={styles.pickButtonText}>Record</Text>
        </TouchableOpacity>
      </View>

      {videoUri && (
        <View style={styles.previewContainer}>
          <Video
            source={{ uri: videoUri }}
            style={styles.videoPreview}
            useNativeControls
            resizeMode={ResizeMode.CONTAIN}
            isLooping={false}
          />

          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => {
              setVideoUri(null);
              setError(null);
            }}
          >
            <Ionicons name="close-circle" size={20} color={colors.textMuted} />
            <Text style={styles.clearText}>Remove</Text>
          </TouchableOpacity>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Ionicons name="alert-circle" size={20} color={colors.danger} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <TouchableOpacity
        style={[
          styles.analyzeButton,
          (!videoUri || analyzing) && styles.analyzeButtonDisabled,
        ]}
        onPress={handleAnalyze}
        disabled={!videoUri || analyzing}
      >
        {analyzing ? (
          <>
            <ActivityIndicator color={colors.white} size="small" />
            <Text style={styles.analyzeText}>Analyzing...</Text>
          </>
        ) : (
          <>
            <Ionicons name="analytics" size={24} color={colors.white} />
            <Text style={styles.analyzeText}>Analyze Video</Text>
          </>
        )}
      </TouchableOpacity>

      {analyzing && (
        <View style={styles.progressInfo}>
          <Text style={styles.progressText}>
            Extracting poses and classifying moves...
          </Text>
          <Text style={styles.progressSubtext}>
            This may take 30-60 seconds depending on video length.
          </Text>
        </View>
      )}

      <View style={styles.tipsSection}>
        <Text style={styles.tipsTitle}>Tips for best results</Text>
        <Tip text="Film from the side or front — full body visible" />
        <Tip text="Good lighting helps pose detection accuracy" />
        <Tip text="Keep the camera steady (tripod recommended)" />
        <Tip text="Works with sparring, bag work, shadow boxing, or fight footage" />
      </View>
    </ScrollView>
  );
}

function Tip({ text }: { text: string }) {
  return (
    <View style={styles.tipRow}>
      <Ionicons name="checkmark-circle" size={16} color={colors.accent} />
      <Text style={styles.tipText}>{text}</Text>
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
  },
  buttonRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 20,
  },
  pickButton: {
    flex: 1,
    backgroundColor: colors.primary,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  pickButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: "bold",
  },
  previewContainer: {
    marginBottom: 20,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  videoPreview: {
    width: "100%",
    height: 220,
  },
  clearButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 10,
    gap: 6,
  },
  clearText: { color: colors.textMuted, fontSize: 14 },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2D1215",
    padding: 12,
    borderRadius: 8,
    gap: 8,
    marginBottom: 16,
  },
  errorText: { color: colors.danger, fontSize: 14, flex: 1 },
  analyzeButton: {
    backgroundColor: colors.primary,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 18,
    borderRadius: 12,
    gap: 10,
    marginBottom: 16,
  },
  analyzeButtonDisabled: {
    backgroundColor: colors.textMuted,
    opacity: 0.6,
  },
  analyzeText: {
    color: colors.white,
    fontSize: 18,
    fontWeight: "bold",
  },
  progressInfo: {
    alignItems: "center",
    marginBottom: 20,
  },
  progressText: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "600",
  },
  progressSubtext: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 4,
  },
  tipsSection: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: colors.text,
    marginBottom: 12,
  },
  tipRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  tipText: { color: colors.textSecondary, fontSize: 13 },
});
