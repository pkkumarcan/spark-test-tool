# Research Package: Folder Structure & Token Budget

## Complete Folder Structure for Domain 1 (AI)

```text
research/
└── Q3_2026/
    └── AI/
        ├── 00_master_brief.md                      # Master brief overview (~800 words | ~1,100 tokens)
        ├── 00a_audience_profile.md                 # Audience profiles and learning levels (~600 words | ~820 tokens)
        ├── 00b_prior_quarters.md                   # Prior quarter coverage & archive refs (~700 words | ~950 tokens)
        ├── 01_topic_map.md                         # Detailed AI topic mapping (~2,200 words | ~3,000 tokens)
        ├── 02_source_index.md                      # Source index and verification links (~4,500 words | ~6,100 tokens)
        ├── 03_deep_notes/                          # Deep-dive research notes on specific topics
        │   ├── agentic_ai_audit.md                 # Agentic AI audit methodologies (~1,200 words | ~1,600 tokens)
        │   ├── fraud_detection_continuous.md       # Fraud detection & continuous monitoring (~1,100 words | ~1,500 tokens)
        │   ├── llm_security_prompt_injection.md    # LLM security & prompt injection prevention (~1,300 words | ~1,800 tokens)
        │   ├── ai_audit_capability_frameworks.md   # AI audit capability frameworks (~1,100 words | ~1,500 tokens)
        │   └── genai_report_writing.md             # GenAI report writing & QA guidelines (~700 words | ~950 tokens)
        ├── 04_quarterly_plan.md                    # Planning parameters & priorities (~1,200 words | ~1,600 tokens)
        ├── 05_watch_list.md                        # Monitored AI risks & regulatory updates (~900 words | ~1,200 tokens)
        ├── 06_monthly_refreshes/                   # Periodic monthly updates
        │   ├── month_1_refresh.md                  # Month 1 update log & scan summary (~500 words | ~680 tokens)
        │   ├── month_2_refresh.md                  # Month 2 update log & scan summary (~500 words | ~680 tokens)
        │   └── month_3_refresh.md                  # Month 3 update log & scan summary (~500 words | ~680 tokens)
        ├── 07_weekly_pulse_log.md                  # Weekly micro-learning & pulse checks (~800 words | ~1,100 tokens)
        ├── 08_feedback_log.md                      # Learner feedback & engagement scores (~600 words | ~820 tokens)
        ├── 09_style_guide.md                       # Format, tone, & visual specs (~800 words | ~1,100 tokens)
        ├── 10_glossary.md                          # Standardized AI auditing definitions (~900 words | ~1,200 tokens)
        ├── 11_approval_tracker.md                  # Content sign-offs & review logs (~500 words | ~680 tokens)
        └── 12_distribution.md                      # Channel-specific publishing specs (~600 words | ~820 tokens)
```

---

## Context Loading Guide - What to Load Per Task

| Task Name | Context Loading Blueprint (Files to Load) | Estimated Token Budget |
| :--- | :--- | :--- |
| **Create Academy Session** | `master_brief` + `topic_map` (session's topic) + `deep_notes/{topic}` + `source_index` (filtered) + `monthly_refreshes` | ~8,000 - 12,000 |
| **Create Audit Spotlight** | `master_brief` + `deep_notes/{topic}` + `source_index` (filtered) + `quarterly_plan` + latest `monthly_refresh` | ~5,000 - 8,000 |
| **Create Audit Pulse** | `deep_notes/{topic}` + `weekly_pulse_log` + `quarterly_plan` | ~2,000 - 4,000 |
| **Run Monthly Refresh** | `watch_list` + `topic_map` + `quarterly_plan` + prior `monthly_refreshes` | ~4,000 - 6,000 |
| **Run Weekly Micro-Check** | `weekly_pulse_log` + `watch_list` + `quarterly_plan` | ~2,000 - 3,000 |

---

## What's Missing? Suggested Additions

| # | Missing Element | Recommendation | Priority |
| :-: | :--- | :--- | :-: |
| 1 | **Audience Profile Document** | Create `00a_audience_profile.md` — defines who the auditors are, their AI maturity level, learning preferences, prior training history. | 🔴 High |
| 2 | **Prior Quarter Archive Reference** | Create `00b_prior_quarters.md` — summary of what was covered in Q1/Q2 to avoid repetition. | 🔴 High |
| 3 | **Feedback & Engagement Log** | Create `08_feedback_log.md` — track session attendance, engagement scores, survey results, content ratings. | 🟡 Medium |
| 4 | **Content Style Guide** | Create `09_style_guide.md` — tone, vocabulary level, visual branding, slide templates, Pulse/Spotlight format specs. | 🟡 Medium |
| 5 | **Glossary of Terms** | Create `10_glossary.md` — standardized definitions for AI terms used across all content. | 🟡 Medium |
| 6 | **Cross-Domain Linkage Map** | Create at `Q3_2026/cross_domain_links.md` — shows where AI topics connect to Risk & Controls and Regulations domains. | 🟡 Medium |
| 7 | **Approval/Sign-off Tracker** | Create `11_approval_tracker.md` — tracks who reviewed and approved each content piece before release. | 🟢 Low |
| 8 | **Distribution Channel Specs** | Create `12_distribution.md` — where each content type is published (email, Teams, LMS, YouTube, intranet). | 🟢 Low |
