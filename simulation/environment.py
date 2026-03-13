"""
Verdia Ecosystem — Agent-Based Model (ABM)
Módulo: Ambiente Estocástico

Gera choques exógenos e controla variáveis macroeconômicas:
  - Crescimento de usuários B2C
  - Choques de demanda B2B
  - Ataques de fraude coordenada
  - Picos de resgate (run risk)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class Environment:
    """Ambiente estocástico para simulação ABM da Verdia."""

    # Production (B2C)
    mu_P: float = 0.001
    sigma_P: float = 0.05

    # Inflow (B2B)
    mu_I: float = 0.0
    sigma_I: float = 0.03
    nrr: float = 1.05

    # Fraud
    phi_base: float = 0.02
    phi_attack: float = 0.13
    attack_probability: float = 0.0

    # Shocks
    shock_probability: float = 0.0
    shock_magnitude: float = 0.30

    # Redemption
    mu_gamma: float = -7.6
    sigma_gamma: float = 0.5

    def generate_production_growth(self, current_P: float,
                                    rng: np.random.Generator) -> float:
        """P_{t+1} = P_t × exp(μ_P + σ_P × ε_t) — GBM."""
        shock = rng.normal(self.mu_P, self.sigma_P)
        return current_P * np.exp(shock)

    def generate_monthly_inflow(self, current_I: float,
                                 rng: np.random.Generator) -> float:
        """I^(m+1) = I^(m) × NRR × exp(μ_I + σ_I × ξ) × (1 - χ)."""
        noise = rng.normal(self.mu_I, self.sigma_I)
        shock = 0.0
        if rng.random() < self.shock_probability:
            shock = self.shock_magnitude
        return current_I * self.nrr * np.exp(noise) * (1 - shock)

    def generate_fraud_rate(self, rng: np.random.Generator) -> float:
        """φ_t = φ_base + φ_attack × 𝟙(ataque ativo)."""
        attack_active = rng.random() < self.attack_probability
        phi = self.phi_base
        if attack_active:
            phi += self.phi_attack
        return min(phi, 0.99)

    def generate_redemption_rate(self, rng: np.random.Generator) -> float:
        """γ_t ~ LogNormal(μ_γ, σ_γ) — fração diária de tokens buscando resgate."""
        return rng.lognormal(self.mu_gamma, self.sigma_gamma)

    @classmethod
    def from_scenario(cls, scenario: dict) -> "Environment":
        """Cria ambiente a partir de cenário de configuração."""
        return cls(
            nrr=scenario.get("nrr", 1.05),
            phi_base=scenario.get("phi_base", 0.02),
            phi_attack=scenario.get("phi_attack", 0.13),
            attack_probability=scenario.get("attack_probability", 0.0),
            shock_probability=scenario.get("shock_probability", 0.0),
            shock_magnitude=scenario.get("shock_magnitude", 0.30),
            mu_gamma=scenario.get("mu_gamma", -7.6),
        )
