"""Read-only analytics and data-health reporting for SPPS Planner V6.

The experimental DB module owns persistence/import.  This module owns derived
operator/developer reports so read-heavy reporting can evolve independently of
record writes and schema migration.
"""
from __future__ import annotations

from pathlib import Path
from bisect import bisect_left
from typing import Any
import json


def v6_analytics(db_path: str | Path | None = None) -> dict[str, Any]:
    from suite_gui import experimental_data as data
    from suite_gui.decision_support import analytics_snapshot
    return analytics_snapshot(
        loading_rows=data.list_records("loading", db_path),
        outcome_rows=data.list_records("outcome", db_path),
        issue_rows=data.list_records("issue", db_path),
        cleavage_rows=data.list_records("cleavage", db_path),
    )


def quality_findings(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    from suite_gui import experimental_data as data
    from suite_gui.decision_support import record_quality_issues
    return record_quality_issues(
        loading_rows=data.list_records("loading", db_path),
        outcome_rows=data.list_records("outcome", db_path),
        issue_rows=data.list_records("issue", db_path),
    )


def _loading_leave_one_out_error(groups: dict[tuple[str, str], list[float]]) -> tuple[float | None, int]:
    """Exact legacy upper-median leave-one-out MAE in O(n log n), not O(n² log n).

    Removing any one duplicate value leaves the same peer multiset. The sorted
    position determines whether the peer median is index k or k+1; ties keep
    the prior deterministic median choice and measured units unchanged.
    """
    absolute_error = 0.0
    count = 0
    for values in groups.values():
        if len(values) < 2:
            continue
        ordered = sorted(values)
        median_index = (len(ordered) - 1) // 2
        for observed in values:
            removed_at = bisect_left(ordered, observed)
            peer_median = ordered[median_index + (removed_at <= median_index)]
            absolute_error += abs(observed - peer_median)
            count += 1
    return (absolute_error / count if count else None, count)


def data_health(db_path: str | Path | None = None) -> dict[str, Any]:
    """Return auditable quality/consistency metrics, never a fabricated success rate."""
    from suite_gui import experimental_data as data

    data.initialize(db_path)
    with data._connect(db_path) as con:
        def status_counts(table: str) -> dict[str, int]:
            rows = con.execute(f"SELECT status,COUNT(*) AS n FROM {table} GROUP BY status").fetchall()
            return {str(row["status"]): int(row["n"]) for row in rows}

        loading_total = int(con.execute("SELECT COUNT(*) FROM loading_records").fetchone()[0])
        cleavage_total = int(con.execute("SELECT COUNT(*) FROM cleavage_records").fetchone()[0])
        sequence_total = int(con.execute("SELECT COUNT(*) FROM synthesis_sequence_records").fetchone()[0])
        usage_total = int(con.execute("SELECT COUNT(*) FROM cleavage_usage_records").fetchone()[0])
        outcome_total = int(con.execute("SELECT COUNT(*) FROM experimental_outcomes").fetchone()[0])
        issue_total = int(con.execute("SELECT COUNT(*) FROM synthesis_issue_records").fetchone()[0])
        usage_unit_review = int(con.execute("SELECT COUNT(*) FROM cleavage_usage_records WHERE unit_review_required=1").fetchone()[0])
        usage_normalized = int(con.execute("SELECT COUNT(*) FROM cleavage_usage_records WHERE cocktail_ml_per_mmol IS NOT NULL").fetchone()[0])
        missing_keys = {
            "loading": int(con.execute("SELECT COUNT(*) FROM loading_records WHERE resin_key='' OR amino_acid_key='' ").fetchone()[0]),
            "cleavage": int(con.execute("SELECT COUNT(*) FROM cleavage_records WHERE product<>'' AND product_key='' ").fetchone()[0]),
            "sequence": int(con.execute("SELECT COUNT(*) FROM synthesis_sequence_records WHERE product_key='' OR sequence_key='' ").fetchone()[0]),
        }
        sequence_products = int(con.execute("SELECT COUNT(DISTINCT product_key) FROM synthesis_sequence_records WHERE product_key<>''").fetchone()[0])
        linked_cleavage = int(con.execute("""
            SELECT COUNT(*) FROM cleavage_records c
            WHERE c.product_key<>'' AND EXISTS (
                SELECT 1 FROM synthesis_sequence_records s WHERE s.product_key=c.product_key
            )
        """).fetchone()[0])
        repeated_loading_groups = int(con.execute("""
            SELECT COUNT(*) FROM (
                SELECT resin_key,amino_acid_key FROM loading_records
                WHERE resin_key<>'' AND amino_acid_key<>''
                GROUP BY resin_key,amino_acid_key HAVING COUNT(*)>=2
            )
        """).fetchone()[0])
        loading_rows = [dict(row) for row in con.execute("""
            SELECT resin_key,amino_acid_key,loading_rate_mmol_g FROM loading_records
            WHERE loading_rate_mmol_g IS NOT NULL AND resin_key<>'' AND amino_acid_key<>''
        """).fetchall()]
        cleavage_rows = [dict(row) for row in con.execute("""
            SELECT product_key,cleavage_eq,cleavage_time_h FROM cleavage_records
            WHERE product_key<>'' AND cleavage_eq IS NOT NULL AND cleavage_time_h IS NOT NULL
        """).fetchall()]
        explicit_edt = 0
        for row in con.execute("SELECT other_scavengers_json FROM cleavage_records").fetchall():
            try:
                parsed = json.loads(str(row[0] or "{}"))
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed = {}
            if isinstance(parsed, dict) and any(
                str(k).strip().casefold() == "edt" and data._float(v) not in (None, 0)
                for k, v in parsed.items()
            ):
                explicit_edt += 1

        groups: dict[tuple[str, str], list[float]] = {}
        for row in loading_rows:
            groups.setdefault((row["resin_key"], row["amino_acid_key"]), []).append(float(row["loading_rate_mmol_g"]))
        loading_mae, evaluated_loading = _loading_leave_one_out_error(groups)

        cgroups: dict[str, list[tuple[float, float]]] = {}
        for row in cleavage_rows:
            cgroups.setdefault(str(row["product_key"]), []).append((float(row["cleavage_eq"]), float(row["cleavage_time_h"])))
        agree = 0
        evaluated = 0
        for values in cgroups.values():
            if len(values) < 2:
                continue
            counts: dict[tuple[float, float], int] = {}
            for value in values:
                counts[value] = counts.get(value, 0) + 1
            mode = max(counts, key=counts.get)
            agree += sum(value == mode for value in values)
            evaluated += len(values)
        cleavage_agreement = (100.0 * agree / evaluated) if evaluated else None

        def lifecycle_counts(table: str) -> dict[str, int]:
            rows = con.execute(f"SELECT record_state,COUNT(*) AS n FROM {table} GROUP BY record_state").fetchall()
            return {str(row["record_state"] or "draft"): int(row["n"]) for row in rows}

        lifecycle = {
            "loading": lifecycle_counts("loading_records"),
            "cleavage": lifecycle_counts("cleavage_records"),
            "outcome": lifecycle_counts("experimental_outcomes"),
            "issue": lifecycle_counts("synthesis_issue_records"),
        }
        status = {
            "loading": status_counts("loading_records"),
            "cleavage": status_counts("cleavage_records"),
            "sequence": status_counts("synthesis_sequence_records"),
            "cleavage_usage": status_counts("cleavage_usage_records"),
            "outcome": status_counts("experimental_outcomes"),
            "issue": status_counts("synthesis_issue_records"),
        }

    # Measurements are never inferred from plans. Count independent Runs and
    # verified QC values separately; historical Parsed and AI imports remain outside
    # the supervised-lab eligibility tally.
    with data._connect(db_path) as con:
        measured = con.execute("""
            SELECT
                COUNT(*) AS all_rows,
                SUM(CASE WHEN status='verified' THEN 1 ELSE 0 END) AS verified_rows,
                SUM(CASE WHEN status='verified' AND
                    ((yield_percent BETWEEN 0 AND 100) OR (purity_percent BETWEEN 0 AND 100))
                    THEN 1 ELSE 0 END) AS verified_measured_rows,
                COUNT(DISTINCT CASE WHEN status='verified' AND
                    ((yield_percent BETWEEN 0 AND 100) OR (purity_percent BETWEEN 0 AND 100))
                    AND run_id<>'' THEN run_id END) AS independent_run_ids,
                COUNT(DISTINCT CASE WHEN status='verified' AND
                    ((yield_percent BETWEEN 0 AND 100) OR (purity_percent BETWEEN 0 AND 100))
                    AND sequence_key<>'' THEN sequence_key END) AS distinct_sequences,
                SUM(CASE WHEN status='verified' AND (yield_percent BETWEEN 0 AND 100)
                    THEN 1 ELSE 0 END) AS verified_yield,
                SUM(CASE WHEN status='verified' AND (purity_percent BETWEEN 0 AND 100)
                    THEN 1 ELSE 0 END) AS verified_purity,
                SUM(CASE WHEN run_id='' OR work_item_id='' THEN 1 ELSE 0 END) AS missing_run_context,
                SUM(CASE WHEN planner_snapshot_json IS NULL OR
                    trim(planner_snapshot_json) IN ('','{}','null') THEN 1 ELSE 0 END) AS missing_plan_snapshot,
                SUM(CASE WHEN yield_percent<0 OR yield_percent>100 OR
                    purity_percent<0 OR purity_percent>100 OR crude_g<0
                    THEN 1 ELSE 0 END) AS invalid_historical_values,
                SUM(CASE WHEN status='parsed' OR status='incomplete' THEN 1 ELSE 0 END) AS awaiting_review
            FROM experimental_outcomes
        """).fetchone()
        repeated_measurement_groups = int(con.execute("""
            SELECT COUNT(*) FROM (
                SELECT run_id, lower(stage) AS stage, yield_percent, purity_percent
                FROM experimental_outcomes
                WHERE run_id<>'' AND status='verified' AND
                    (yield_percent IS NOT NULL OR purity_percent IS NOT NULL)
                GROUP BY run_id, lower(stage), yield_percent, purity_percent
                HAVING COUNT(*)>1
            )
        """).fetchone()[0])
        verified_loading_measures = int(con.execute("""
            SELECT COUNT(*) FROM loading_records
            WHERE status='verified' AND outlier_flag=0 AND
                loading_rate_mmol_g IS NOT NULL AND loading_rate_mmol_g>=0
        """).fetchone()[0])
    def count(name: str) -> int:
        return int(measured[name] or 0)
    collection = {
        "verified_outcomes": count("verified_rows"),
        "verified_measured_outcomes": count("verified_measured_rows"),
        "independent_run_ids": count("independent_run_ids"),
        "distinct_sequences": count("distinct_sequences"),
        "verified_yield_measurements": count("verified_yield"),
        "verified_purity_measurements": count("verified_purity"),
        "verified_loading_measurements": verified_loading_measures,
        "missing_run_context": count("missing_run_context"),
        "missing_plan_snapshot": count("missing_plan_snapshot"),
        "historical_out_of_range": count("invalid_historical_values"),
        "possible_duplicate_measurement_groups": repeated_measurement_groups,
        "awaiting_review": count("awaiting_review"),
        "ai_imports_are_separate": True,
        "model_ready": None,  # No arbitrary threshold or untested claim.
    }
    collection["review_actions"] = [
        action for required, action in (
            (collection["awaiting_review"] > 0, "Review parsed/incomplete records before using them as training labels."),
            (collection["missing_run_context"] > 0, "Link outcome records to their actual Work Item and independent Run."),
            (collection["missing_plan_snapshot"] > 0, "Check missing frozen Plan/condition snapshots; never infer performed conditions."),
            (collection["historical_out_of_range"] > 0, "Review historical percentages or negative masses before model training."),
            (collection["possible_duplicate_measurement_groups"] > 0, "Review repeated Run/stage measurements; keep real replicates but prevent training leakage."),
            (collection["verified_measured_outcomes"] == 0, "Record measured yield/purity with the final result; predictions are not measurements."),
        ) if required
    ]

    quality = quality_findings(db_path)
    return {
        "data_collection_readiness": collection,
        "counts": {"loading": loading_total, "cleavage": cleavage_total, "sequence": sequence_total, "cleavage_usage": usage_total, "outcome": outcome_total, "issue": issue_total},
        "cleavage_usage_unit_review_required": usage_unit_review,
        "cleavage_usage_normalized_records": usage_normalized,
        "status_counts": status,
        "missing_canonical_keys": missing_keys,
        "sequence_products": sequence_products,
        "cleavage_records_linked_to_sequence_product": linked_cleavage,
        "repeated_loading_groups": repeated_loading_groups,
        "explicit_edt_records": explicit_edt,
        "loading_leave_one_out_mae_mmol_g": loading_mae,
        "loading_leave_one_out_evaluated": evaluated_loading,
        "cleavage_eq_time_replay_agreement_pct": cleavage_agreement,
        "cleavage_eq_time_replay_evaluated": evaluated,
        "record_state_counts": lifecycle,
        "quality_findings_count": len(quality),
        "quality_findings": quality[:100],
    }


__all__ = ["v6_analytics", "quality_findings", "data_health"]
