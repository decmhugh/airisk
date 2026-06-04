# AI Operational Risk Management Platform — Dashboard Specification

> **Audience Key**
> | Label Used | Represents | View Purpose |
> |------------|------------|--------------|
> | **Audit Partner** | External audit / risk / compliance firm | Regulatory oversight, risk registers, DORA / EU AI Act |
> | **Insurer** | Underwriting / insurance / portfolio risk firm | Trigger events, exposure pricing, accumulation risk |
> | **Engineering / Ops** | Internal client engineering & operations teams | Live monitoring, incident response, performance |

---

## 1. Overall Platform Dashboard Structure

### Main Navigation

| Section | Audience |
|---------|----------|
| **Dashboard** | All |
| **Executive Risk Overview** | Board / Executives |
| **AI Risk Register** | Risk / Audit |
| **System Monitoring** | Engineering |
| **Drift & Performance** | Data Science |
| **Incidents** | Risk / Ops |
| **Insurance Triggers** | Insurer |
| **Portfolio Risk** | Insurer |
| **Compliance (DORA / EU AI Act)** | Audit |
| **Reports** | All |
| **Evidence Packs** | Audit / Insurer |

> You are building **one platform**, but three distinct dashboard views tailored to each audience above.

---

## 2. Executive Risk Overview Dashboard *(High Priority)*

This is the **first screen** a user lands on.

**Purpose:** Provide a single-pane view of overall AI risk exposure across the organisation.

### Top Panel — KPIs

| KPI | Description |
|-----|-------------|
| Number of AI Systems | Total in production |
| Average AI Risk Score | Across all systems |
| High Risk Systems | Score > 65 |
| Critical Incidents (90 days) | Count |
| AI Downtime (hours) | Last 90 days |
| Drift Events | Last 90 days |
| Insurance Trigger Events | Count |
| Estimated Financial Exposure | € |

### Risk Distribution Chart

Bar chart showing number of systems per risk grade — **critical for insurers**.

| Risk Grade | Number of Systems |
|-----------|------------------|
| AAA | 2 |
| AA | 5 |
| A | 8 |
| BBB | 4 |
| BB | 3 |
| B | 1 |

### Top Risk Systems Table

| System | Business Use | Risk Score | Grade | Main Risk | Owner |
|--------|-------------|-----------|-------|-----------|-------|
| Fraud AI | Payments | 79 | BB | Third-party dependency | John |
| Chatbot | Customer Support | 42 | A | Hallucinations | Sarah |
| Credit Model | Lending | 68 | BB | Drift | Mark |

---

## 3. AI Risk Register *(Audit Partner View)*

A structured risk register scoped specifically to AI systems, used by the external audit and compliance team to assess, track, and report on AI risk.

### Register Table

| System | Owner | Use Case | Criticality | Risk Score | Grade | Last Review | Issues | Status |
|--------|-------|----------|-------------|-----------|-------|-------------|--------|--------|
| Fraud AI | Risk Dept | Fraud detection | High | 79 | BB | Mar 2026 | Drift | Open |
| Chatbot | Ops | Customer support | Medium | 42 | A | Mar 2026 | Hallucinations | Monitoring |

Clicking a system opens a full **System Risk Detail Page**.

---

### System Risk Detail Page

#### Section 1 — Risk Score Breakdown *(Radar Chart)*

| Domain | Score |
|--------|-------|
| Availability | 62 |
| Performance | 58 |
| Drift | 71 |
| Security | 30 |
| Governance | 25 |
| Third-Party | 80 |
| Compliance | 20 |
| Incident | 55 |

#### Section 2 — Trend Over Time *(Line Charts)*

- Risk score over last 12 months
- Drift score trend
- Accuracy trend
- Uptime trend

> Trend data is particularly valuable for insurers when assessing deterioration patterns.

#### Section 3 — Incidents

| Date | Incident | Duration | Impact | Insurance Trigger |
|------|----------|----------|--------|-------------------|
| 12 Feb | OpenAI outage | 2h | Service down | Yes |
| 03 Mar | Drift detected | N/A | Accuracy drop | No |

#### Section 4 — Controls / Governance

| Control | Status |
|---------|--------|
| Model owner | ✅ Yes |
| Monitoring | ✅ Yes |
| Logging | ✅ Yes |
| Human oversight | ⚠️ Partial |
| Rollback | ✅ Yes |
| Testing | ✅ Yes |

