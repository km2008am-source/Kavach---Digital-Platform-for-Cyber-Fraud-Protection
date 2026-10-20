# Member 3 Q&A: answer honestly, never claim more than the prototype does

- **Isn't this Truecaller?** Caller-ID apps label numbers. Call Shield asks for a reason, checks the claimed organisation against its published numbers, and treats a hang-up as a signal. Kavach also covers the after-fraud hour and training.
- **How would Call Shield work for a real user?** Conditional call forwarding on the user's SIM to the Kavach number, one-time setup. Telephony cost needs a partner (bank or telecom). The demo calls the number directly.
- **Can the simulator train scammers?** Fictional agency, 40-word lines, output filter that blocks real agency and bank names, no export, no free-form mode, and it stops if someone types ID-like numbers.
- **What if the LLM fails mid-call?** Scripted lines per stage, and scoring is plain code, so the session still completes.
- **Is Scam Pulse real?** The clustering is M2's real code; the demo data is a seeded replay and the page says so. Real alerts need real reporters.
- **What are the limits?** Identity check covers only organisations whose numbers we hold (SBI so far); Tamil keyword lists in scoring need a native speaker's review; browser Tamil voice depends on the device; Twilio trial limits.
- **How do you know the web app works without the backend?** Every data page falls back to demo JSON and labels it.
- **Is call audio stored?** Kavach never records or saves audio, and never writes the transcript to its logs. Be precise if pressed: Twilio itself shows request details (including the recognised speech) in its own console for trial accounts, so say "Kavach stores no call audio" rather than "no trace exists anywhere".
