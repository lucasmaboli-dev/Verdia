# Simulação ABM — Verdia Ecosystem

## Visão Geral

Simulação computacional baseada em agentes (ABM) para avaliação da robustez institucional do mecanismo Verdia, utilizando Monte Carlo com 10.000 trajetórias ao longo de 120 períodos.

## Arquitetura

```
simulation/
├── config.json       # Parâmetros, cenários e critérios de robustez
├── agents.py         # Agentes: FamilyAgent, EnterpriseAgent, ValidatorAgent
├── protocol.py       # VerdiaProtocol: CCS, CVS, emissão, burn, LCR
├── environment.py    # Ambiente estocástico com choques exógenos
└── monte_carlo.py    # Runner Monte Carlo + métricas de robustez
```

## Execução

```bash
pip install numpy scipy pandas
cd simulation
python monte_carlo.py
```

## Critérios de Robustez

| Dimensão | Métrica | Critério |
|----------|---------|----------|
| Solvência | Q₀.₀₅(CCS_t) | ≥ 1 |
| Liquidez | Q₀.₀₅(LCR_t) | ≥ 0.8 |
| Estabilidade | CVS | Convergência assintótica |
| Convergência | \|CVS̄ recente - CVS̄ anterior\| | < ε |
| Resiliência | θ = 1 - β (AR1) | > 0 |
| Half-life | t½ = ln(0.5)/ln(β) | Finito |
| Crise | π₃ | < 1% |
| Severidade | CVaR₀.₀₅ | Limitado |

## Cenários

- **Base:** NRR=1.05, φ=2%, crescimento linear
- **Otimista:** NRR=1.20, φ=1%, flywheel acelerado
- **Pessimista:** Choque -30% inflow, φ=15%, run de resgate

## Fundamentação

- **Popper:** Modelo falsificável — define condições de falha
- **Fogg:** B = M × A × P para agentes B2C
- **Tirole:** Externalidades de rede cruzadas para B2B
- **Basileia III:** CCS como colchão de capital programável
