# AI Operational Risk Management Platform — Top 5 Use Cases

> These use cases represent the highest-value scenarios the platform addresses. Each maps to a specific audience, a real business problem, and a measurable outcome.

---

## Use Case 1: AI Risk Scoring for Insurance Underwriting

**Primary Audience:** Insurer (Underwriting / Portfolio Risk)

### Problem
Insurers have no standardised, auditable way to assess the operational risk of an organisation's AI systems before writing a policy. Pricing is guesswork. Accumulation risk across a portfolio is invisible.

### How the Platform Solves It
The platform continuously calculates a risk score (AAA → B) for every AI system in production, based on eight domains: availability, performance, drift, security, governance, third-party dependency, compliance, and incident history. Each score is explainable, time-stamped, and audit-ready.

### Key Screens
- Executive Risk Overview (risk grade distribution chart)
- System Risk Detail Page (radar chart + trend lines)
- Portfolio Risk Dashboard (cross-client accumulation view)

### Outcome
- Insurers can price AI risk policies with confidence
- Underwriters can monitor portfolio exposure in real time
- Risk deterioration triggers proactive policy review

### Why It Matters
> One dataset replaces months of manual due diligence. The risk score becomes the underwriting input.

---

## Use Case 2: Parametric Insurance Trigger Monitoring & Claims Evidence

**Primary Audience:** Insurer (Claims / Underwriting)

### Problem
Parametric insurance policies pay out when a defined event occurs — but proving that an event happened, when it started, how long it lasted, and what the financial impact was requires evidence that most organisations cannot produce quickly or reliably.

### How the Platform Solves It
The platform monitors all AI systems against pre-defined trigger thresholds (e.g. outage > 1 hour, accuracy drop > 10%, provider outage > 2 hours). When a threshold is breached, the event is automatically logged, classified, and an **Evidence Pack PDF** is generated containing:

- Incident timeline
- System logs and metrics
- Third-party provider status
- Drift metrics at time of event
- Financial exposure estimate
- Policy clause mapping
- Audit trail and sign-off

### Key Screens
- Insurance Trigger Dashboard
- Incident Dashboard
- Evidence Pack (auto-generated PDF)

### Outcome
- Trigger events are captured automatically — no manual reporting
- Claims are supported by timestamped, auditable evidence
- Dispute resolution is faster and objective

### Why It Matters
> This turns a manual, contested claims process into an automated, verifiable one. It is the critical enabler for parametric AI insurance products.

---

## Use Case 3: DORA & EU AI Act Compliance Reporting

**Primary Audience:** Audit Partner (External Audit / Risk / Compliance)

### Problem
Regulated organisations must demonstrate compliance with DORA (Digital Operational Resilience Act) and the EU AI Act. This requires maintaining an AI inventory, documenting third-party dependencies, evidencing human oversight, and producing structured incident reports — currently a fragmented, manual process.

### How the Platform Solves It
The platform maintains a live compliance dashboard mapped directly to DORA and EU AI Act requirements. Every AI system has a documented:

- Risk assessment
- Third-party dependency register (with criticality and fallback status)
- Incident history
- Governance controls checklist
- Human oversight status

A compliance score is calculated and tracked over time. Monthly reporting packs are generated automatically for the audit partner.

### Key Screens
- Compliance Dashboard (DORA / EU AI Act)
- AI Risk Register
- System Risk Detail Page — Controls & Third-Party sections
- Monthly Reporting Pack

### Outcome
- Audit-ready compliance documentation at any time
- Gaps identified and tracked to resolution
- Regulator submissions supported by structured evidence

### Why It Matters
> DORA became enforceable in January 2025. EU AI Act obligations are phased through 2026–2027. Organisations that cannot evidence compliance face fines and reputational risk. This platform makes compliance continuous rather than point-in-time.

---

## Use Case 4: AI Incident Management & Operational Resilience

**Primary Audience:** Engineering / Ops (Internal Teams) + Audit Partner

### Problem
When an AI system fails — model drift, provider outage, hallucination event — there is no centralised system to detect the failure, quantify the impact, trigger a response, and produce a structured post-incident record. Incidents are handled ad hoc and often go unrecorded.

### How the Platform Solves It
The platform monitors live system metrics (requests per minute, latency, error rate, accuracy, fallback usage) and automatically detects anomalies. When an incident occurs:

1. It is classified by type (outage, drift, hallucination, provider failure)
2. Severity and financial impact are estimated
3. Mean time to detect (MTTD) and mean time to recover (MTTR) are recorded
4. The incident feeds the AI Risk Register and compliance records
5. If it meets a trigger threshold, the Insurance Trigger Dashboard flags it

### Key Screens
- System Monitoring Dashboard
- Incident Dashboard
- Drift & Performance Dashboard

### Outcome
- Faster detection and response to AI failures
- Structured incident records that satisfy DORA reporting requirements
- Incident history that informs insurance pricing and risk scoring

### Why It Matters
> AI incidents are inevitable. The difference between a managed event and a regulatory or financial liability is whether the organisation can detect, respond to, and evidence what happened.

---

## Use Case 5: Executive & Board-Level AI Risk Visibility

**Primary Audience:** Board / Executives + Audit Partner

### Problem
Boards and senior executives are accountable for AI risk under DORA and the EU AI Act, but they have no accessible, non-technical view of their organisation's AI risk exposure. Risk remains siloed in engineering teams and is only surfaced when something goes wrong.

### How the Platform Solves It
The Executive Risk Overview dashboard provides a single-screen summary of the organisation's entire AI risk posture, including:

- Total AI systems in production
- Average risk score and grade distribution
- High-risk systems and their owners
- Critical incidents in the last 90 days
- Estimated financial exposure
- Insurance trigger events

This view is designed to be understood in under 60 seconds, with drill-down available for any system or metric.

### Key Screens
- Executive Risk Overview (primary landing screen)
- System Risk Detail Page (drill-down)
- Monthly Reporting Pack (board-ready PDF)

### Outcome
- Board members can fulfil their AI governance obligations with confidence
- Risk conversations are grounded in data, not anecdote
- Audit partners have a clear view of executive awareness and oversight

### Why It Matters
> Regulators expect boards to demonstrate active oversight of AI risk. This screen is the evidence that oversight exists — and it doubles as the opening slide when onboarding a new audit or insurance client.

---

## Summary

| # | Use Case | Primary Audience | Core Value |
|---|----------|-----------------|------------|
| 1 | AI Risk Scoring for Insurance Underwriting | Insurer | Structured, priceable risk data |
| 2 | Parametric Trigger Monitoring & Claims Evidence | Insurer | Automated evidence for policy payouts |
| 3 | DORA & EU AI Act Compliance Reporting | Audit Partner | Continuous, audit-ready compliance |
| 4 | AI Incident Management & Operational Resilience | Engineering / Audit | Detection, response, and structured records |
| 5 | Executive & Board-Level AI Risk Visibility | Board / Executives | Governance oversight and stakeholder reporting |

> These five use cases represent the commercial, regulatory, and operational pillars of the platform. Together they address the needs of all three buyer audiences from a single data layer.
