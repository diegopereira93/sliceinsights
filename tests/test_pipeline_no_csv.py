"""Smoke test: pipeline runs without CSV seed files (SCRP-01)."""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestPipelineWithoutCsv:
    """Verify the pipeline works when data/raw/ has no CSV files."""

    def test_seed_csv_files_deleted(self):
        """app/data/ CSV files no longer exist."""
        assert not os.path.exists("app/data/brazil_pickleball_store.csv"), \
            "brazil_pickleball_store.csv should be deleted"
        assert not os.path.exists("app/data/joola_brazil.csv"), \
            "joola_brazil.csv should be deleted"
        assert not os.path.exists("app/data/paddle_stats_dump.csv"), \
            "paddle_stats_dump.csv should be deleted"

    def test_seed_script_deleted(self):
        """seed_brazil_catalog.py should not exist."""
        assert not os.path.exists("app/db/seed_brazil_catalog.py"), \
            "seed_brazil_catalog.py should be deleted"

    def test_no_import_of_seed_module(self):
        """No Python file should import seed_brazil_catalog."""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "seed_brazil_catalog", "--include=*.py", "-l", "."],
            capture_output=True, text=True
        )
        matches = [
            line for line in result.stdout.strip().split("\n")
            if line and "test_pipeline_no_csv" not in line and ".planning" not in line and "11-03-SUMMARY" not in line
        ]
        assert len(matches) == 0, f"Files still reference seed_brazil_catalog: {matches}"

    def test_json_spec_files_preserved(self):
        """manual_specs.json and scraped_product_specs.json must still exist."""
        assert os.path.exists("app/data/manual_specs.json"), \
            "manual_specs.json should NOT be deleted (used by enrich_from_csv.py)"
        assert os.path.exists("app/data/scraped_product_specs.json"), \
            "scraped_product_specs.json should NOT be deleted (used by scrape_product_specs.py)"

    def test_data_raw_directory_exists(self):
        """data/raw/ directory must exist (with .gitkeep)."""
        assert os.path.isdir("data/raw"), "data/raw/ directory must exist"
        assert os.path.exists("data/raw/.gitkeep"), "data/raw/.gitkeep must exist"

    @patch("app.db.database.init_db_sync")
    def test_ingestor_importable_without_csv(self, mock_init):
        """Ingestor module can be imported without any CSV file dependency."""
        from app.db.ingestor import ingest_rows, is_paddle
        assert callable(ingest_rows)
        assert callable(is_paddle)

    @patch("scripts.scrape_yosports.init_db_sync")
    @patch("scripts.scrape_yosports.Session")
    @patch("scripts.scrape_yosports.ingest_rows")
    @patch("scripts.scrape_yosports.fetch_shopify_products")
    def test_scraper_runs_without_csv_dependency(self, mock_fetch, mock_ingest, mock_session, mock_init):
        """A representative scraper (yoSports) runs without CSV file access."""
        mock_fetch.return_value = []
        mock_ingest.return_value = {"created": 0, "updated": 0, "skipped": 0}
        mock_store = MagicMock()
        mock_store.id = 1
        mock_sess = MagicMock()
        mock_sess.exec.return_value.one.return_value = mock_store
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_sess)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        from scripts.scrape_yosports import main
        main()
