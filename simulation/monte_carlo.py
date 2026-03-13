"""
Verdia Ecosystem — Agent-Based Model (ABM)
Módulo: Simulação Monte Carlo + Métricas de Robustez

Executa 10.000 trajetórias e calcula:
  - Q_{0.05}(CCS_t) — solvência de cauda
  - Q_{0.05}(LCR_t) — liquidez de cauda
  - CVS — estabilidade macroprudencial
  - AR(1) / θ / Half-life — resiliência ativa
  - π₃ — tempo em crise
  - CVaR_{0.05} — severidade das caudas
"""

import numpy as np
import json
from dataclasses import dataclass, field
from protocol import VerdiaProtocol
from environment import Environment


@dataclass
class MonteCarloResults:
    """Resultados agregados de todas as trajetórias."""
    ccs_matrix: np.ndarray        # shape: (iterations, periods)
    lcr_matrix: np.ndarray
    state_matrix: np.ndarray
    cvs_per_trajectory: np.ndarray
    crisis_fraction: np.ndarray

    def quantile_transversal(self, q: float = 0.05) -> np.ndarray:
        """Q_{q}^(t) por período — quantil transversal entre trajetórias."""
        return np.quantile(self.ccs_matrix, q, axis=0)

    def quantile_lcr(self, q: float = 0.05) -> np.ndarray:
        """Q_{q}(LCR_t) por período."""
        return np.quantile(self.lcr_matrix, q, axis=0)

    def solvency_check(self) -> bool:
        """Q_{0.05}(CCS_t) ≥ 1 para todo t?"""
        q5 = self.quantile_transversal(0.05)
        return bool(np.all(q5 >= 1.0))

    def liquidity_check(self) -> bool:
        """Q_{0.05}(LCR_t) ≥ 0.8 para todo t?"""
        q5_lcr = self.quantile_lcr(0.05)
        return bool(np.all(q5_lcr >= 0.8))

    def mean_cvs(self) -> float:
        """CVS médio entre trajetórias."""
        return float(np.mean(self.cvs_per_trajectory))

    def mean_crisis_fraction(self) -> float:
        """π₃ médio — fração de tempo em crise."""
        return float(np.mean(self.crisis_fraction))

    def cvar_ccs(self, q: float = 0.05) -> np.ndarray:
        """CVaR_{q}(CCS_t) = E[CCS | CCS ≤ Q_q] por período."""
        quantiles = self.quantile_transversal(q)
        cvar = np.zeros(self.ccs_matrix.shape[1])
        for t in range(self.ccs_matrix.shape[1]):
            col = self.ccs_matrix[:, t]
            mask = col <= quantiles[t]
            cvar[t] = col[mask].mean() if mask.any() else quantiles[t]
        return cvar

    def estimate_ar1(self) -> dict:
        """
        Estima AR(1): CVS_t = α + β × CVS_{t-1} + ε
        θ = 1 - β (velocidade de reversão)
        t½ = ln(0.5) / ln(β) (half-life do choque)
        """
        # Usa CVS rolling por trajetória como proxy
        cvs_series = self.cvs_per_trajectory
        if len(cvs_series) < 10:
            return {"alpha": 0, "beta": 0, "theta": 0, "half_life": float("inf")}

        y = cvs_series[1:]
        x = cvs_series[:-1]

        # OLS simples
        x_mean = x.mean()
        y_mean = y.mean()
        beta = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        alpha = y_mean - beta * x_mean
        theta = 1 - beta

        half_life = float("inf")
        if 0 < beta < 1:
            half_life = np.log(0.5) / np.log(beta)

        return {
            "alpha": float(alpha),
            "beta": float(beta),
            "theta": float(theta),
            "half_life": float(half_life),
        }

    def summary(self) -> dict:
        """Resumo completo das métricas de robustez."""
        ar1 = self.estimate_ar1()
        q5_ccs = self.quantile_transversal(0.05)
        q5_lcr = self.quantile_lcr(0.05)

        return {
            "solvency_Q05_min": float(q5_ccs.min()),
            "solvency_pass": self.solvency_check(),
            "liquidity_Q05_min": float(q5_lcr.min()),
            "liquidity_pass": self.liquidity_check(),
            "cvs_mean": self.mean_cvs(),
            "crisis_fraction_mean": self.mean_crisis_fraction(),
            "crisis_pass": self.mean_crisis_fraction() < 0.01,
            "ar1_beta": ar1["beta"],
            "ar1_theta": ar1["theta"],
            "half_life_periods": ar1["half_life"],
            "cvar_05_min": float(self.cvar_ccs(0.05).min()),
        }


