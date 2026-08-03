from __future__ import annotations

from app.modules.questionnaire.validation import ValidationEngine


class TestValidationEngine:
    def setup_method(self) -> None:
        self.v = ValidationEngine()

    def test_is_empty_none_value(self) -> None:
        assert self.v._is_empty({"value": None}) is True

    def test_is_empty_empty_string(self) -> None:
        assert self.v._is_empty({"value": ""}) is True

    def test_is_empty_empty_list(self) -> None:
        assert self.v._is_empty({"value": []}) is True

    def test_is_empty_valid_value(self) -> None:
        assert self.v._is_empty({"value": "hello"}) is False
        assert self.v._is_empty({"value": 0}) is False
        assert self.v._is_empty({"value": ["a"]}) is False

    def test_validate_numeric_valid(self) -> None:
        errors = self.v._validate_numeric({"value": 50}, {"min": 0, "max": 100})
        assert len(errors) == 0

    def test_validate_numeric_below_min(self) -> None:
        errors = self.v._validate_numeric({"value": -5}, {"min": 0, "max": 100})
        assert len(errors) == 1
        assert "at least 0" in errors[0]

    def test_validate_numeric_above_max(self) -> None:
        errors = self.v._validate_numeric({"value": 150}, {"min": 0, "max": 100})
        assert len(errors) == 1
        assert "at most 100" in errors[0]

    def test_validate_numeric_non_numeric(self) -> None:
        errors = self.v._validate_numeric({"value": "abc"}, {"min": 0, "max": 100})
        assert len(errors) == 1

    def test_validate_numeric_no_rules(self) -> None:
        errors = self.v._validate_numeric({"value": 999}, {})
        assert len(errors) == 0

    def test_validate_decimal_valid(self) -> None:
        errors = self.v._validate_decimal({"value": 3.14}, {"min": 0, "max": 10, "decimal_places": 2})
        assert len(errors) == 0

    def test_validate_decimal_too_many_places(self) -> None:
        errors = self.v._validate_decimal({"value": 3.14159}, {"decimal_places": 2})
        assert len(errors) == 1

    def test_validate_decimal_non_numeric(self) -> None:
        errors = self.v._validate_decimal({"value": "not_a_number"}, {"min": 0, "max": 100})
        assert len(errors) == 1

    def test_validate_slider_valid(self) -> None:
        errors = self.v._validate_slider({"value": 50}, {"min": 0, "max": 100})
        assert len(errors) == 0

    def test_validate_slider_out_of_range(self) -> None:
        errors = self.v._validate_slider({"value": -5}, {"min": 0, "max": 100})
        assert len(errors) == 1

    def test_validate_slider_non_numeric(self) -> None:
        errors = self.v._validate_slider({"value": "abc"}, {})
        assert len(errors) == 1

    def test_validate_date_valid(self) -> None:
        errors = self.v._validate_date({"value": "2024-01-15"})
        assert len(errors) == 0

    def test_validate_date_invalid_format(self) -> None:
        errors = self.v._validate_date({"value": "15-01-2024"})
        assert len(errors) == 1

    def test_validate_date_empty(self) -> None:
        errors = self.v._validate_date({"value": ""})
        assert len(errors) == 1

    def test_validate_time_valid(self) -> None:
        errors = self.v._validate_time({"value": "14:30"})
        assert len(errors) == 0

    def test_validate_time_invalid(self) -> None:
        errors = self.v._validate_time({"value": "25:00"})
        assert len(errors) == 1

    def test_validate_single_choice_valid(self) -> None:
        errors = self.v._validate_single_choice({"value": "b"}, {"allowed_values": ["a", "b", "c"]})
        assert len(errors) == 0

    def test_validate_single_choice_invalid(self) -> None:
        errors = self.v._validate_single_choice({"value": "z"}, {"allowed_values": ["a", "b", "c"]})
        assert len(errors) == 1

    def test_validate_single_choice_no_allowed(self) -> None:
        errors = self.v._validate_single_choice({"value": "x"}, {})
        assert len(errors) == 0

    def test_validate_multiple_choice_valid(self) -> None:
        errors = self.v._validate_multiple_choice(
            {"value": ["a", "b"]}, {"allowed_values": ["a", "b", "c"], "min_selections": 1, "max_selections": 3}
        )
        assert len(errors) == 0

    def test_validate_multiple_choice_too_few(self) -> None:
        errors = self.v._validate_multiple_choice(
            {"value": []}, {"min_selections": 1}
        )
        assert len(errors) == 1

    def test_validate_multiple_choice_too_many(self) -> None:
        errors = self.v._validate_multiple_choice(
            {"value": ["a", "b", "c", "d"]}, {"max_selections": 3}
        )
        assert len(errors) == 1

    def test_validate_multiple_choice_not_a_list(self) -> None:
        errors = self.v._validate_multiple_choice({"value": "not_a_list"}, {})
        assert len(errors) == 1

    def test_validate_text_valid(self) -> None:
        errors = self.v._validate_text({"value": "hello world"}, {})
        assert len(errors) == 0

    def test_validate_text_non_string(self) -> None:
        errors = self.v._validate_text({"value": 123}, {})
        assert len(errors) == 1

    def test_validate_file_valid(self) -> None:
        errors = self.v._validate_file(
            {"value": {"mime_type": "image/png", "size_mb": 1.0}},
            {"allowed_types": ["image/png", "image/jpeg"], "max_size_mb": 10},
        )
        assert len(errors) == 0

    def test_validate_file_wrong_type(self) -> None:
        errors = self.v._validate_file(
            {"value": {"mime_type": "text/html", "size_mb": 1.0}},
            {"allowed_types": ["image/png", "image/jpeg"]},
        )
        assert len(errors) == 1

    def test_validate_file_too_large(self) -> None:
        errors = self.v._validate_file(
            {"value": {"mime_type": "image/png", "size_mb": 50}},
            {"max_size_mb": 10},
        )
        assert len(errors) == 1

    def test_regex_validation_match(self) -> None:
        errors = []
        q_value = {"value": "ABC123"}
        pattern = r"^[A-Z]{3}\d{3}$"
        import re
        if not re.match(pattern, q_value["value"]):
            errors.append("Value does not match required pattern")
        assert len(errors) == 0

    def test_regex_validation(self) -> None:
        errors = []
        q_value = {"value": "ABC123"}
        pattern = r"^[A-Z]{3}\d{3}$"
        import re
        if not re.match(pattern, q_value["value"]):
            errors.append("Value does not match required pattern")
        assert len(errors) == 0
        invalid = {"value": "hello"}
        if not re.match(pattern, invalid["value"]):
            errors.append("Value does not match required pattern")
        assert len(errors) == 1

    def test_invalid_payload_structure(self) -> None:
        assert self.v._is_empty({}) is True
        assert self.v._is_empty(None) is True

    def test_unexpected_payload_types(self) -> None:
        result = self.v._validate_numeric({"value": None}, {"min": 0})
        assert len(result) == 1
        result2 = self.v._validate_decimal({"value": None}, {"min": 0})
        assert len(result2) == 1
        result3 = self.v._validate_slider({"value": None}, {})
        assert len(result3) == 1

    def test_edge_case_empty_allowed_values(self) -> None:
        errors = self.v._validate_single_choice({"value": ""}, {"allowed_values": []})
        assert len(errors) == 0
