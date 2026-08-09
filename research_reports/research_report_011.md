# Project Genesis Research Report

**Created:** 2026-08-09 10:50:58

**Prepared by:** Research AI

**Target audience:** ShiftGuard AI — SaaS attendance tracking for SMBs at $49/month

**Status:** Preliminary and unvalidated

---

## Important Notice

This report was generated using AI reasoning and existing company context.

It does not contain verified live market research unless clearly stated.

Customer interviews and external validation are required before development begins.

---

# Research Report: Preliminary Product Hypotheses for ShiftGuard AI

**Role:** Research AI  
**Project:** Project Genesis  
**Target Audience:** Small and Medium-Sized Businesses (SMBs) struggling with attendance tracking, labor costs, and shift management.  
**Pricing Anchor:** $49/month  

---

## Executive Summary

In accordance with **Principle 1 (Profit First)** and **Principle 2 (Customer Obsession)** of the Project Genesis Constitution, we have formulated exactly three preliminary product hypotheses. These hypotheses target the operational bottlenecks of SMBs managing shift-based workforces. 

*Disclaimer: In line with **Principle 6 (Honest Decisions)**, these ideas are completely unvalidated hypotheses. We have not conducted live web-scraping or primary market testing for these specific iterations. All market assumptions, difficulty scores, and profit potential metrics are analytical estimates that require real-world validation before any development begins.*

---

## Hypothesis 1: ShiftGuard — Biometric Buddy (Anti-Fraud Module)

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** ShiftGuard Biometric Buddy (or *ShiftGuard Anti-Fraud*)
2. **Customer Problem:** "Buddy punching" (employees clocking in or out for one another) and timecard inflation cost SMB owners thousands of dollars annually in unearned wages. Traditional hardware biometric clock-in machines are expensive, difficult to install, and prone to breaking.
3. **Proposed AI Solution:** A lightweight tablet or smartphone app installed at the workplace entrance. It utilizes the device's front-facing camera and lightweight AI facial verification to match the face of the clocking-in employee against their profile image. It flags discrepancies to managers in real-time without storing sensitive raw biometric data.
4. **Why Customers May Pay:** The ROI is immediately visible. If an SMB with 15 employees prevents just 10 hours of fraudulent/inflated hours per month at a $15/hour wage rate, they save $150/month. Paying $49/month is an easy financial decision.
5. **Difficulty Score:** `5 / 10` (Leverages existing facial verification APIs; primary technical effort is secure mobile/web frontend development and secure data pipelines).
6. **Profit Potential Score:** `9 / 10` (Extremely high margins as it runs on the customer's existing hardware, e.g., an old iPad).
7. **Main Risk:** Strict local biometric privacy laws (e.g., BIPA in Illinois, GDPR in Europe) which restrict facial recognition. 
8. **Validation Required:** Speak to 10 retail, hospitality, or warehouse managers to confirm if buddy punching is a top-3 operational drain and if they would trust a software-only facial verification app.

---

## Hypothesis 2: ShiftGuard — PredictFlow (Demand-Based Scheduler)

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** ShiftGuard PredictFlow
2. **Customer Problem:** SMB managers spend hours every week manually creating employee schedules. They often overstaff (wasting money) or understaff (losing sales and burning out employees) because they cannot accurately predict customer demand.
3. **Proposed AI Solution:** An AI integration engine that connects to the business's Point of Sale (POS) system. It analyzes historical sales data, local weather forecasts, and holiday calendars to predict peak hours, automatically generating the optimal shift schedule for the upcoming week in one click.
4. **Why Customers May Pay:** It saves the manager 3–5 hours of tedious scheduling work per week while directly optimizing labor costs and maximizing sales capacity during busy hours. 
5. **Difficulty Score:** `8 / 10` (Requires building secure integrations with popular SMB POS platforms like Square, Clover, or Shopify, alongside a forecasting algorithm).
6. **Profit Potential Score:** `8 / 10` (High stickiness; once a business relies on AI scheduling, they are highly unlikely to churn).
7. **Main Risk:** High friction in data integration. If the target SMB has messy, paper-based, or fragmented POS data, the AI predictions will be inaccurate.
8. **Validation Required:** Create a simple landing page explaining the "AI schedule optimizer." Manually collect past sales data from 3 local businesses, run a manual optimization mock-up, and ask if they would pay $49/month to automate it.

---

## Hypothesis 3: ShiftGuard — Compliance Guardian

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** ShiftGuard Compliance Guardian
2. **Customer Problem:** SMB owners face steep legal fines, lawsuits, and unexpected overtime payouts due to accidental violations of labor laws (e.g., missed mandatory rest breaks, exceeding maximum daily hours, or violating local predictive scheduling laws).
3. **Proposed AI Solution:** A real-time, AI-driven compliance auditor that monitors clock-in/out patterns. It detects when an employee is nearing a violation (e.g., working 5 consecutive hours without a 30-minute meal break) and automatically sends an SMS alert to both the employee and the shift manager to take action.
4. **Why Customers May Pay:** Avoidance of legal fees and government penalties. A single wage-and-hour compliance lawsuit can bankrupt an SMB; a $49/month "insurance" tool is highly cost-effective.
5. **Difficulty Score:** `4 / 10` (The rules engine is largely deterministic, paired with simple natural language parsing for local labor code updates).
6. **Profit Potential Score:** `7 / 10` (Extremely valuable in highly regulated regions like California or New York, but harder to market in states with looser labor laws).
7. **Main Risk:** If the system misses a regulatory rule or fails to alert, the business owner could blame the software for legal penalties.
8. **Validation Required:** Interview 5 HR consultants or labor attorneys to identify the top 3 compliance mistakes SMBs make, and interview 10 local managers to see if they actively worry about wage-and-hour lawsuits.

---

## Recommended Next Steps for Project Genesis

To uphold **Principle 1 (Profit First)** and **Principle 5 (Learn From Everything)**, we should test these hypotheses using the lowest-cost methods possible before writing a single line of production code. 

I recommend starting with **Hypothesis 1 (ShiftGuard Biometric Buddy)**. It has the lowest technical implementation difficulty (5/10), the highest potential ROI for the customer, and does not require complex third-party POS integrations. 

**Proposed Next Action:** Direct our Acquisition or Marketing AI worker (or the founder) to set up a basic landing page for "ShiftGuard Biometric Buddy" targeting local retail/restaurant owners to collect email signups and gauge interest in a beta program.

---

## Current Decision

No product has been approved automatically.

Final product selection requires review and approval from Harshit, Founder of Project Genesis.
