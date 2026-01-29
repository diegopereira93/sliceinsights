# Price Alerts Feature Plan

## Goal
Allow users to track prices of specific paddles and receive notifications when they drop.

## Core Concept
Users are price-sensitive. This feature allows them to "subscribe" to a paddle's price and get alerted (via email/system notification) when it becomes cheaper.

## Proposed Solution
- **Subscription**: API to create an alert for a specific paddle and target price (optional).
- **Monitoring**: Background process (or check during scraper runs) to compare current price vs alert price.
- **Notification**: Send email when condition is met.

## Success Metrics
- Number of alerts created.
- Click-through rate on alert emails.
