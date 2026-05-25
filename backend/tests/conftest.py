"""Shared pytest fixtures live here. Populated as tasks need them."""

from dotenv import load_dotenv

# Load backend/.env early so env-gated tests (e.g. test_e2e_with_api) see the key.
load_dotenv()
