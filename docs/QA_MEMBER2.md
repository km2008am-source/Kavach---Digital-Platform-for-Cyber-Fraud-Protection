# Member 2: judging Q&A prep

Guide sections 13 and 15 list the questions Member 2 answers. Each answer is short enough to say in about 20 seconds, honest about limits, and backed by a number or a file you can show. Numbers are from `eval/report.md` (offline mode).

---

### 1. How does the AI work?
**Say:** "Three independent signals. First, keyword and pattern rules: OTP requests, arrest threats, urgency. Second, link intelligence: lookalike bank domains, cheap scam-prone web addresses, blocklists and domain age. Third, an LLM classifier. We take the strongest signal, and when two agree we add confidence. The LLM is never the only safeguard."
**Show:** `python -m kavach.analysis.cli "<message>"` prints every red flag.

### 2. How accurate is it?
**Say:** "On a test set we locked away before our last change, Kavach caught all 10 scams and flagged none of 12 genuine messages, in about a second. Across all our sets: 90 of 90 scams, and 2 of 58 genuine messages got a 'may be a scam', never 'high'. With no internet, the rules alone still catch 13 of 15 with no false alarms. The sets are small and team-written, so a larger real-world evaluation is our next step."
**If pushed:** "We measured, found problems and fixed them in the open. The rules first scored 0.13 on unseen messages because they'd memorised phrases. The first AI run flagged 9 of 46 genuine messages because it assumed every delivery call was a trick. Each time we locked a new test set away before the fix, and quote only that set."

### 3. What about false positives?
**Say:** "None of the 12 genuine messages in our newest locked test set was flagged. Across all sets, 2 of 58 got a 'may be a scam', never 'high': the AI on its own is never allowed to say 'this is a scam'. The rules need two or more scam signals together, so a bank OTP SMS that says 'do not share your OTP' scores zero."

### 4. What if the LLM hallucinates or is tricked?
**Say:** "The message goes to the LLM as quoted data. We even neutralise a fake closing tag in the message. The rule and link scores can't be lowered by the LLM, so a message that talks the LLM into 'safe' still gets flagged. We test five injection messages, and none is marked safe even when the LLM is fooled. For receipts, any value the LLM returns must literally appear in the OCR text, so it can't invent a transaction ID."

### 5. Why not train your own model?
**Say:** "With 36 hours and no large labelled Indian scam dataset, a trained model would just learn our 60 examples. Rules plus link intelligence are explainable: every verdict says *why* in plain words, which matters for a 62-year-old user. And they work offline. The LLM adds coverage for phrasings rules miss. With real reports from Scam Pulse, training a model is a natural next step."

### 6. How is user data protected? Is Scam Pulse private?
**Say:** "Pulse stores only scam reports, never genuine messages. Phone numbers, UPI IDs, links and amounts are removed before anything is saved. The reporter is stored as a keyed hash with a server secret, and the app refuses to start in demo or production mode if that secret is weak. District is chosen by the user, never GPS. APKs are never run, and we only look up their hash, never upload them."

### 7. Is Scam Pulse real?
**Say:** "In the demo it runs on seeded data, labelled as such. The clustering code is real: it groups similar reports per district and raises an alert at five reports from three different people. Real alerts need real users."

### 8. What was technically hardest?
**Say:** "Combining three uncertain signals into one verdict that is still explainable, and being honest about accuracy. Our first held-out test exposed overfitting, which changed how we built the rules."

### 9. What if the internet fails during the demo?
**Say:** "The engine works fully offline: rules, lookalike checks and a local malware-host list. `DEMO_MODE` serves cached answers for the prepared inputs."

---

**Limits to admit if asked:** see `docs/LIMITATIONS.md`. The main ones: small test sets, numbers measured without the LLM, spoken numbers missed, Tamil keywords not yet reviewed by a native speaker.
