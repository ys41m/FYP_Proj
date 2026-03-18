import React, { useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Platform,
  TextInput,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { Video, ResizeMode } from "expo-av";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/lib/theme";
import { analyzeVideo, analyzeVideoUrl } from "@/lib/api";
import { setSessionResponse } from "@/lib/state";

const MAX_DURATION = 120; // 2 minutes in seconds

type SourceMode = "file" | "url";

export default function UploadScreen() {
  const router = useRouter();
  const [sourceMode, setSourceMode] = useState<SourceMode>("file");
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Web file input ref
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const pickVideo = async () => {
    setError(null);

    if (Platform.OS === "web") {
      // On web, trigger the hidden file input
      fileInputRef.current?.click();
      return;
    }

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

  const handleWebFileChange = (event: any) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoUri(url);
    }
  };

  const recordVideo = async () => {
    setError(null);

    if (Platform.OS === "web") {
      Alert.alert("Not available", "Recording is not supported on web. Please choose a video file.");
      return;
    }

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
    const isUrl = sourceMode === "url";
    if (!isUrl && !videoUri) return;
    if (isUrl && !videoUrl.trim()) return;

    setAnalyzing(true);
    setProgress(0);
    setError(null);

    try {
      const response = isUrl
        ? await analyzeVideoUrl(videoUrl.trim(), (pct) => setProgress(pct))
        : await analyzeVideo(videoUri!, (pct) => setProgress(pct));

      // Store session response in state
      setSessionResponse(response);

      // If only 1 fighter detected, skip fighter selection
      if (response.fighter_count === 1) {
        router.push({
          pathname: "/analysis/[id]",
          params: {
            id: "result",
            session_id: response.session_id,
            fighter_id: response.fighters[0].id,
          },
        });
      } else {
        // Multiple fighters — go to selection screen
        router.push({
          pathname: "/analysis/select-fighter",
          params: { session_id: response.session_id },
        });
      }
    } catch (err: any) {
      setError(err.message || "Analysis failed. Check your connection and try again.");
    } finally {
      setAnalyzing(false);
      setProgress(0);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Analyze Your Boxing</Text>
      <Text style={styles.subheader}>
        Upload a sparring clip, fight footage, or paste a YouTube link (max 2 minutes).
        We'll track all fighters and let you choose who you are after.
      </Text>

      {/* Source mode toggle */}
      <View style={styles.modeToggle}>
        <TouchableOpacity
          style={[styles.modeTab, sourceMode === "file" && styles.modeTabActive]}
          onPress={() => setSourceMode("file")}
        >
          <Ionicons
            name="cloud-upload"
            size={18}
            color={sourceMode === "file" ? colors.white : colors.textMuted}
          />
          <Text
            style={[styles.modeTabText, sourceMode === "file" && styles.modeTabTextActive]}
          >
            Upload File
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.modeTab, sourceMode === "url" && styles.modeTabActive]}
          onPress={() => setSourceMode("url")}
        >
          <Ionicons
            name="link"
            size={18}
            color={sourceMode === "url" ? colors.white : colors.textMuted}
          />
          <Text
            style={[styles.modeTabText, sourceMode === "url" && styles.modeTabTextActive]}
          >
            Paste URL
          </Text>
        </TouchableOpacity>
      </View>

      {sourceMode === "file" ? (
        <>
          {/* Hidden web file input */}
          {Platform.OS === "web" && (
            <input
              ref={fileInputRef as any}
              type="file"
              accept="video/*"
              style={{ display: "none" }}
              onChange={handleWebFileChange}
            />
          )}

          {/* Video source buttons */}
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

          {/* Video preview */}
          {videoUri && (
            <View style={styles.previewContainer}>
              {Platform.OS === "web" ? (
                <video
                  src={videoUri}
                  controls
                  style={{ width: "100%", height: 220, objectFit: "contain", backgroundColor: "#000" }}
                />
              ) : (
                <Video
                  source={{ uri: videoUri }}
                  style={styles.videoPreview}
                  useNativeControls
                  resizeMode={ResizeMode.CONTAIN}
                  isLooping={false}
                />
              )}
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
        </>
      ) : (
        /* URL input */
        <View style={styles.urlSection}>
          <TextInput
            style={styles.urlInput}
            placeholder="Paste a YouTube or video URL..."
            placeholderTextColor={colors.textMuted}
            value={videoUrl}
            onChangeText={setVideoUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            editable={!analyzing}
          />
          {videoUrl.trim() !== "" && (
            <TouchableOpacity
              style={styles.urlClearButton}
              onPress={() => {
                setVideoUrl("");
                setError(null);
              }}
            >
              <Ionicons name="close-circle" size={20} color={colors.textMuted} />
            </TouchableOpacity>
          )}
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
          ((sourceMode === "file" && !videoUri) ||
            (sourceMode === "url" && !videoUrl.trim()) ||
            analyzing) &&
            styles.analyzeButtonDisabled,
        ]}
        onPress={handleAnalyze}
        disabled={
          (sourceMode === "file" && !videoUri) ||
          (sourceMode === "url" && !videoUrl.trim()) ||
          analyzing
        }
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

      {/* Progress bar */}
      {analyzing && (
        <View style={styles.progressSection}>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressFill,
                { width: `${Math.max(5, progress)}%` },
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            {progress < 90
              ? sourceMode === "url"
                ? "Downloading and detecting fighters..."
                : "Uploading and detecting fighters..."
              : "Running boxing analysis..."}
          </Text>
          <Text style={styles.progressSubtext}>
            {sourceMode === "url"
              ? "Downloading and analysing may take 1-2 minutes."
              : "This may take 30-60 seconds depending on video length."}
          </Text>
        </View>
      )}

      <View style={styles.tipsSection}>
        <Text style={styles.tipsTitle}>Tips for best results</Text>
        <Tip text="Film from the side or front — full body visible" />
        <Tip text="Good lighting helps pose detection accuracy" />
        <Tip text="Keep the camera steady (tripod recommended)" />
        <Tip text="Works with sparring, bag work, shadow boxing, or fight footage" />
        <Tip text="Both fighters are tracked — you choose who you are after analysis" />
        <Tip text="Paste a YouTube or direct video URL to analyse fight footage online" />
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
  content: { padding: 20, paddingBottom: 40 },
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
  modeToggle: {
    flexDirection: "row",
    backgroundColor: colors.card,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 4,
    marginBottom: 16,
  },
  modeTab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  modeTabActive: {
    backgroundColor: colors.primary,
  },
  modeTabText: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textMuted,
  },
  modeTabTextActive: {
    color: colors.white,
  },
  urlSection: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  urlInput: {
    flex: 1,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: colors.text,
    fontSize: 15,
  },
  urlClearButton: {
    position: "absolute",
    right: 12,
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
    marginBottom: 16,
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
  progressSection: {
    alignItems: "center",
    marginBottom: 20,
  },
  progressTrack: {
    width: "100%",
    height: 6,
    backgroundColor: colors.cardBorder,
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 10,
  },
  progressFill: {
    height: "100%",
    backgroundColor: colors.primary,
    borderRadius: 3,
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
