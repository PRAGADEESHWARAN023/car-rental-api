# car-rental-api

## Design decisions
- Custom user model: We define our custom User model before the first migration, because Django connects the user model to permissions, the admin system, and foreign keys, so switching models later can require rebuilding those relationships and the database.
- Price validation: We use both a Python validator and a database constraint, because operations such as Car.objects.create() can bypass a validator, while the database constraint protects data integrity.
- Car deletion: Cars have no DELETE endpoint, because bookings will point to them, and deleting a car would erase the rental history.
- User roles: The server assigns the user's role during registration, because allowing clients to choose their own role could let someone register as an administrator without permission.
- JWT tokens: We use short-lived access tokens and longer-lived refresh tokens, because a leaked access token provides temporary access, while a leaked refresh token may allow an attacker to obtain new access tokens for longer.

# Database Query Optimization

- An N+1 query problem occurs when an API executes an additional database query for each item in a list, often when accessing related objects during serialization.

- The booking endpoint uses Django's select_related() to retrieve related car and user data efficiently. Automated query-count tests compare requests involving different numbers of bookings to detect query growth and prevent regressions.

- Query-count tests measure database query behavior, not HTTP response time or overall performance.

## Why it works this way

### Query optimization
A list endpoint that runs one extra query for every row is called an N+1 problem. My booking list shows each booking's car and customer, so without care it would hit the database once per row. I fetch everything in one go with `select_related()`, and a test compares the query count for 3 and for 10 bookings, so it fails if the count ever starts to grow. These tests measure database queries, not response time, so I don't claim a speed-up beyond that.

### Preventing overlapping bookings
Two people can ask for the same car at the same moment, so the database has the final word: a PostgreSQL exclusion constraint rejects any overlapping booking for the same car, even if some other code path skips my checks. But when I fired 20 simultaneous requests at it, PostgreSQL sometimes aborted one with a deadlock error instead of a clean "car not available". So each booking first locks that car's row. Requests for the same car queue up and go one at a time, while requests for different cars don't wait. The lock keeps things orderly, and the constraint is the guarantee.

### Handling money
Prices, fees and refunds use `Decimal`, never `float`. A float stores a value like 100.10 as an approximation, so a 5% fee can land just on either side of ₹5.005 and round the wrong way. With `Decimal` the fee is exactly 5.005, and `ROUND_HALF_UP` turns it into ₹5.01. A test covers this exact case.