def run_single_trajectory(config: dict, scenario: dict,
                           seed: int) -> dict:
    """Executa uma trajetória completa de N períodos."""
    rng = np.random.default_rng(seed)
    env = Environment.from_scenario(scenario)
    init = config["initial_conditions"]

    protocol = VerdiaProtocol(
        R=init["R_0"],
        T=init.get("T_0", 100.0),
        V=init["V_0"],
        delta=init["delta"],
        rho=init["rho"],
        kappa=init["kappa"],
        beta_base=init["beta_base"],
        beta_max=init["beta_max"],
    )

    periods = config["simulation"]["periods"]
    ccs_series = []
    lcr_series = []
    state_series = []

    current_P = 100.0
    current_I_monthly = 20000.0
    day_in_month = 0

    for t in range(periods):
        # Generate stochastic variables
        current_P = env.generate_production_growth(current_P, rng)
        phi = env.generate_fraud_rate(rng)
        gamma = env.generate_redemption_rate(rng)

        # Monthly inflow update
        day_in_month += 1
        if day_in_month >= 30:
            current_I_monthly = env.generate_monthly_inflow(current_I_monthly, rng)
            day_in_month = 0

        I_t = current_I_monthly / 30.0
        P_eff = current_P * (1 - phi)
        W_t = gamma * protocol.T
        U_t = max(protocol.T * 0.001 * rng.random(), 0)  # utility burn

        result = protocol.step(P_eff, I_t, W_t, U_t)
        ccs_series.append(result["ccs"])
        lcr_series.append(result["lcr"])
        state_series.append(1 if result["state"] == "C" else 0)

    cvs = protocol.compute_CVS()
    crisis_frac = np.mean(state_series)

    return {
        "ccs": np.array(ccs_series),
        "lcr": np.array(lcr_series),
        "states": np.array(state_series),
        "cvs": cvs,
        "crisis_fraction": crisis_frac,
    }


def run_monte_carlo(config: dict, scenario: dict) -> MonteCarloResults:
    """Executa N iterações de Monte Carlo."""
    n_iter = config["simulation"]["iterations"]
    n_periods = config["simulation"]["periods"]
    base_seed = config["simulation"].get("random_seed", 42)

    ccs_matrix = np.zeros((n_iter, n_periods))
    lcr_matrix = np.zeros((n_iter, n_periods))
    state_matrix = np.zeros((n_iter, n_periods))
    cvs_list = []
    crisis_list = []

    for i in range(n_iter):
        result = run_single_trajectory(config, scenario, seed=base_seed + i)
        ccs_matrix[i] = result["ccs"]
        lcr_matrix[i] = result["lcr"]
        state_matrix[i] = result["states"]
        cvs_list.append(result["cvs"])
        crisis_list.append(result["crisis_fraction"])

        if (i + 1) % 1000 == 0:
            print(f"  Iteração {i + 1}/{n_iter} concluída")

    return MonteCarloResults(
        ccs_matrix=ccs_matrix,
        lcr_matrix=lcr_matrix,
        state_matrix=state_matrix,
        cvs_per_trajectory=np.array(cvs_list),
        crisis_fraction=np.array(crisis_list),
    )


if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)

    for scenario_name in ["base", "optimistic", "pessimistic"]:
        print(f"\n{'='*60}")
        print(f"  CENÁRIO: {scenario_name.upper()}")
        print(f"{'='*60}")

        scenario = config["scenarios"][scenario_name]
        results = run_monte_carlo(config, scenario)
        summary = results.summary()

        for k, v in summary.items():
            print(f"  {k}: {v}")

        print(f"\n  ✅ SOLVÊNCIA: {'PASS' if summary['solvency_pass'] else '❌ FAIL'}")
        print(f"  ✅ LIQUIDEZ:  {'PASS' if summary['liquidity_pass'] else '❌ FAIL'}")
        print(f"  ✅ CRISE:     {'PASS' if summary['crisis_pass'] else '❌ FAIL'}")
