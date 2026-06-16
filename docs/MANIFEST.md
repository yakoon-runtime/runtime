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

---

## 6. The Most Provocative Sentence

> **"The cloud doesn't solve the AI problem. The cloud hides the data problem."**

Because many companies don't have an AI problem. They have:
- Data silos
- Missing authorization
- Missing governance
- Missing structure

And as long as that remains unsolved, even GPT-9 won't suddenly run the company.

Yakoon solves the structure problem: it defines who can access which data (permissions), which operations are possible (nodes), and which AI can do what (ports).

**Structure first, then AI. Not the other way around.**

---

## 7. Review

### What is strong

The argument chain is not attackable because it doesn't argue against cloud — it questions **causality**. Nobody can say "cloud is wrong." But the question "Is cloud really a prerequisite or just a consequence?" can't be answered with "cloud is good." It forces reflection.

### What's missing

The article needs a **counter-proof**. A concrete example where the centralized AI approach fails because data cannot be in the cloud:

- **Legal/Compliance**: Law firm with attorney-client privilege. No cloud model may see contracts. A local 7B model on the firm's server can.
- **Production**: Machine builder whose CAD data must never leave the corporate network (export control).
- **Healthcare**: Patient data that must not leave the jurisdiction (GDPR).

### The biggest risk

The article could be misunderstood as "cloud is evil, local is good." That would be too simple. The strength is the nuance: "Cloud is not the answer — cloud is yesterday's question."

### Prediction

If published, this will be **cited**. Not because it's right (time will tell). But because it asks a question everyone working with AI in enterprises is asking — and nobody has articulated clearly.

> **The question isn't "cloud or local." The question is "Who controls the data and the decisions?"**
>
> And Yakoon gives a clear answer: **The enterprise. Not the cloud provider. Not the AI. The enterprise.**