#### Section 5 — Third-Party Dependencies *(DORA Critical)*

| Provider | Service | Critical | Fallback |
|---------|---------|----------|---------|
| OpenAI | LLM | Yes | No |
| AWS | Hosting | Yes | Multi-region |

> Third-party dependency mapping is a core requirement under **DORA** and must be maintained for all production AI systems.

---

## 4. System Monitoring Dashboard *(Engineering / Ops View)*

A real-time operational dashboard — similar in style to tools like Datadog — used by internal engineering and operations teams.

### Metrics & Chart Types

| Metric | Chart Type |
|--------|-----------|
| Requests per minute | Line |
| Latency P50 / P95 | Line |
| Error rate | Line |
| Uptime | % gauge |
| Cost per day | Line |
| Drift score | Line |
| Accuracy | Line |
| Hallucination rate | Line |
| Human override rate | Line |
| Fallback usage | Count |

---

## 5. Drift & Performance Dashboard *(Data Science View)*

| Metric | Description |
|--------|-------------|
| PSI | Data drift measurement |
| Accuracy | Overall model performance |
| Precision / Recall | Classification model metrics |
| Hallucination rate | LLM-specific quality metric |
| Output distribution | Change detection across outputs |
| Embedding drift | Vector DB / semantic drift |

**Alerts surfaced:**
- Drift alerts
- Performance degradation alerts
- Model version change notifications

---

## 6. Incident Dashboard

| Incident ID | System | Type | Severity | Duration | Financial Impact | Insurance Trigger |
|------------|--------|------|----------|----------|-----------------|-------------------|
| INC-001 | Fraud AI | Outage | High | 2h | €120k | Yes |
| INC-002 | Chatbot | Hallucination | Medium | N/A | €5k | No |

**Summary metrics shown:**
- Mean time to detect (MTTD)
- Mean time to recover (MTTR)
- Incidents per system
- Incidents per provider

> Incident history and financial impact data feed directly into insurance pricing models.

---

## 7. Insurance Trigger Dashboard *(Insurer View — High Priority)*

This dashboard is purpose-built for the underwriting and insurance team to track parametric trigger events and manage payout eligibility.

### Trigger Events Table

| Date | System | Trigger | Duration | Payout Band | Status |
|------|--------|---------|----------|------------|--------|
| 12 Feb | Fraud AI | Outage > 1h | 2h | Band 2 | Eligible |
| 22 Feb | Chatbot | Accuracy drop | 3 days | Band 1 | Under Review |
| 05 Mar | LLM | Provider outage | 4h | Band 3 | Eligible |

### Trigger Definitions Panel

| Trigger | Threshold | Indicative Payout |
|---------|-----------|------------------|
| Outage | > 1h | €10,000 |
| Outage | > 4h | €50,000 |
| Accuracy drop | > 10% | €25,000 |
| Drift PSI | > 0.25 | €15,000 |
| Provider outage | > 2h | €20,000 |

---

## 8. Portfolio Risk Dashboard *(Insurer View)*

An aggregated cross-client view used by the insurer to manage **accumulation risk** across the entire book of insured AI systems.

### Client Portfolio Table

| Client | AI Systems | Avg Score | High Risk Systems | Incidents | Estimated Exposure |
|--------|-----------|-----------|------------------|-----------|-------------------|
| Bank A | 12 | 48 | 2 | 5 | €5M |
| Fintech B | 5 | 62 | 3 | 8 | €8M |
| SaaS C | 3 | 35 | 0 | 1 | €1M |

### Risk Heatmap *(Criticality vs Score)*

|  | Low Criticality | Medium Criticality | High Criticality |
|--|----------------|--------------------|-----------------|
| **Low Score** | 🟢 | 🟢 | 🟡 |
| **Medium Score** | 🟢 | 🟡 | 🟠 |
| **High Score** | 🟡 | 🟠 | 🔴 |

> This heatmap enables the insurer to identify correlated risk concentrations and manage portfolio-level exposure.

---

## 9. Compliance Dashboard *(Audit Partner View — DORA / EU AI Act)*

