# SLO threshold constants
# SLO-03: Market Offers (prices) must be refreshed within 24 hours
FRESHNESS_SLO_HOURS = 24

# SLO-04: Product Master Data (specs) must be refreshed within 7 days
COMPLETENESS_SLO_DAYS = 7

# Derived
COMPLETENESS_SLO_HOURS = COMPLETENESS_SLO_DAYS * 24  # 168
