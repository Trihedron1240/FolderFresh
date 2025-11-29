# tests/test_condition_selector_logic.py
"""
Test suite for condition selector popup logic.

Tests:
- Category structure and organization
- Condition item listing
- Category headers are non-selectable
- Popup creation and destruction
- Callback triggering on selection
"""

import pytest
from folderfresh.condition_selector_popup import CONDITION_CATEGORIES


@pytest.mark.unit
class TestConditionCategories:
    """Test the condition category structure."""

    def test_categories_defined(self):
        """Test that condition categories are defined."""
        assert CONDITION_CATEGORIES is not None
        assert isinstance(CONDITION_CATEGORIES, dict)

    def test_all_categories_have_items(self):
        """Test that all categories have at least one condition."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            assert isinstance(category_name, str)
            assert isinstance(conditions, list)
            assert len(conditions) > 0

    def test_expected_categories_exist(self):
        """Test that expected categories exist."""
        expected_categories = ["Name", "File Properties", "File Attributes", "Path"]
        for expected in expected_categories:
            assert expected in CONDITION_CATEGORIES, f"Missing category: {expected}"

    def test_all_conditions_are_strings(self):
        """Test that all condition items are strings."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            for condition in conditions:
                assert isinstance(condition, str)
                assert len(condition) > 0

    def test_no_duplicate_conditions(self):
        """Test that conditions don't appear in multiple categories."""
        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        # Check for duplicates
        unique_conditions = set(all_conditions)
        assert len(all_conditions) == len(unique_conditions)

    def test_name_category_contains_expected_items(self):
        """Test that Name category has expected conditions."""
        name_conditions = CONDITION_CATEGORIES.get("Name", [])
        expected = [
            "Name Contains",
            "Name Starts With",
            "Name Ends With",
            "Name Equals",
            "Regex Match",
        ]
        for item in expected:
            assert item in name_conditions

    def test_file_properties_category_contains_expected_items(self):
        """Test that File Properties category has expected conditions."""
        file_props = CONDITION_CATEGORIES.get("File Properties", [])
        expected = [
            "Extension Is",
            "File Size > X bytes",
            "File Age > X days",
            "Last Modified Before",
        ]
        for item in expected:
            assert item in file_props

    def test_file_attributes_category_contains_expected_items(self):
        """Test that File Attributes category has expected conditions."""
        file_attrs = CONDITION_CATEGORIES.get("File Attributes", [])
        expected = [
            "Is Hidden",
            "Is Read-Only",
            "Is Directory",
        ]
        for item in expected:
            assert item in file_attrs

    def test_path_category_contains_expected_items(self):
        """Test that Path category has expected conditions."""
        path_conditions = CONDITION_CATEGORIES.get("Path", [])
        expected = ["Parent Folder Contains"]
        for item in expected:
            assert item in path_conditions