| Requirement | Status |
|------------|--------|
| AI inventory | ✅ Complete |
| Risk assessment | ✅ Complete |
| Monitoring | ✅ Complete |
| Incident reporting | ✅ Complete |
| Third-party risk | ⚠️ Partial |
| Business continuity | ✅ Complete |
| Human oversight | ⚠️ Partial |
| Logging | ✅ Complete |
| Documentation | ✅ Complete |

An overall **compliance score** is calculated and displayed at the top of this view.

---

## 10. Monthly Reporting Pack

Distributed to three audiences each month:

- **Client** (internal leadership)
- **Audit Partner** (external audit / risk / compliance)
- **Insurer** (underwriting and portfolio risk)

### Report Structure

#### 1. Executive Summary
- Overall risk score
- Major incidents
- Drift events
- Downtime hours
- Insurance triggers activated
- Key risks identified

#### 2. Risk Score Summary

| System | Score | Grade | Change vs Prior Month |
|--------|-------|-------|-----------------------|

#### 3. Incident Summary

| Incident | Duration | Impact |

#### 4. Drift & Performance
- Accuracy trends
- Drift trends (PSI over time)

#### 5. Availability
- Uptime percentage
- Latency statistics
- Error rates

#### 6. Controls & Governance Changes
- New models deployed
- Model updates
- Control gaps identified

#### 7. Insurance Trigger Events
- Trigger evidence
- Duration
- Severity classification

#### 8. Recommendations
- Add fallback provider
- Improve monitoring coverage
- Add human review layer
- Retrain model
- Other governance actions

---

## 11. Evidence Pack *(For Insurance Claims — Parametric)*

When a trigger event occurs, the platform automatically generates a **PDF evidence pack** to support the insurance claim process.

### Evidence Pack Contents

| Section | Contents |
|---------|---------|
| Incident summary | What happened and systems affected |
| Timeline | Start time, end time, recovery time |
| Logs | System and application logs |
| Metrics | Latency, uptime, error rates during event |
| Provider status | Third-party provider status records (e.g. cloud/LLM) |
| Drift metrics | PSI values at time of event |
| Financial exposure | Estimated monetary impact |
| Policy trigger | Which policy clause was activated |
| Risk score at time | Recorded risk score at time of incident |
| Sign-off | Audit trail and approvals |

> Automated evidence pack generation is a **critical capability** for parametric insurance products — it removes manual claims preparation and provides auditable, timestamped proof.

---

## 12. Platform Value Summary

The platform produces **three distinct outputs from a single dataset**:

| Output | Primary Consumer |
|--------|-----------------|
| AI Risk Score | Insurer (pricing, triggers, accumulation) |
| AI Compliance Report | Audit Partner (DORA, EU AI Act, governance) |
| AI Monitoring Dashboard | Engineering / Ops (live system health) |

> **This is the core commercial proposition** — one data layer, three buyer segments, each with high willingness to pay.

---

## 13. MVP — The 5 Screens To Build First

If you build only these five, you have a deployable product:

| Priority | Screen | Why |
|---------|--------|-----|
| 1 | Executive Risk Overview | Sells the platform to leadership |
| 2 | System Risk Detail Page | Core audit and insurer analysis tool |
| 3 | Monitoring Dashboard | Engineering adoption and daily use |
| 4 | Incident Dashboard | Feeds insurance pricing and claims |
| 5 | Insurance Trigger Dashboard | Direct commercial value for insurer |

---

## 14. Positioning & Messaging

When presenting this platform to an external audit firm or an insurance underwriter, **do not frame it as a technology tool**.

Frame it as:

> ### AI Operational Risk Management Platform
>
> Supporting compliance with:
> - **DORA** — Digital Operational Resilience Act
> - **EU AI Act** — High-risk AI system requirements
> - **AI Risk Auditing** — Structured register, scoring, and evidence
> - **AI Insurance** — Parametric trigger monitoring and claims evidence
> - **AI Incident Management** — Detection, response, and reporting
> - **AI Governance** — Ownership, controls, and oversight documentation

That positioning resonates with both auditors and underwriters — it maps to obligations they already carry, rather than asking them to evaluate a technology product.

---

## Next Steps

Define the **database schema** — tables and fields required to power all of the above views.

Key entities will include: `ai_systems`, `risk_scores`, `incidents`, `drift_events`, `trigger_events`, `controls`, `third_party_dependencies`, `compliance_requirements`, `evidence_packs`, `clients`, `reports`.
