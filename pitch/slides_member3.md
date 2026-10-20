# Member 3 slides: 1, 2, 3, 8, 9, 14 (about 20 words on screen each; the rest is speaker notes)

Rule: no slide claims a feature that is not working. Pulse is "demo data". Re-check every line against the build before H33.

## Slide 1: Kavach (15 s)
- On screen: logo, "One WhatsApp number that protects you before, during and after a scam", WhatsApp chat mock-up (use a real screenshot from the demo phone).
- Say: "What if every Indian had a fraud expert one WhatsApp message away? Here's why they need one."

## Slide 2: The problem (30 s)
- On screen: big number "₹1,935 crore lost to digital arrest scams in 2024", small line "1.23 lakh complaints". Three icons: pressure / late response / scattered help.
- Source line on slide: Minister of State for Home Affairs, written reply in the Rajya Sabha, March 2025 (as reported by Inc42, https://inc42.com/?p=504907).
- BEFORE PRESENTING: open the primary Parliament reply (Rajya Sabha / MHA site), confirm both numbers and the year, and cite that instead. Do not present a figure you have not confirmed.
- Say: "Scams work by pressure. Victims act too late. And the help exists, 1930, Sanchar Saathi, but it is scattered, in English, and not what a panicked person thinks of first. Let's make this personal."

## Slide 3: Meet Lakshmi (20 s)
- On screen: persona card (62, Coimbatore, Tamil-speaking) and a before / during / after timeline.
- Say: "Lakshmi gets a call from a 'customs officer'. He says a parcel in her name has illegal items. She panics. She has no idea who to call. This is what Kavach does for her."
- Persona is fictional: say so on the slide in small print.

## Slide 8: Call Shield (20 s)
- On screen: call flow (Caller > Twilio > notice > speech > verdict > WhatsApp alert) and a screenshot of the real alert.
- Say: "Caller-ID apps label numbers. Call Shield asks the caller why they are calling, judges the answer, checks whether the organisation they claim matches its published numbers, and treats a hang-up as a signal. In production it works through call forwarding on the user's SIM, a one-time setup. Today's demo calls our number directly."
- Honest limits (for Q&A, not the slide): the identity check only has SBI's published numbers; agencies like CBI and police have none, because real officers do not phone about money. Twilio trial plays a short Twilio notice and only calls verified numbers.

## Slide 9: Manipulation X-Ray (20 s)
- On screen: simulator screenshot with tactic chips, plus the before / after score card (use numbers from your own test sessions only).
- Say: "A fictional officer from a made-up agency uses real pressure tactics. Each one is named as it happens: urgency, authority, isolation, fear, secrecy, payment push. At the end she gets a debrief and a score, and the same quiz before and after."
- Do not quote an improvement figure you did not measure.

## Slide 14: Team and close (15 s)
- On screen: three names and roles, team photo, QR to the repo.
- Say: "Three of us, three layers: M1 the WhatsApp experience, M2 the verdict engine, M3 voice, web and pitch. Lakshmi didn't lose her savings. Kavach made sure she knew what to do."
