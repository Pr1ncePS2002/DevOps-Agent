"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TourStep } from "./tour-steps";

interface GuidedTourProps {
  steps: TourStep[];
  onComplete: () => void;
}

export function GuidedTour({ steps, onComplete }: GuidedTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
  const [visible, setVisible] = useState(false);

  const step = steps[currentStep];

  const positionTooltip = useCallback(() => {
    if (!step) return;
    const el = document.querySelector(step.target);
    if (!el) {
      // If the target doesn't exist, center the tooltip
      setTooltipStyle({
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      });
      setVisible(true);
      return;
    }

    const rect = el.getBoundingClientRect();
    const pad = 16;
    const style: React.CSSProperties = { position: "fixed" };

    switch (step.position) {
      case "bottom":
        style.top = rect.bottom + pad;
        style.left = rect.left + rect.width / 2;
        style.transform = "translateX(-50%)";
        break;
      case "top":
        style.bottom = window.innerHeight - rect.top + pad;
        style.left = rect.left + rect.width / 2;
        style.transform = "translateX(-50%)";
        break;
      case "left":
        style.top = rect.top + rect.height / 2;
        style.right = window.innerWidth - rect.left + pad;
        style.transform = "translateY(-50%)";
        break;
      case "right":
        style.top = rect.top + rect.height / 2;
        style.left = rect.right + pad;
        style.transform = "translateY(-50%)";
        break;
    }

    setTooltipStyle(style);
    setVisible(true);
  }, [step]);

  useEffect(() => {
    positionTooltip();
    const onResize = () => positionTooltip();
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onResize, true);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onResize, true);
    };
  }, [positionTooltip, currentStep]);

  // Highlight the target element
  useEffect(() => {
    if (!step) return;
    const el = document.querySelector(step.target);
    if (el) {
      (el as HTMLElement).style.position = "relative";
      (el as HTMLElement).style.zIndex = "60";
      (el as HTMLElement).style.borderRadius = "1rem";
      (el as HTMLElement).style.boxShadow = "0 0 0 4px rgba(99,102,241,0.4), 0 0 30px rgba(99,102,241,0.15)";
    }
    return () => {
      if (el) {
        (el as HTMLElement).style.zIndex = "";
        (el as HTMLElement).style.boxShadow = "";
      }
    };
  }, [step]);

  const next = () => {
    if (currentStep < steps.length - 1) {
      setVisible(false);
      setTimeout(() => setCurrentStep((s) => s + 1), 150);
    } else {
      onComplete();
    }
  };

  const prev = () => {
    if (currentStep > 0) {
      setVisible(false);
      setTimeout(() => setCurrentStep((s) => s - 1), 150);
    }
  };

  if (!step) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" onClick={onComplete} />

      {/* Tooltip */}
      <div
        className={cn(
          "z-[70] w-80 rounded-2xl border border-white/10 bg-surface-800 p-5 shadow-2xl transition-all duration-200",
          visible ? "opacity-100 scale-100" : "opacity-0 scale-95"
        )}
        style={tooltipStyle}
      >
        {/* Close */}
        <button
          onClick={onComplete}
          className="absolute top-3 right-3 text-white/30 hover:text-white/60 transition"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Step counter */}
        <p className="text-[10px] uppercase tracking-[0.3em] text-accent-400 mb-2">
          Step {currentStep + 1} of {steps.length}
        </p>

        <h3 className="text-lg font-display text-white mb-2">{step.title}</h3>
        <p className="text-sm text-white/60 leading-relaxed mb-4">{step.description}</p>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={onComplete}
            className="text-xs text-white/30 hover:text-white/60 transition"
          >
            Skip Tour
          </button>
          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={prev}
                className="flex items-center gap-1 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/60 hover:text-white transition"
              >
                <ChevronLeft className="h-3 w-3" />
                Back
              </button>
            )}
            <button
              onClick={next}
              className="flex items-center gap-1 rounded-lg bg-accent-500/20 border border-accent-500/30 px-3 py-1.5 text-xs text-accent-300 hover:bg-accent-500/30 transition"
            >
              {currentStep < steps.length - 1 ? "Next" : "Finish"}
              {currentStep < steps.length - 1 && <ChevronRight className="h-3 w-3" />}
            </button>
          </div>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-1 mt-3">
          {steps.map((_, i) => (
            <span
              key={i}
              className={cn(
                "h-1.5 rounded-full transition-all",
                i === currentStep ? "w-4 bg-accent-400" : "w-1.5 bg-white/20"
              )}
            />
          ))}
        </div>
      </div>
    </>
  );
}
