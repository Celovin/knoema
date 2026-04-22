# Payments Onboarding

This section is an operator checklist for payment seller setup. Codex does not register seller accounts, generate live keys, or run live transactions.

- [Toss Payments onboarding, Korean](toss-onboarding-ko.md)
- [Paddle onboarding, English](paddle-onboarding-en.md)

## Environment Check

Run the diagnostic script after the seller accounts exist and the keys are stored in `.env.local`:

```powershell
.venv\Scripts\python.exe scripts\check_payment_env.py
```

The script prints only set or unset status. It never prints key values.
