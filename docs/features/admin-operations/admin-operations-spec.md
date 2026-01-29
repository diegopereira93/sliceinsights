# Admin Operations Feature Specification

## User Story
- As an administrator, I want to force a re-seed of the database when I upload new CSV files.
- As an administrator, I want to check if the application can see the required data files.

## Requirements
- `GET /admin/diag`: Returns status of data files and DB connection.
- `POST /admin/seed`: JSON response with count of created items.
- Secret key authentication (`?secret=...`).

## Technical Details
### API Structure
- `GET /admin/diag`
- `POST /admin/seed`

### Security
- Uses `ADMIN_SEED_SECRET` env variable. Default: `sliceinsights2026`.

### Implementation Notes
- Seeding runs synchronously to ensure data integrity during the process.
- Diagnostic checks specific paths in `app/data/`.
