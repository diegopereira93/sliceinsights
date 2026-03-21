"""
Unified scraper entry point with real-time SLO validation.

Usage:
  python scripts/run_scraper.py <scraper_name>
  python scripts/run_scraper.py mercado_livre
  python scripts/run_scraper.py brazil_pickleball_store

After the named scraper's main() completes successfully, validate_job_slo is
called for that scraper.  The SLO check is non-blocking — a failure there will
never prevent the scraper result from being recorded.
"""
import sys
import importlib
from pathlib import Path

# Allow importing sibling scripts as modules
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Map CLI argument → module name inside scripts/
SCRAPER_MODULES: dict[str, str] = {
    "brazil_pickleball_store": "scrape_brazil_store",
    "drop_shot_brasil": "scrape_dropshot_brasil",
    "joola": "scrape_joola",
    "just_paddles": "scrape_justpaddles",
    "pcklhouse": "scrape_pcklhouse",
    "propadel": "scrape_propadel",
    "prospin": "scrape_prospin",
    "shark": "scrape_shark",
    "supremo": "scrape_supremo",
    "yosports": "scrape_yosports",
}


def run_scraper(scraper_name: str) -> None:
    """Import and execute the named scraper's main(), then trigger SLO validation."""
    module_name = SCRAPER_MODULES.get(scraper_name)
    if module_name is None:
        available = ", ".join(sorted(SCRAPER_MODULES.keys()))
        print(f"[run_scraper] Unknown scraper: '{scraper_name}'")
        print(f"[run_scraper] Available scrapers: {available}")
        sys.exit(1)

    print(f"[run_scraper] Starting scraper: {scraper_name} (module={module_name})")

    module = importlib.import_module(module_name)
    if not hasattr(module, "main"):
        print(f"[run_scraper] ERROR: {module_name} has no main() function")
        sys.exit(1)

    module.main()

    print(f"[run_scraper] Scraper finished: {scraper_name}")

    # Non-blocking SLO validation — runs immediately after data is committed
    try:
        from scraper_utils import finish_run
        finish_run(scraper_name)
    except Exception as exc:
        print(f"[run_scraper] WARNING: SLO hook failed (non-blocking): {exc}")

    print(f"[run_scraper] Done: {scraper_name}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_scraper.py <scraper_name>")
        print(f"Available: {', '.join(sorted(SCRAPER_MODULES.keys()))}")
        sys.exit(1)

    scraper_name = sys.argv[1]
    run_scraper(scraper_name)


if __name__ == "__main__":
    main()
