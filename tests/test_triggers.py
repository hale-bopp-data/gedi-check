"""Tests per gedi_check.triggers"""

import pytest
from gedi_check.triggers import check_fix_keyword, check_no_options_question, record_error
import os

os.environ["GEDI_SESSION"] = "test-pytest"


class TestFixKeyword:
    def test_triggers_on_fix(self):
        found, kw = check_fix_keyword("fix: workaround per il timeout Redis")
        assert found is True
        assert kw.lower() == "fix"

    def test_triggers_on_workaround(self):
        found, kw = check_fix_keyword("applied a workaround for the issue")
        assert found is True

    def test_triggers_on_hardcoded(self):
        found, kw = check_fix_keyword("valore hardcoded nel config")
        assert found is True

    def test_no_trigger_on_clean_text(self):
        found, _ = check_fix_keyword("refactored the authentication module")
        assert found is False

    def test_exclusion_metalinguistic(self):
        found, _ = check_fix_keyword("fix (cerotto) vs soluzione strutturale")
        assert found is False

    def test_exclusion_technical_name(self):
        found, _ = check_fix_keyword("gedi-check --trigger fix keyword detected")
        assert found is False

    def test_exclusion_documentation(self):
        found, _ = check_fix_keyword("fix strutturale proposto: eliminare la dipendenza")
        assert found is False


class TestNoOptionsQuestion:
    def test_triggers_on_question_without_options(self):
        result = check_no_options_question("Vuoi procedere con il deploy?")
        assert result is True

    def test_no_trigger_with_numbered_options(self):
        result = check_no_options_question(
            "Come vuoi procedere?\n1. Deploy immediato\n2. Deploy graduale\n3. Annulla"
        )
        assert result is False

    def test_no_trigger_without_question(self):
        result = check_no_options_question("Ho completato il deploy.")
        assert result is False


class TestErrorRepeat:
    def test_blocks_at_third_repetition(self):
        os.environ["GEDI_SESSION"] = "test-error-repeat"
        block1, count1 = record_error(42, "test error")
        block2, count2 = record_error(42, "test error")
        block3, count3 = record_error(42, "test error")
        assert block1 is False
        assert block2 is False
        assert block3 is True
        assert count3 == 3
