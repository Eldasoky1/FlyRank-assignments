import { describe, expect, it } from "vitest";
import { classifyMessage, branchSteps, BRANCHES } from "../src/domain/branchRouter";

describe("AI branch router", () => {
  it("routes a double-charge message to billing", () => {
    const r = classifyMessage("I was charged twice and I want a refund");
    expect(r.category).toBe("billing");
    expect(r.confidence).toBeGreaterThan(0.5);
  });

  it("routes a crash/error message to technical", () => {
    const r = classifyMessage("The app crashes with a 500 error and freezes");
    expect(r.category).toBe("technical");
  });

  it("routes a reset-password message to account", () => {
    const r = classifyMessage("I forgot my password and am locked out");
    expect(r.category).toBe("account");
  });

  it("routes a plan/pricing message to sales", () => {
    const r = classifyMessage("What is the price to upgrade to the pro plan?");
    expect(r.category).toBe("sales");
  });

  it("routes an ambiguous message to other", () => {
    const r = classifyMessage("hello there, thanks");
    expect(r.category).toBe("other");
  });

  it("stays within 0..1 confidence and raises with more keyword hits", () => {
    const single = classifyMessage("I want a refund");
    const many = classifyMessage("I was charged twice on my billing invoice, please refund the price");
    expect(single.confidence).toBeGreaterThanOrEqual(0);
    expect(single.confidence).toBeLessThanOrEqual(0.98);
    expect(many.confidence).toBeGreaterThan(single.confidence);
  });

  it("exposes every category through the branch map with a reason", () => {
    const cats = BRANCHES.map((b) => b.category);
    expect(cats).toEqual(["billing", "technical", "account", "sales", "other"]);
    const r = classifyMessage("please charge me again, also fix the bug");
    expect(r.reason.length).toBeGreaterThan(0);
  });

  it("provides ordered, non-empty steps for every branch", () => {
    for (const b of BRANCHES) {
      const steps = branchSteps(b.category);
      expect(steps.length).toBeGreaterThan(0);
      for (const s of steps) {
        expect(s.label.length).toBeGreaterThan(0);
        expect(s.detail.length).toBeGreaterThan(0);
      }
    }
  });

  it("billing branch runs the expected refund steps in order", () => {
    const labels = branchSteps("billing").map((s) => s.label);
    expect(labels).toEqual(["Look up subscription", "Compute refund", "Issue refund"]);
  });
});
