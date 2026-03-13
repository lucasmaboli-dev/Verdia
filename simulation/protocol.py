"""
Verdia Ecosystem — Agent-Based Model (ABM)
Módulo: VerdiaProtocol — Banco Central Algorítmico

Implementa:
  - Coeficiente de Cobertura Sistêmica (CCS)
  - Coeficiente de Variação Sistêmica (CVS)
  - Emissão elástica com estados e histerese
  - Mecanismo de queima (burn)
  - Índice de Cobertura de Liquidez (LCR)
  - Controlador anticíclico de segunda ordem
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum


class ProtocolState(Enum):
    NORMAL = "A"
    ALERT = "B"
    CRISIS = "C"


@dataclass
class VerdiaProtocol:
    """Banco Central Algorítmico da Verdia — Basileia programável."""

    # --- State variables ---
    R: float              # Reserva fiduciária [BRL]
    T: float              # Tokens em circulação [token]
    V: float              # Valor de liquidação [BRL/token]
    Q: float = 0.0        # Fila de resgates [token]

    # --- Parameters ---
    delta: float = 0.20          # Buffer prudencial
    delta_up: float = 0.22       # Histerese (saída do alerta)
    delta_down: float = 0.18     # Histerese (entrada no alerta)
    rho: float = 0.50            # Fração de reserva como liquidez
    kappa: float = 1.0           # Conversão produção → tokens
    beta_base: float = 0.05      # Taxa esterilização base
    beta_max: float = 0.30       # Taxa esterilização máxima
    eta: float = 0.3             # Fator de emissão reduzida (estado B)
    ema_lambda: float = 0.0645   # EMA lambda (janela 30 dias)

    # --- Derived ---
    R_ema: float = 0.0           # EMA da reserva
    state: ProtocolState = ProtocolState.NORMAL
    ccs_history: list = field(default_factory=list)

    def __post_init__(self):
        self.R_ema = self.R

    # ── Core Metrics ──────────────────────────────────────────

    @property
    def CCS(self) -> float:
        """Coeficiente de Cobertura Sistêmica."""
        denominator = self.T * self.V
        if denominator <= 0:
            return float("inf")
        return self.R / denominator

    @property
    def L(self) -> float:
        """Liquidez disponível para resgate."""
        return self.rho * self.R

    def LCR(self, expected_outflow: float) -> float:
        """Índice de Cobertura de Liquidez on-chain."""
        if expected_outflow <= 0:
            return float("inf")
        return self.L / expected_outflow

    # ── State Machine (com histerese) ─────────────────────────

    def update_state(self, lcr: float) -> ProtocolState:
        """Determina estado via limiares com histerese."""
        ccs = self.CCS

        if self.state == ProtocolState.NORMAL:
            if ccs < 1 or lcr < 0.8:
                self.state = ProtocolState.CRISIS
            elif ccs < 1 + self.delta_down or lcr < 1.0:
                self.state = ProtocolState.ALERT

        elif self.state == ProtocolState.ALERT:
            if ccs < 1 or lcr < 0.8:
                self.state = ProtocolState.CRISIS
            elif ccs >= 1 + self.delta_up and lcr >= 1.0:
                self.state = ProtocolState.NORMAL

        elif self.state == ProtocolState.CRISIS:
            if ccs >= 1 + self.delta_down and lcr >= 0.8:
                self.state = ProtocolState.ALERT
            if ccs >= 1 + self.delta_up and lcr >= 1.0:
                self.state = ProtocolState.NORMAL

        return self.state

    # ── Emission ──────────────────────────────────────────────

    def g(self) -> float:
        """Fator de emissão por estado."""
        if self.state == ProtocolState.NORMAL:
            return 1.0
        elif self.state == ProtocolState.ALERT:
            return self.eta
        else:
            return 0.0

    def compute_emission(self, P_eff: float) -> float:
        """E_t = κ × P_t^eff × g(estado)."""
        return self.kappa * P_eff * self.g()

    # ── Burn ──────────────────────────────────────────────────

    def beta(self) -> float:
        """Taxa de esterilização por estado."""
        if self.state == ProtocolState.NORMAL:
            return self.beta_base
        elif self.state == ProtocolState.ALERT:
            return 2 * self.beta_base
        else:
            return self.beta_max

    def compute_burn(self, I_t: float, U_t: float) -> float:
        """B_t = β_t × (I_t / V_t) + U_t."""
        if self.V <= 0:
            return U_t
        sterilization = self.beta() * (I_t / self.V)
        return sterilization + U_t

    # ── Redemption ────────────────────────────────────────────

    def compute_redemption(self, W_t: float) -> tuple:
        """
        X_t = min(W_t + Q_t, L_t / V_t)
        Out_t = X_t × V_t
        Returns: (X_t, Out_t)
        """
        if self.V <= 0:
            return 0.0, 0.0
        max_redeemable = self.L / self.V
        X_t = min(W_t + self.Q, max_redeemable)
        Out_t = X_t * self.V
        return X_t, Out_t

    # ── Daily Settlement ──────────────────────────────────────

    def step(self, P_eff: float, I_t: float, W_t: float, U_t: float) -> dict:
        """
        Executa ciclo diário completo do Banco Central Algorítmico.

        Args:
            P_eff: Produção efetiva validada (pós-fraude)
            I_t: Inflow fiduciário do dia
            W_t: Tokens solicitados para resgate
            U_t: Tokens gastos em utilidades (queima por consumo)

        Returns:
            dict com métricas do dia
        """
        # 1. Calcular métricas pré-step
        ccs_pre = self.CCS
        expected_outflow = W_t * self.V if W_t > 0 else 0.01
        lcr = self.LCR(expected_outflow)

        # 2. Atualizar estado (com histerese)
        self.update_state(lcr)

        # 3. Emissão
        E_t = self.compute_emission(P_eff)

        # 4. Queima
        B_t = self.compute_burn(I_t, U_t)

        # 5. Resgate
        X_t, Out_t = self.compute_redemption(W_t)

        # 6. Atualizar ledger
        self.T = max(self.T + E_t - B_t, 0)
        self.R = max(self.R + I_t - Out_t, 0)
        self.Q = max(self.Q + W_t - X_t, 0)

        # 7. Atualizar EMA
        self.R_ema = self.ema_lambda * self.R + (1 - self.ema_lambda) * self.R_ema

        # 8. Registrar CCS
        ccs_post = self.CCS
        self.ccs_history.append(ccs_post)

        return {
            "ccs": ccs_post,
            "lcr": lcr,
            "state": self.state.value,
            "E_t": E_t,
            "B_t": B_t,
            "X_t": X_t,
            "Out_t": Out_t,
            "R_t": self.R,
            "T_t": self.T,
            "Q_t": self.Q,
        }

    # ── Analytics ─────────────────────────────────────────────

    def compute_CVS(self) -> float:
        """Coeficiente de Variação Sistêmica (longitudinal intra-trajetória)."""
        if len(self.ccs_history) < 2:
            return 0.0
        arr = np.array(self.ccs_history)
        mu = arr.mean()
        if mu <= 0:
            return float("inf")
        return arr.std() / mu

    def check_convergence(self, window: int = 12) -> float:
        """
        |CVS̄_{t-11:t} - CVS̄_{t-23:t-12}| — teste de convergência assintótica.
        """
        h = self.ccs_history
        if len(h) < 2 * window:
            return float("inf")
        recent = np.array(h[-window:])
        previous = np.array(h[-2 * window: -window])
        cvs_recent = recent.std() / recent.mean() if recent.mean() > 0 else float("inf")
        cvs_prev = previous.std() / previous.mean() if previous.mean() > 0 else float("inf")
        return abs(cvs_recent - cvs_prev)
