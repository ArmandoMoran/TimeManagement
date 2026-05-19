-- Creates the test database used by pytest integration and Playwright e2e tiers.
-- Runs once when the Postgres volume is first initialized.
CREATE DATABASE timetrack_test OWNER timetrack;
