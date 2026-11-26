"""Data-only, bounded RandomForest inference for SPPS Planner V9 Excel AI.

A trained sklearn Pipeline is exported as plain JSON *data*, not a pickle/joblib
object. Reading this file does not import or invoke model code. The architecture
is deliberately narrow: numeric median imputation, categorical constant
imputation + one-hot encoding, then sklearn RandomForestRegressor.

This is NOT a portable generic sklearn converter. Model output is advisory only.
"""
from __future__ import annotations

import math
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any
import json

FORMAT = 'spps-v9-safe-forest-v1'
MAX_TREES = 250
MAX_TREE_NODES = 30_000
MAX_CATEGORIES = 2_000
MAX_MODEL_FEATURES = 5_000


def export_forest(pipeline, numeric: tuple[str, ...], categorical: tuple[str, ...]) -> dict[str, Any]:
    prep = pipeline.named_steps['prep']
    forest = pipeline.named_steps['model']
    num_imp = prep.named_transformers_['num']
    cat_pipe = prep.named_transformers_['cat']
    cat_imp = cat_pipe.named_steps['impute']
    encoder = cat_pipe.named_steps['ohe']
    if len(num_imp.statistics_) != len(numeric) or len(encoder.categories_) != len(categorical):
        raise ValueError('Unsupported fitted transformation layout.')
    if len(cat_imp.statistics_) != len(categorical):
        raise ValueError('Unsupported category imputation layout.')
    trees = []
    for estimator in forest.estimators_:
        tree = estimator.tree_
        if tree.n_outputs != 1 or tree.n_classes[0] != 1:
            raise ValueError('Only single-output regression forests are supported.')
        trees.append({
            'left': [int(x) for x in tree.children_left],
            'right': [int(x) for x in tree.children_right],
            'feature': [int(x) for x in tree.feature],
            'threshold': [float(x) for x in tree.threshold],
            'value': [float(x) for x in tree.value[:, 0, 0]],
        })
    model = {
        'format': FORMAT,
        'numeric': list(numeric),
        'categorical': list(categorical),
        'numeric_medians': [float(v) for v in num_imp.statistics_],
        'category_fill': [str(v) for v in cat_imp.statistics_],
        'categories': [[str(c) for c in cats] for cats in encoder.categories_],
        'trees': trees,
    }
    validate_forest(model)
    return model


def validate_forest(model: Any) -> None:
    if not isinstance(model, dict) or model.get('format') != FORMAT:
        raise ValueError('Unsafe or unsupported AI model format. Retrain locally.')
    nums, cats = model.get('numeric'), model.get('categorical')
    medians, fills, categories = model.get('numeric_medians'), model.get('category_fill'), model.get('categories')
    trees = model.get('trees')
    if not (isinstance(nums, list) and isinstance(cats, list) and isinstance(medians, list)
            and isinstance(fills, list) and isinstance(categories, list) and isinstance(trees, list)
            and len(nums) == len(medians) and len(cats) == len(fills) == len(categories)
            and 1 <= len(trees) <= MAX_TREES):
        raise ValueError('Corrupt AI feature layout.')
    if not all(isinstance(n, str) and len(n) <= 100 for n in nums + cats):
        raise ValueError('Corrupt feature names.')
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in medians):
        raise ValueError('Corrupt numeric imputers.')
    if not all(isinstance(c, str) and len(c) <= 120 for c in fills):
        raise ValueError('Corrupt category imputers.')
    if any(not isinstance(items, list) or not 1 <= len(items) <= MAX_CATEGORIES
           or any(not isinstance(c, str) or len(c) > 120 for c in items)
           for items in categories):
        raise ValueError('Corrupt category encoders.')
    n_features = len(nums) + sum(len(x) for x in categories)
    if n_features > MAX_MODEL_FEATURES:
        raise ValueError('AI model feature count exceeds safety limit.')
    for tree in trees:
        if not isinstance(tree, dict):
            raise ValueError('Corrupt forest tree.')
        left, right, features, thresholds, values = (tree.get(k) for k in ('left', 'right', 'feature', 'threshold', 'value'))
        if not all(isinstance(a, list) for a in (left, right, features, thresholds, values)):
            raise ValueError('Corrupt forest arrays.')
        n = len(left)
        if not 1 <= n <= MAX_TREE_NODES or any(len(a) != n for a in (right, features, thresholds, values)):
            raise ValueError('Corrupt forest tree length.')
        for i in range(n):
            if not all(isinstance(v, int) and not isinstance(v, bool) for v in (left[i], right[i], features[i])):
                raise ValueError('Corrupt forest node indices.')
            if not (isinstance(thresholds[i], (int, float)) and math.isfinite(thresholds[i])
                    and isinstance(values[i], (int, float)) and math.isfinite(values[i])):
                raise ValueError('Corrupt forest node values.')
            if left[i] == right[i] == -1 and features[i] == -2:
                continue
            # The exported trees always have children with higher indices.
            if not (i < left[i] < n and i < right[i] < n and 0 <= features[i] < n_features):
                raise ValueError('Corrupt forest topology.')


def predict_forest(model: dict[str, Any], record: dict[str, Any], *, validated: bool = False) -> float:
    if not validated:
        validate_forest(model)
    x = []
    for name, median in zip(model['numeric'], model['numeric_medians']):
        value = record.get(name)
        if value is None or value == '':
            x.append(float(median))
        else:
            try: v = float(value)
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError('Invalid AI numeric input.') from exc
            x.append(v if math.isfinite(v) else float(median))
    for name, fill, classes in zip(model['categorical'], model['category_fill'], model['categories']):
        raw = record.get(name)
        key = fill if raw is None else str(raw)
        x.extend(1.0 if key == category else 0.0 for category in classes)
    results = []
    for tree in model['trees']:
        node = 0
        left, right, feature, threshold = (tree[k] for k in ('left', 'right', 'feature', 'threshold'))
        for _ in range(len(left)):
            if left[node] == -1:
                results.append(tree['value'][node])
                break
            node = left[node] if x[feature[node]] <= threshold[node] else right[node]
        else:
            raise ValueError('Invalid model node traversal.')
    return sum(results) / len(results)


# Re-reading the bytes and checking SHA-256 detects modification even when size
# and mtime are unchanged. Cache only the decoded *validated* structure.
_MODEL_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_CACHE_LOCK = Lock()

def load_verified_forest(path: str | Path, expected_sha256: str) -> dict[str, Any]:
    """Load data-only forest with integrity checking and a 2-entry decode cache.

    No pickle/joblib deserialization. Never trust mtime alone for a security check.
    """
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 80 * 1024 * 1024:
        raise ValueError('Untrusted or oversized AI model file.')
    blob = p.read_bytes()
    digest = sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise ValueError('AI model checksum mismatch.')
    with _MODEL_CACHE_LOCK:
        cached = _MODEL_CACHE.get(digest)
    if cached is not None:
        return cached
    model = json.loads(blob.decode('utf-8'))
    validate_forest(model)
    with _MODEL_CACHE_LOCK:
        # Bounded memory: at most two recently validated models.
        if digest not in _MODEL_CACHE:
            if len(_MODEL_CACHE) >= 2:
                _MODEL_CACHE.pop(next(iter(_MODEL_CACHE)))
            _MODEL_CACHE[digest] = model
        return _MODEL_CACHE[digest]
