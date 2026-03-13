# 🌿 Verdia Ecosystem — Unified Repository

**Infraestrutura Digital de Coordenação Regulatória Baseada em Dados Físicos Verificáveis**

> *"Transformamos obrigação regulatória em ativo digital auditável."*

---

## Source of Truth

O **source of truth canônico** do ecossistema é `docs/verdia-master-repository-v4.json`. Todos os parâmetros numéricos, métricas prudenciais, fórmulas e regras de governança devem ser consultados neste arquivo antes de codificar ou simular.

## Arquivos Principais

### 📋 Documentos Canônicos (`docs/`)

| Arquivo | Papel |
|---------|-------|
| `verdia-master-repository-v4.json` | **Source of truth v4** — arquitetura, auditoria, parâmetros canônicos, camada prudencial, simulação, rastreabilidade e programa |
| `verdia-ecosystem-architect-profile.json` | Arquitetura consolidada do ecossistema v1.1 (estratégia, tecnologia, tokenomics, UX, compliance, riscos, simulação) |
| `verdia-ecosystem-decoding.json` | Trilhas mandatórias de execução (compliance, ACB, interfaces, operações, monetização, diretivas EPD) |
| `verdia-program-backlog.json` | Backlog PMO com 17 blocos, 5 workstreams, 6 gates (G0-G5), 13 papéis e dependências |

### 🤖 Agentes de IA (`agents/`)

| Arquivo | Papel |
|---------|-------|
| `ecosystem_architect_agent.json` | Prompt do Arquiteto de Software (persona Engenheiro de Produção) |

### 🧪 Simulação ABM (`simulation/`)

| Arquivo | Papel |
|---------|-------|
| `agents.py` | Agentes: FamilyAgent (Fogg), EnterpriseAgent (Tirole), ValidatorAgent (Beta) — **ART-03** |
| `protocol.py` | VerdiaProtocol: CCS, CVS, estados, histerese, emissão, burn, resgate — **ART-02** |
| `environment.py` | Ambiente estocástico: GBM, choques, fraude, run risk |
| `monte_carlo.py` | Runner Monte Carlo: Q₀.₀₅, CVaR, AR(1), half-life, π₃ |
| `config.json` | Parâmetros e cenários (base, otimista, pessimista) |

### 📜 Smart Contracts (`contracts/`)

| Arquivo | Papel |
|---------|-------|
| `daily_settlement.pseudo` | Pseudocódigo Solidity: Basileia programável on-chain — **ART-04** |

### 🏗️ Arquitetura Suplementar (`architecture/`)

| Arquivo | Papel |
|---------|-------|
| `technology_layers.json` | Camadas tecnológicas detalhadas |
| `data_model.json` | Modelo de dados e fluxos |

### 📖 Documentação Legível (`docs/`)

| Arquivo | Conteúdo |
|---------|----------|
| `fundamentacao_teorica.md` | Coase, Ostrom, Tirole, Fogg, Porter |
| `gtm_strategy.md` | Estratégia Go-to-Market faseada |
| `risk_matrix.md` | Matriz de riscos completa |
| `pitch_structure.md` | Estrutura do Pitch Deck para VC |

---

## Validação Rápida

```bash
# Validar todos os JSONs
python -m json.tool docs/verdia-master-repository-v4.json > /dev/null && echo "✅ master-v4"
python -m json.tool docs/verdia-ecosystem-architect-profile.json > /dev/null && echo "✅ profile v1.1"
python -m json.tool docs/verdia-ecosystem-decoding.json > /dev/null && echo "✅ decoding"
python -m json.tool docs/verdia-program-backlog.json > /dev/null && echo "✅ backlog"

# Validar sintaxe Python
python -c "import py_compile; [py_compile.compile(f'simulation/{f}', doraise=True) for f in ['agents.py','protocol.py','environment.py','monte_carlo.py']]" && echo "✅ Python OK"
```

---

## Artifact Registry

| ID | Arquivo | Papel |
|----|---------|-------|
| ART-02 | `simulation/protocol.py` | Implementação de referência da lógica prudencial |
| ART-03 | `simulation/monte_carlo.py` | Motor de simulação de referência |
| ART-04 | `contracts/daily_settlement.pseudo` | Arquitetura de referência do smart contract |

---

## Contexto

**Projeto:** Verdia — Cleantech de Economia Circular e Logística Reversa  
**TCC:** *Tokenização via Blockchain na Gestão de Resíduos Sólidos: O Modelo Verdia*  
**Programa:** MBA em ESG e Negócios Sustentáveis — USP/ESALQ/Pecege  
**Autor:** Lucas Magalhães Barbosa de Oliveira  

## Licença

[MIT License](LICENSE)
