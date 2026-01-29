# Price Alerts Feature Specification

## User Story
- As a user, I want to be notified if the "Joola Perseus" drops below R$ 1500.

## Requirements
- Create alert for a paddle.
- (Implicit) Delete/Unsubscribe alert.
- Trigger notifications when price updates.

## Technical Details
### Data Model
- **PriceAlert**: `id`, `user_email`, `paddle_id`, `target_price`, `is_active`.

### API Structure
- `POST /alerts`: Create new alert.
- `GET /alerts/{email}`: List active alerts (Optional, based on implementation).

### Implementation Notes
- Currently implemented as a model and likely an endpoint in `app/api/endpoints/alerts.py`.
