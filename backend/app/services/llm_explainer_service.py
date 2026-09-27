import os
import requests
from typing import Optional
from app.schemas.action import ActionRequest
from app.core.enums import VerdictEnum

class LLMExplainerService:
    """
    Person 3 Deliverable:
    Groq LLM-powered Natural Language Block Rationale Explainer.
    Uses GROQ_API_KEY for ultra-fast Llama-3 LLM reasoning generation.
    """
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")

    def generate_explanation(
        self,
        req: ActionRequest,
        verdict: VerdictEnum,
        reason: str,
        ml_score: float
    ) -> str:
        if verdict == VerdictEnum.ALLOW:
            return f"Action '{req.action_type}' for agent '{req.agent_id}' passed all policy rules, spend limits, and security checks."

        # Try live Groq API call if key is present and valid
        if self.groq_api_key and self.groq_api_key.startswith("gsk_") and len(self.groq_api_key) > 20:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                prompt = (
                    f"You are SentinelAI Security Officer. Explain why the action '{req.action_type}' "
                    f"requested by AI agent '{req.agent_id}' for amount ₹{req.amount:,.2f} was {verdict.value}ED. "
                    f"System Reason: {reason}. ML Anomaly Score: {ml_score}. Keep explanation under 3 sentences."
                )
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 150
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=2.0)
                if resp.status_code == 200:
                    explanation = resp.json()["choices"][0]["message"]["content"].strip()
                    return f"🤖 **Groq Llama-3 AI Explanation**:\n{explanation}"
            except Exception:
                pass # Fallback to fast template on timeout/error

        # Fallback Template Explainer (Zero-Latency Backup)
        explanation_parts = [
            f"⚠️ **SentinelAI Security Guardrail Triggered**: Action '{req.action_type}' by agent '{req.agent_id}' was {verdict.value}ED.",
            f"**Reason**: {reason}",
            f"**Risk Score**: ML Anomaly Score is {ml_score:.2f} (Threshold: 0.70)."
        ]

        if req.amount > 0:
            explanation_parts.append(f"**Financial Impact**: Requested amount was ₹{req.amount:,.2f}.")

        explanation_parts.append("🛡️ *SentinelAI Governance Guardrail strictly prevents unauthorized financial drift.*")

        return "\n\n".join(explanation_parts)

llm_explainer_service = LLMExplainerService()
