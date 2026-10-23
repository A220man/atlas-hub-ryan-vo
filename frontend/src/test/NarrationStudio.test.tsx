import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { NarrationStudio } from "../components/NarrationStudio.tsx";
import { NarrationPlan } from "../types/index.ts";

// Mock the apiClient
vi.mock("../api/client.ts", () => ({
  apiClient: {
    generateNarration: vi.fn(),
    exportNarrationVtt: vi.fn(),
    downloadNarrationAudio: vi.fn(),
    downloadSlideAudio: vi.fn(),
  },
}));

import { apiClient } from "../api/client.ts";

const mockPlan: NarrationPlan = {
  presentation_id: "pres-1",
  total_duration_seconds: 120.0,
  estimated_words: 150,
  voice_id: "neutral-presenter",
  target_wpm: 140,
  cues: [
    {
      slide_index: 0,
      slide_title: "Introduction",
      start_time_seconds: 0.0,
      duration_seconds: 30.0,
      speech_text: "Welcome to Atlas Hub.",
      pause_after_seconds: 0.8,
    },
  ],
};

describe("NarrationStudio Component", () => {
  it("renders narration plan stats and audio/vtt download buttons", () => {
    render(
      <NarrationStudio
        presentationId="pres-1"
        narrationPlan={mockPlan}
        onPlanGenerated={vi.fn()}
      />
    );

    // Stats
    expect(screen.getByText("120s")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("140 WPM")).toBeInTheDocument();

    // Download buttons present
    expect(
      screen.getByText("🎧 Download Audio (WAV)")
    ).toBeInTheDocument();
    expect(screen.getByText("📥 Export WebVTT")).toBeInTheDocument();
  });

  it("triggers full-deck audio download via API client", async () => {
    const mockBlob = new Blob([new Uint8Array([0x52, 0x49, 0x46, 0x46])], {
      type: "audio/wav",
    });
    vi.mocked(apiClient.downloadNarrationAudio).mockResolvedValue(mockBlob);

    // Mock URL.createObjectURL / revokeObjectURL (not implemented in jsdom)
    URL.createObjectURL = vi.fn().mockReturnValue("blob:mock-url");
    URL.revokeObjectURL = vi.fn();
    // Suppress jsdom window.alert
    vi.stubGlobal("alert", vi.fn());

    render(
      <NarrationStudio
        presentationId="pres-1"
        narrationPlan={mockPlan}
        onPlanGenerated={vi.fn()}
      />
    );

    const audioBtn = screen.getByText("🎧 Download Audio (WAV)");
    fireEvent.click(audioBtn);

    await waitFor(() => {
      expect(apiClient.downloadNarrationAudio).toHaveBeenCalledWith("pres-1");
    });

    vi.restoreAllMocks();
  });

  it("triggers per-slide audio download via API client", async () => {
    const mockBlob = new Blob([new Uint8Array([0x52, 0x49, 0x46, 0x46])], {
      type: "audio/wav",
    });
    vi.mocked(apiClient.downloadSlideAudio).mockResolvedValue(mockBlob);

    // Mock URL.createObjectURL / revokeObjectURL (not implemented in jsdom)
    URL.createObjectURL = vi.fn().mockReturnValue("blob:mock-url");
    URL.revokeObjectURL = vi.fn();
    // Suppress jsdom window.alert
    vi.stubGlobal("alert", vi.fn());

    render(
      <NarrationStudio
        presentationId="pres-1"
        narrationPlan={mockPlan}
        onPlanGenerated={vi.fn()}
      />
    );

    // Find the per-slide audio button (first slide in the table)
    const slideAudioBtn = screen.getByText("⬇️ WAV");
    fireEvent.click(slideAudioBtn);

    await waitFor(() => {
      expect(apiClient.downloadSlideAudio).toHaveBeenCalledWith("pres-1", 0);
    });

    vi.restoreAllMocks();
  });
});