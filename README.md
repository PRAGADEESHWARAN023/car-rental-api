# car-rental-api

## Design decisions
- Custom user model: We define our custom User model before the first migration, because Django connects the user model to permissions, the admin system, and foreign keys, so switching models later can require rebuilding those relationships and the database.
- Price validation: We use both a Python validator and a database constraint, because operations such as Car.objects.create() can bypass a validator, while the database constraint protects data integrity.
- Car deletion: Cars have no DELETE endpoint, because bookings will point to them, and deleting a car would erase the rental history.
- User roles: The server assigns the user's role during registration, because allowing clients to choose their own role could let someone register as an administrator without permission.
- JWT tokens: We use short-lived access tokens and longer-lived refresh tokens, because a leaked access token provides temporary access, while a leaked refresh token may allow an attacker to obtain new access tokens for longer.