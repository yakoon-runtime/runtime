# The Yakoon Manifesto

## Why the common narrative is wrong and what we do differently

---

## 1. The Common Narrative

The current justification for cloud architecture goes:

```
AI → needs huge models → huge models run in the cloud
→ therefore everything must be in the cloud
```

This is treated almost like a law of nature. As if the cloud were a technical necessity for AI.

**But this causality is historical, not technical.**

---

## 2. The Reversed Causality

> Companies didn't move to the cloud because AI demanded it.
>
> AI works so well with the cloud today because companies had already moved their data there.

That's a fundamental difference.

### Phase 1: Everything on-prem

```
ERP     CRM     Fileserver     Exchange
│       │       │              │
└───────┴───────┴──────────────┘
         Enterprise (on-prem)
```

Data lived where the company worked. Secure, controlled, but hard to update, expensive to operate.

### Phase 2: Data moves outward

```
Salesforce     Office365     Jira Cloud     HubSpot     Slack
│             │             │              │           │
└─────────────┴─────────────┴──────────────┴───────────┘
                     Cloud (SaaS)
```

Not because of AI. But because of:
- Easier updates
- Lower IT costs
- Lower entry barriers

The cloud solved an **operations problem**, not a **data problem**.

### Phase 3: AI appears

Now suddenly: **"AI works where the data is."**

Of course. The data was already there.

> **The cloud doesn't solve the AI problem. The cloud hides the data problem.**

---

## 3. The Wrong Question

The industry asks: "Which model is the best?"

The right question would be: **"Why do we believe a single model can do everything?"**

An enterprise has:
- Invoices
- Projects
- HR
- Procurement
- Production

These are completely different domains with different data, different rules, different security requirements.

**Why should one centralized AI be perfect at everything?**

Why not:

```
Invoice AI     Project AI     Contract AI     Support AI
│              │              │               │
└──────────────┴──────────────┴───────────────┘
           Yakoon Runtime
```

All local, with their respective data. Small, specialized, controlled.

---

## 4. Yakoon Asks a Different Question

> **What if the runtime goes to the data instead of the data going to the runtime?**

This is the inversion of the SaaS idea.

| SaaS Philosophy | Yakoon Philosophy |
|-----------------|-------------------|
| Move data to the cloud | Move runtime to the data |
| One platform for all | One kernel per domain |
| Central AI | Domain AI (per space/node) |
| Cloud = prerequisite | Cloud = option |

Yakoon doesn't say "cloud is bad." Yakoon says: **"The runtime decides where the data stays — not the hosting provider."**

---

## 5. What Yakoon Does Differently

Yakoon can connect a **completely different AI** per space/node/domain:

```python
# Space "billing" → small specialized invoice AI
billing.ports.provide(OnAI, Ollama("billing-llama:7b"))

# Space "legal" → local AI that never leaves the corporate network
legal.ports.provide(OnAI, Ollama("legal-mistral:7b"))

# Space "creative" → large cloud AI for brainstorming
creative.ports.provide(OnAI, Remote("gpt-7"))

# Space "support" → hybrid: local pre-processing, cloud for complex cases
support.ports.provide(OnAI, Hybrid(
    local=Ollama("support-fast:3b"),
    fallback=Remote("claude-5"),
))
```

**The runtime decouples AI from infrastructure.** A space gets exactly the AI it needs — no more, no less.


