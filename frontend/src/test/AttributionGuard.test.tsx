import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AttributionGuardView } from "../components/AttributionGuardView.tsx";
import { EvaluationScorecard } from "../types/index.ts";

describe("AttributionGuardView Component", () => {
  it("renders gate status, exit code, and actionable diagnostic suggestions", () => {
    const mockScorecard: EvaluationScorecard = {
      presentation_id: "pres-1",
      overall_score: 72.5,
      grounding_score: 85.0,
      balance_score: 70.0,
      pacing_score: 65.0,
      consistency_score: 80.0,
      status: "passed",
      summary: "Evaluation PASSED",
      span_groundings: [
        {
          slide_index: 0,
          claim: "Latency is 120 ms end-to-end.",
          matched_source_span: "latency is 120 ms",
          grounding_confidence: 0.95,
          is_grounded: true,
        },
      ],
      diagnostics: [
        {
          code: "ATTR_UNGROUNDED_CLAIM",
          severity: "warning",
          slide_index: 1,
          element: "bullet_0",
          message: "Slide #2 bullet lacks verifiable source grounding.",
          suggestion: "Rephrase bullet to cite documented empirical metrics.",
        },
      ],
    };

    render(
      <AttributionGuardView
        scorecard={mockScorecard}
        onRunEvaluation={vi.fn()}
        loading={false}
      />
    );

    expect(screen.getByText("GATE PASSED (Exit Code 0)")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("[ATTR_UNGROUNDED_CLAIM]")).toBeInTheDocument();
    expect(screen.getByText("Slide #2 bullet lacks verifiable source grounding.")).toBeInTheDocument();
    expect(screen.getByText(/Rephrase bullet to cite documented empirical metrics/)).toBeInTheDocument();
  });
});
