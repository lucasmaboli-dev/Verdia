"""
Verdia Ecosystem — Agent-Based Model (ABM)
Módulo: Agentes autônomos com racionalidade limitada

Agentes:
  - FamilyAgent (B2C): Decisão via Fogg Behavior Model com feedback adaptativo
  - EnterpriseAgent (B2B): Utilidade baseada em externalidades de rede (Tirole)
  - ValidatorAgent (Cooperativa): Trade-off fraude vs. penalidade reputacional
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class FamilyAgent:
    """Agente Gerador (B2C) — decisão via Fogg: B = M × A × P"""

    agent_id: int
    motivation: float       # M ~ N(μ_M, σ_M)
    ability: float          # A — facilidade de uso (constante por período)
    prompt_prob: float      # P — probabilidade de receber gatilho contextual
    reputation: float = 0.0
    streak: int = 0
    tokens_balance: float = 0.0
    feedback_delta: float = 0.05

    def decide_recycle(self, rng: np.random.Generator) -> bool:
        """Prob(Reciclar) = M × A × P — equação de Fogg."""
        prob = np.clip(self.motivation * self.ability * self.prompt_prob, 0, 1)
        return rng.random() < prob

    def update_motivation(self, reward: float, frustration: float) -> None:
        """Feedback adaptativo: M_{t+1} = M_t + δ(Recompensa - Frustração)."""
        self.motivation += self.feedback_delta * (reward - frustration)
        self.motivation = np.clip(self.motivation, 0.01, 0.99)

    def update_streak(self, recycled: bool) -> None:
        if recycled:
            self.streak += 1
        else:
            self.streak = 0

    @staticmethod
    def create_population(n: int, mu_m: float, sigma_m: float,
                          ability: float, prompt: float,
                          delta: float, rng: np.random.Generator) -> list:
        """Cria população heterogênea: M ~ N(μ, σ)."""
        motivations = rng.normal(mu_m, sigma_m, n)
        motivations = np.clip(motivations, 0.01, 0.99)
        return [
            FamilyAgent(
                agent_id=i,
                motivation=float(motivations[i]),
                ability=ability,
                prompt_prob=prompt,
                feedback_delta=delta,
            )
            for i in range(n)
        ]


@dataclass
class EnterpriseAgent:
    """Agente Financiador (B2B) — utilidade de rede: U = α×n_C + β×n_B - C"""

    agent_id: int
    annual_contract_brl: float
    alpha_network: float    # sensibilidade ao volume B2C
    beta_network: float     # sensibilidade ao número de B2B
    cost: float
    active: bool = True

    def compute_utility(self, n_consumers: int, n_enterprises: int) -> float:
        """Utilidade corporativa baseada em externalidades de rede (Tirole)."""
        return (self.alpha_network * n_consumers
                + self.beta_network * n_enterprises
                - self.cost)

    def decide_inject(self, n_consumers: int, n_enterprises: int) -> bool:
        """Injeta liquidez se U > 0."""
        return self.compute_utility(n_consumers, n_enterprises) > 0

    def monthly_inflow(self) -> float:
        """Inflow mensal linearizado."""
        return self.annual_contract_brl / 12.0


@dataclass
class ValidatorAgent:
    """Agente Validador (Cooperativa) — propensão à fraude: φ ~ Beta(α, β)"""

    agent_id: int
    fraud_propensity: float   # φ ~ Beta(α, β) ∈ [0, 1]
    reputation: float = 1.0
    detection_probability: float = 0.85
    penalty_multiplier: float = 5.0
    daily_volume: float = 0.0
    suspended: bool = False

    def decide_fraud(self, potential_gain: float, rng: np.random.Generator) -> bool:
        """Fraude ocorre se G_f > p_d × C_r (ganho > custo esperado da punição)."""
        if self.suspended:
            return False
        reputational_cost = self.detection_probability * self.penalty_multiplier * self.reputation
        return potential_gain > reputational_cost and rng.random() < self.fraud_propensity

    def apply_penalty(self) -> None:
        """Penalidade reputacional exponencial."""
        self.reputation *= 0.5
        if self.reputation < 0.1:
            self.suspended = True

    def apply_reward(self, amount: float) -> None:
        """Recompensa positiva por validação honesta."""
        self.reputation = min(self.reputation * 1.02, 1.0)

    @staticmethod
    def create_population(n: int, alpha: float, beta: float,
                          detection_prob: float, penalty_mult: float,
                          rng: np.random.Generator) -> list:
        """Cria cooperativas com heterogeneidade: φ ~ Beta(α, β)."""
        propensities = rng.beta(alpha, beta, n)
        return [
            ValidatorAgent(
                agent_id=i,
                fraud_propensity=float(propensities[i]),
                detection_probability=detection_prob,
                penalty_multiplier=penalty_mult,
            )
            for i in range(n)
        ]
