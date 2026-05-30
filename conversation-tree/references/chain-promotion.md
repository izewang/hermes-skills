# Chain Promotion Algorithm

## Problem

When sessions form a chain where each was branched and then continued:

root (12msgs) → sessionA (39msgs→158msgs) → sessionB (137msgs)

sessionA is BOTH a promoted child of root AND a parent with promoted children (sessionB). Simple one-pass breaks because sessionA gets skipped.

## Solution: Two-pass approach

### Pass 1: Top-level promotions

Sessions in `prom_pars` but NOT `prom_cids` — top-level parents with promoted children.

For each:
1. Create virtual branch-point node
2. Insert virtual under grandparent (or as root if no grandparent)
3. Add the original session as "continuation" child of virtual
4. Add promoted children under virtual

### Pass 2: Chained promotions

Sessions in `prom_cids & prom_pars` (both).

For each:
1. Create virtual node UNDER the session (as child)
2. Add promoted children under virtual

### Key distinction

- Pass 1: virtual node REPLACES the session in the tree
- Pass 2: virtual node is CHILD of the session

## Detection Query

```sql
-- Post-branch messages > 0 → promoted
SELECT COUNT(*) FROM messages
WHERE session_id='<parent_id>' AND timestamp > <child_started>;

-- Count at branch point
SELECT COUNT(*) FROM messages
WHERE session_id='<parent_id>' AND timestamp <= <child_started>;
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| `prom_cids` only | Skipped pass 1; handled by parent's virtual |
| `prom_pars` only | Handled in pass 1 with replacement |
| Both (`chain`) | Skipped pass 1; virtual as child in pass 2 |
| Virtual root | Needs special `📄 ⚪  N` styling (not resumable, shows branch count) |
| Session resumed | end_reason cleared; msg_count grows; can trigger promotion |
