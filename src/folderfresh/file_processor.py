# file_processor.py
"""
Unified file processing with rules-first execution.

This module provides a shared interface for processing files across all execution modes:
- Watcher (auto-tidy)
- Manual Organise
- Preview/Simulation

Rules are ALWAYS executed first. If a rule matches, sorting is skipped.
If no rules match, standard sorting is performed.
"""

from typing import Dict, Any, List
from pathlib import Path

from .rule_engine import RuleExecutor
from .fileinfo import get_fileinfo
from .profile_store import ProfileStore
from .sorting import pick_smart_category, pick_category
from .naming import resolve_category
from .activity_log import log_activity


def process_file_with_rules(src, rules, config, preview=False):
    """
    PURE rule engine pass.

    Execution order:
    1. Extract fileinfo from src
    2. Run RuleExecutor against rules
    3. If a rule matched and action succeeded → return matched state
    4. If no rule matched → return not matched (caller must decide on sorting)
    5. NEVER perform category sorting here
    6. NEVER delete files

    Args:
        src: file path (str)
        rules: list of Rule objects
        config: configuration dict with safe_mode, dry_run, etc.
        preview: if True, set dry_run=True in config

    Returns:
        {
            "matched": True/False - did any rule match and execute?
            "success": True/False - did the rule action succeed?
            "rule_name": str or None - name of matched rule
            "dst": final destination path or original src
            "error": None or error message
        }
    """

    result = {
        "matched": False,
        "success": False,
        "rule_name": None,
        "dst": src,
        "error": None
    }

    # Extract fileinfo
    try:
        fileinfo = get_fileinfo(src)
    except Exception as e:
        result["error"] = f"Failed to extract file info: {e}"
        return result

    # Apply dry-run mode based on preview flag
    exec_cfg = config.copy()
    exec_cfg["dry_run"] = preview  # dry_run=True if preview, False if executing

    # Run executor
    try:
        executor = RuleExecutor()
        exec_result = executor.execute(rules, fileinfo, exec_cfg)

        # Extract required fields from executor result
        matched_rule = exec_result.get("matched_rule")
        final_dst = exec_result.get("final_dst")
        success = exec_result.get("success", True)
        handled = exec_result.get("handled", False)
        safe_mode_delete_blocks = exec_result.get("safe_mode_delete_blocks", [])

        # Update result
        result["success"] = success

        if matched_rule and handled:
            result["matched"] = True
            result["rule_name"] = matched_rule
            if final_dst:
                result["dst"] = final_dst
            else:
                # If no final_dst was set, keep original
                result["dst"] = src

        # Pass through safe mode delete blocks
        if safe_mode_delete_blocks:
            result["safe_mode_delete_blocks"] = safe_mode_delete_blocks

        return result

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        return result


def process_files_batch(
    file_paths: List[str],
    rules: List[Any],
    config: Dict[str, Any],
    *,
    preview: bool = False,
) -> List[Dict[str, Any]]:
    """
    Process multiple files with rules-first execution.

    Args:
        file_paths: List of file paths to process
        rules: List of Rule objects
        config: Configuration dict
        preview: If True, use dry-run mode

    Returns:
        List of result dictionaries (one per file)
    """
    results = []

    for file_path in file_paths:
        result = process_file_with_rules(
            file_path,
            rules,
            config,
            preview=preview
        )
        results.append(result)

    return results
