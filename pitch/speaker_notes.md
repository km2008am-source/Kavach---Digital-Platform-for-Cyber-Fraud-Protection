# Speaker notes (Member 3)

No em dashes. Plain words. Use "we" in the team intro and "I" on Call Shield, Simulator, and close.

## Slide 1

What if every Indian had a fraud expert one WhatsApp message away? That is Kavach.

Transition: Here's why they need one.

## Slide 2

Read the cited government figure. Then: scams work because they rush you, because the first hour after a payment is messy, and because 1930, Chakshu and bank apps sit in different places.

Transition: Let's make this personal.

## Slide 3

Lakshmi is 62. She gets a call about a parcel and an arrest. She is scared and she does not know who is real.

Transition: This is what Kavach does for her.

## Demo narration

Follow `demo_script.md`. Keep eyes on the mirrored phone for steps 1 to 4, then the laptop.

## Slide 8

Caller-ID apps guess a number. We ask the caller to speak, we score the story, and we check the claimed office against numbers published on official sites. In production this sits behind conditional call forwarding. Today you called our Twilio line.

Transition: And for the calls that get through, we train people.

## Slide 9

The simulator is labelled as training. The caller is fictional. Each line is tagged: urgency, authority, isolation, fear, secrecy, payment push. If you type an Aadhaar-like number, we stop the drill and teach that lesson.

Transition: Kavach also watches the threats themselves.

## Slide 14

Three of us. WhatsApp, verdicts, voice and web. Closing line: Lakshmi didn't lose her savings. Kavach made sure she knew what to do.

Then Q&A.

## Q&A I own

Why this problem? Pressure plus late response plus English-only tools.

Truecaller comparison? They label a number. We screen the reason for the call and we stay on WhatsApp.

Call forwarding in production? After a missed or rejected call, the operator forwards to Kavach. Demo uses a direct Twilio number because we are on a trial.

Simulator misuse? Guardrails: fictional agency, no real IDs, stop on Aadhaar-like input, debrief that sends people to 1930.
