import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SlideViewer } from "../components/SlideViewer.tsx";
import { Slide } from "../types/index.ts";

describe("SlideViewer Component", () => {
  const mockSlides: Slide[] = [
    {
      slide_index: 0,
      title: "Hero Title Slide",
      layout_type: "hero_title",
      content: {
        header: "Technical Architecture",
        bullets: ["First key finding", "Second empirical metric"],
        callout: "Key takeaway point",
      },
      notes: "Introductory speaker notes for presenter.",
    },
    {
      slide_index: 1,
      title: "Empirical Benchmarks",
      layout_type: "metrics_chart",
      content: {
        header: "Performance Statistics",
        metric_value: "96.8%",
        metric_label: "Attribution Accuracy",
        bullets: ["Verified on 500 test documents"],
        chart_series: [
          { category: "Baseline", value: 50 },
          { category: "Atlas Hub", value: 96.8 },
        ],
      },
      notes: "Speaker notes describing performance charts.",
    },
  ];

  it("renders slide title, bullets, speaker notes, and navigates between slides", () => {
    render(<SlideViewer slides={mockSlides} templateId="modern-navy" />);

    expect(screen.getByRole("heading", { name: "Hero Title Slide" })).toBeInTheDocument();
    expect(screen.getByText("First key finding")).toBeInTheDocument();
    expect(screen.getByText(/Introductory speaker notes/)).toBeInTheDocument();
    expect(screen.getByText("Slide 1 of 2")).toBeInTheDocument();

    // Click Next slide
    const nextBtn = screen.getByText("Next →");
    fireEvent.click(nextBtn);

    expect(screen.getByRole("heading", { name: "Empirical Benchmarks" })).toBeInTheDocument();
    expect(screen.getAllByText(/96\.8/)[0]).toBeInTheDocument();
    expect(screen.getByText("Attribution Accuracy")).toBeInTheDocument();
    expect(screen.getByText("Slide 2 of 2")).toBeInTheDocument();
  });
});
