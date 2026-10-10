# car-rental-api

## Design decisions
- Custom user model must be defined before the first migration.
- Enforce the price rule with both a validator and a database constraint.
- Do not provide a DELETE endpoint for cars; preserve historical records.
- Never allow users to set their role during registration.
- Use short-lived access tokens and longer-lived refresh tokens.