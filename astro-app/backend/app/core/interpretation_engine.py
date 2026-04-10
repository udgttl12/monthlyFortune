from collections import defaultdict


class InterpretationEngine:
    def build_rule_based_summary(self, aspects: list[dict], transit_events: list[dict]) -> dict[str, str]:
        scores = defaultdict(int)

        for aspect in aspects:
            if aspect["aspect"] in {"Trine", "Sextile"}:
                scores["love"] += 2
                scores["money"] += 1
            elif aspect["aspect"] in {"Square", "Opposition"}:
                scores["risk"] += 2
                scores["career"] += 1
            else:
                scores["career"] += 1

        for event in transit_events:
            if event["impact"] == "high":
                scores["career"] += 2
                scores["risk"] += 1
            else:
                scores["money"] += 1

        return {
            "career": self._bucket(scores["career"], "Career shifts are steady with room to grow."),
            "money": self._bucket(scores["money"], "Money flow is balanced; keep your spending intentional."),
            "love": self._bucket(scores["love"], "Emotional clarity improves connection and trust."),
            "risk": self._bucket(scores["risk"], "Manage stress and avoid rushed commitments this month."),
        }

    def enhance_with_llm(self, summary: dict[str, str]) -> dict[str, str]:
        # Placeholder for future LLM integration.
        return summary

    @staticmethod
    def _bucket(score: int, fallback: str) -> str:
        if score >= 8:
            return "Very active cycle: prioritize decisions and seize opportunities."
        if score >= 4:
            return "Moderate momentum: progress comes from consistency and timing."
        return fallback
