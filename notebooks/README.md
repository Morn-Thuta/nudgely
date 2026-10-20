# Notebooks (A: Data/ML)

Uplift model training. Put raw Lenta data in `data/raw/` (git-ignored). Only save small outputs to `data/`:

- `data/lenta_scored_test.csv`: treatment, visit, uplift, decile
- `data/uplift_summary.json`: visit rates, decile table, top-30% capture share

Remember: drop `gender`, use a 50% sample, float32.
