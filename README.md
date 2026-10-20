# Kavach---Digital-Platform-for-Cyber-Fraud-Protection
A digital platform for cyber fraud protection for Indian citizens before, during and after scams occur.

## Analysis engine (Person 2)

Scam Check, link intelligence, APK scanner, Scam Bait Verifier, Scam Pulse and receipt OCR live in `backend/kavach/analysis/`.

```bash
cd backend
pip install -e ".[test]"        # Python 3.11+
pytest -q                       # offline test suite
python ../eval/evaluate.py      # accuracy report -> eval/report.md
```

- **Known limitations:** [docs/LIMITATIONS.md](docs/LIMITATIONS.md)
- **Work log (why / how / what):** [docs/MEMBER2_LOG.md](docs/MEMBER2_LOG.md)
- **Accuracy:** [eval/report.md](eval/report.md)