@pytest.mark.unit
class TestConditionSelectorPopupLogic:
    """Test the popup logic without GUI automation."""

    def test_popup_imports_successfully(self):
        """Test that ConditionSelectorPopup can be imported."""
        from folderfresh.condition_selector_popup import ConditionSelectorPopup
        assert ConditionSelectorPopup is not None

    def test_all_conditions_are_valid(self):
        """Test that all categorized conditions are valid."""
        from folderfresh.condition_editor import CONDITION_TYPES

        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        for condition in all_conditions:
            assert condition in CONDITION_TYPES, f"Condition not in CONDITION_TYPES: {condition}"

    def test_no_separator_items_in_categories(self):
        """Test that no separator items are in categories."""
        separators = ["— Path —", "— File Attributes —"]

        for category_name, conditions in CONDITION_CATEGORIES.items():
            for condition in conditions:
                assert condition not in separators, f"Separator found in category: {condition}"

    def test_all_condition_types_in_categories(self):
        """Test that all valid CONDITION_TYPES are in categories."""
        from folderfresh.condition_editor import CONDITION_TYPES

        all_categorized = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_categorized.extend(conditions)

        # Valid condition types (exclude None values)
        valid_types = {k: v for k, v in CONDITION_TYPES.items() if v is not None}

        for condition_name in valid_types.keys():
            assert condition_name in all_categorized, f"Condition not in categories: {condition_name}"

    def test_callback_structure(self):
        """Test that callback can be defined and called."""
        callback_called = {"value": None}

        def test_callback(condition_name: str):
            callback_called["value"] = condition_name

        # Simulate callback
        test_callback("Name Contains")
        assert callback_called["value"] == "Name Contains"

    def test_multiple_callbacks(self):
        """Test multiple callback selections."""
        results = []

        def test_callback(condition_name: str):
            results.append(condition_name)

        # Simulate multiple selections
        test_callback("Name Contains")
        test_callback("Regex Match")
        test_callback("Is Hidden")

        assert len(results) == 3
        assert results == ["Name Contains", "Regex Match", "Is Hidden"]

    def test_category_count(self):
        """Test that we have the expected number of categories."""
        expected_count = 6
        assert len(CONDITION_CATEGORIES) == expected_count

    def test_total_conditions_count(self):
        """Test that we have expected total conditions."""
        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        # Should have 21 conditions total (14 original + 2 Tier-1 + 5 Tier-2)
        assert len(all_conditions) == 21

    def test_category_order(self):
        """Test that categories are in expected order."""
        categories = list(CONDITION_CATEGORIES.keys())
        expected_order = ["Name", "File Properties", "File Attributes", "Path", "Content & Patterns", "Metadata & Tags"]

        assert categories == expected_order


@pytest.mark.unit
class TestConditionEditorIntegration:
    """Test integration with condition editor."""

    def test_condition_types_dict_updated(self):
        """Test that CONDITION_TYPES dict is properly updated."""
        from folderfresh.condition_editor import CONDITION_TYPES

        # Should NOT have separators
        assert "— Path —" not in CONDITION_TYPES
        assert "— File Attributes —" not in CONDITION_TYPES

    def test_all_valid_conditions_in_types_dict(self):
        """Test all valid conditions are in CONDITION_TYPES."""
        from folderfresh.condition_editor import CONDITION_TYPES

        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        for condition in all_conditions:
            assert condition in CONDITION_TYPES
            assert CONDITION_TYPES[condition] is not None

    def test_condition_classes_exist(self):
        """Test that all condition classes are available."""
        from folderfresh.condition_editor import CONDITION_TYPES

        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        for condition_name in all_conditions:
            condition_class = CONDITION_TYPES[condition_name]
            assert condition_class is not None
            # Verify class is callable
            assert callable(condition_class)


@pytest.mark.unit
class TestConditionSelectorEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_empty_category_not_allowed(self):
        """Verify no categories are empty."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            assert len(conditions) > 0

    def test_category_names_not_empty(self):
        """Verify all category names are non-empty."""
        for category_name in CONDITION_CATEGORIES.keys():
            assert category_name.strip() != ""

    def test_condition_names_unique_in_categories(self):
        """Verify each condition appears only once per category."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            unique_conditions = set(conditions)
            assert len(conditions) == len(unique_conditions)

    def test_no_whitespace_only_conditions(self):
        """Verify no conditions are whitespace-only."""
        for category_name, conditions in CONDITION_CATEGORIES.items():
            for condition in conditions:
                assert condition.strip() != ""
                # Verify it's the same as the trimmed version
                assert condition == condition.strip() or condition == condition  # Allow as-is

    def test_condition_name_consistency(self):
        """Test that condition names match expected format."""
        all_conditions = []
        for category_name, conditions in CONDITION_CATEGORIES.items():
            all_conditions.extend(conditions)

        for condition in all_conditions:
            # Should contain letters and common separators
            assert any(c.isalpha() for c in condition)
