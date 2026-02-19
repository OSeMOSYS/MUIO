"""
SliceInterpreter — Phase 2: Semantic expansion of parsed GMPL structures.

Converts Phase 1 parse output (GMPLParseResult) into a normalized
long-form representation:

    {
        param_name: {
            (dim1, dim2, ..., dimN): numeric_value,
            ...
        },
        ...
    }

This module does NOT:
  - Rename sets (FUEL stays FUEL, COMMODITY stays COMMODITY)
  - Generate MUIO-specific IDs
  - Pivot to wide format
  - Write JSON files
  - Modify Phase 1 data structures
"""

from __future__ import annotations

from typing import Optional, Union
from Classes.Case.GMPLParser import GMPLParseResult, ParsedParam, SliceBlock


# ---------------------------------------------------------------------------
# Dimension Registry
# ---------------------------------------------------------------------------
# Maps parameter names to their expected dimension order.
# Source: OSeMOSYS model formulation.
#
# This is the single source of truth for dimension ordering.
# Do NOT infer dimension order from slice length.

DIMENSIONS: dict[str, list[str]] = {
    # ── Demand ──
    "AccumulatedAnnualDemand":          ["REGION", "FUEL", "YEAR"],
    "SpecifiedAnnualDemand":            ["REGION", "FUEL", "YEAR"],
    "SpecifiedDemandProfile":           ["REGION", "FUEL", "TIMESLICE", "YEAR"],

    # ── Time ──
    "YearSplit":                        ["TIMESLICE", "YEAR"],
    "Conversionls":                     ["TIMESLICE", "SEASON"],
    "Conversionld":                     ["TIMESLICE", "DAYTYPE"],
    "Conversionlh":                     ["TIMESLICE", "DAILYTIMEBRACKET"],
    "DaySplit":                         ["TIMESLICE", "YEAR"],
    "DaysInDayType":                    ["SEASON", "DAYTYPE", "YEAR"],

    # ── Technology performance ──
    "CapacityToActivityUnit":           ["REGION", "TECHNOLOGY"],
    "CapacityFactor":                   ["REGION", "TECHNOLOGY", "TIMESLICE", "YEAR"],
    "AvailabilityFactor":               ["REGION", "TECHNOLOGY", "YEAR"],
    "OperationalLife":                  ["REGION", "TECHNOLOGY"],
    "InputActivityRatio":               ["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR"],
    "OutputActivityRatio":              ["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR"],
    "ResidualCapacity":                 ["REGION", "TECHNOLOGY", "YEAR"],

    # ── Costs ──
    "CapitalCost":                      ["REGION", "TECHNOLOGY", "YEAR"],
    "FixedCost":                        ["REGION", "TECHNOLOGY", "YEAR"],
    "VariableCost":                     ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],

    # ── Capacity constraints ──
    "TotalAnnualMaxCapacity":           ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMinCapacity":           ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMaxCapacityInvestment": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMinCapacityInvestment": ["REGION", "TECHNOLOGY", "YEAR"],

    # ── Activity constraints ──
    "TotalTechnologyAnnualActivityUpperLimit": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalTechnologyAnnualActivityLowerLimit": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalTechnologyModelPeriodActivityUpperLimit": ["REGION", "TECHNOLOGY"],
    "TotalTechnologyModelPeriodActivityLowerLimit": ["REGION", "TECHNOLOGY"],

    # ── Emissions ──
    "EmissionActivityRatio":            ["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
    "EmissionsPenalty":                  ["REGION", "EMISSION", "YEAR"],
    "AnnualExogenousEmission":          ["REGION", "EMISSION", "YEAR"],
    "AnnualEmissionLimit":              ["REGION", "EMISSION", "YEAR"],
    "ModelPeriodExogenousEmission":     ["REGION", "EMISSION"],
    "ModelPeriodEmissionLimit":         ["REGION", "EMISSION"],

    # ── Reserve margin ──
    "ReserveMargin":                    ["REGION", "YEAR"],
    "ReserveMarginTagFuel":             ["REGION", "FUEL", "YEAR"],
    "ReserveMarginTagTechnology":       ["REGION", "TECHNOLOGY", "YEAR"],

    # ── Renewable energy ──
    "RETagTechnology":                  ["REGION", "TECHNOLOGY", "YEAR"],
    "RETagFuel":                        ["REGION", "FUEL", "YEAR"],
    "REMinProductionTarget":            ["REGION", "YEAR"],

    # ── Storage ──
    "TechnologyToStorage":              ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    "TechnologyFromStorage":            ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    "StorageLevelStart":                ["REGION", "STORAGE"],
    "StorageMaxChargeRate":             ["REGION", "STORAGE"],
    "StorageMaxDischargeRate":          ["REGION", "STORAGE"],
    "MinStorageCharge":                 ["REGION", "STORAGE", "YEAR"],
    "OperationalLifeStorage":           ["REGION", "STORAGE"],
    "CapitalCostStorage":               ["REGION", "STORAGE", "YEAR"],
    "ResidualStorageCapacity":          ["REGION", "STORAGE", "YEAR"],

    # ── Trade ──
    "TradeRoute":                       ["REGION", "REGION", "FUEL", "YEAR"],

    # ── Scalar / global ──
    "DiscountRate":                     ["REGION"],
    "DiscountRateStorage":              ["REGION", "STORAGE"],
    "DepreciationMethod":               ["REGION"],

    # ── Other ──
    "CapacityOfOneTechnologyUnit":      ["REGION", "TECHNOLOGY", "YEAR"],
    "ResultsPath":                      [],
}

# Also accept COMMODITY as an alias for FUEL in set lookups.
_SET_ALIASES: dict[str, str] = {
    "COMMODITY": "FUEL",
}


# ---------------------------------------------------------------------------
# Numeric conversion helper
# ---------------------------------------------------------------------------

def _to_number(s: str) -> Union[int, float]:
    """Convert a string to int or float.

    Returns int if the string represents a whole number,
    otherwise float.
    """
    try:
        f = float(s)
        if f == int(f) and "." not in s and "e" not in s.lower():
            return int(f)
        return f
    except (ValueError, OverflowError):
        return float("nan")


def _default_to_number(s: Optional[str]) -> Optional[Union[int, float]]:
    """Convert a default value string to a number, or None if not numeric."""
    if s is None:
        return None
    # Strip trailing dots (e.g., "0." → "0")
    cleaned = s.rstrip(".")
    if not cleaned:
        return 0.0
    try:
        f = float(cleaned)
        if f == int(f) and "." not in cleaned and "e" not in cleaned.lower():
            return int(f)
        return f
    except (ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# SliceInterpreter
# ---------------------------------------------------------------------------

class SliceInterpreter:
    """
    Phase 2 interpreter: expands parsed GMPL structures into normalized
    long-form tuple data.

    Usage
    -----
    >>> from Classes.Case.GMPLParser import GMPLParser
    >>> parse_result = GMPLParser.parse_file("data.txt")
    >>> interp = SliceInterpreter(parse_result)
    >>> normalized = interp.interpret()
    >>> print(normalized["CapitalCost"])
    {("UTOPIA", "E01", "1990"): 1400.0, ...}
    """

    def __init__(self, parse_result: GMPLParseResult):
        self.sets = parse_result.sets
        self.params = parse_result.params

        # Build a unified set lookup that handles FUEL/COMMODITY aliasing.
        self._set_lookup: dict[str, list[str]] = dict(self.sets)

    def interpret(self) -> dict[str, dict[tuple, Union[int, float]]]:
        """Interpret all parsed params into normalized long-form dictionaries.

        Returns
        -------
        dict mapping param_name → { tuple_key: numeric_value }
        """
        result: dict[str, dict[tuple, Union[int, float]]] = {}

        for param in self.params:
            # Skip params with no slice data (default-only).
            if not param.slices:
                continue

            # Skip non-data params (e.g., ResultsPath).
            dims = self._get_dimensions(param.name)
            if dims is None:
                continue
            if not dims:
                # Zero-dimensional (scalar) — skip for now.
                continue

            default_val = _default_to_number(param.default)
            param_data: dict[tuple, Union[int, float]] = {}

            for slice_block in param.slices:
                self._expand_slice(param.name, dims, slice_block, default_val, param_data)

            if param_data:
                result[param.name] = param_data

        return result

    def _get_dimensions(self, param_name: str) -> Optional[list[str]]:
        """Look up the dimension schema for a parameter.

        Returns None if the parameter is unknown.
        """
        if param_name in DIMENSIONS:
            return DIMENSIONS[param_name]
        return None

    def _resolve_set_name(self, dim_name: str) -> str:
        """Resolve a dimension name to its set name, handling aliases.

        For example, if the file uses COMMODITY instead of FUEL,
        the dimension 'FUEL' should look up the 'COMMODITY' set.
        """
        # Direct match.
        if dim_name in self._set_lookup:
            return dim_name

        # Check if any alias maps to this dimension.
        for alias, canonical in _SET_ALIASES.items():
            if canonical == dim_name and alias in self._set_lookup:
                return alias

        return dim_name

    def _expand_slice(
        self,
        param_name: str,
        dims: list[str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Expand one SliceBlock into tuple → value entries."""
        header = block.header
        col_labels = block.column_labels
        rows = block.rows

        if not rows:
            return

        n_dims = len(dims)

        # ── Headerless tables ──
        # These have header == [] and use bare ':' columns.
        # Dimension mapping depends on the number of dims.
        if not header:
            self._expand_headerless(param_name, dims, block, default_val, out)
            return

        # ── Headed tables ──
        # Identify which dimension positions are wildcards.
        # The header length should match n_dims (or n_dims - 1 if
        # columns provide the last dimension).
        wildcard_positions = [i for i, h in enumerate(header) if h == "*"]
        fixed_positions = {i: header[i] for i in range(len(header)) if header[i] != "*"}

        n_header = len(header)
        n_wildcards = len(wildcard_positions)

        # ── Header length > dim count ──
        # This happens when the GMPL table format uses an extra wildcard
        # for the column layout dimension that doesn't correspond to a
        # model dimension.  E.g., OperationalLife has dims [REGION, TECHNOLOGY]
        # but header [RE1,*,*] — the extra * is the column layout.
        if n_header > n_dims and n_wildcards >= 2:
            self._expand_oversized_header(
                dims, header, wildcard_positions, fixed_positions,
                block, default_val, out,
            )
            return

        if n_wildcards == 0:
            # All fixed — shouldn't have rows, skip.
            return

        if n_wildcards == 1:
            # Single wildcard — either rows or columns provide its values.
            self._expand_single_wildcard(
                dims, header, wildcard_positions[0], fixed_positions,
                block, default_val, out,
            )
            return

        if n_wildcards == 2:
            # Two wildcards — rows provide one, columns provide the other.
            self._expand_two_wildcards(
                dims, header, wildcard_positions, fixed_positions,
                block, default_val, out,
            )
            return

        # More than 2 wildcards — not expected in standard OSeMOSYS,
        # but handle gracefully by skipping.
        return

    def _expand_headerless(
        self,
        param_name: str,
        dims: list[str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Expand a headerless table (no slice notation).

        These tables use bare ':' column headers.
        The row key is one dimension, column labels are another dimension.
        """
        col_labels = block.column_labels
        n_dims = len(dims)

        if n_dims == 2:
            # Two dimensions: row key is dim[0], columns are dim[1]
            # OR: row key is dim[0], columns are dim[1]
            # Detect which by checking if row keys match a known set
            # or if column labels match a known set.
            row_dim_idx, col_dim_idx = self._detect_headerless_2d(dims, block)

            for row in block.rows:
                row_key = row.key
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue

                    tup = [None] * n_dims
                    tup[row_dim_idx] = row_key
                    tup[col_dim_idx] = col_label
                    out[tuple(tup)] = val

        elif n_dims == 1:
            # Single dimension: columns are the dimension values
            for row in block.rows:
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue
                    out[(col_label,)] = val

        else:
            # More than 2 dims in a headerless table — unusual.
            # Fall back: assume first row key fills dim[0],
            # columns fill last dim.
            for row in block.rows:
                row_key = row.key
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue

                    tup = [None] * n_dims
                    tup[0] = row_key
                    tup[-1] = col_label
                    out[tuple(tup)] = val

    def _detect_headerless_2d(
        self,
        dims: list[str],
        block: SliceBlock,
    ) -> tuple[int, int]:
        """Detect which dimension is rows vs columns in a 2D headerless table.

        Returns (row_dim_index, col_dim_index).
        """
        col_labels = block.column_labels
        row_keys = [r.key for r in block.rows]

        # Check if column labels match dim[0]'s set.
        set_name_0 = self._resolve_set_name(dims[0])
        set_members_0 = set(self._set_lookup.get(set_name_0, []))

        set_name_1 = self._resolve_set_name(dims[1])
        set_members_1 = set(self._set_lookup.get(set_name_1, []))

        # If column labels match dim[1]'s set members → rows=dim[0], cols=dim[1]
        col_match_1 = all(c in set_members_1 for c in col_labels) if col_labels else False
        col_match_0 = all(c in set_members_0 for c in col_labels) if col_labels else False

        if col_match_1 and not col_match_0:
            return (0, 1)
        if col_match_0 and not col_match_1:
            return (1, 0)

        # Fallback: rows = dim[0], columns = dim[1]
        return (0, 1)

    def _expand_oversized_header(
        self,
        dims: list[str],
        header: list[str],
        wc_positions: list[int],
        fixed: dict[int, str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Expand a slice where header has more elements than dim count.

        This happens when the GMPL table format uses wildcards for both
        the row and column layout but the parameter has fewer actual
        dimensions.

        Example: OperationalLife dims=[REGION, TECHNOLOGY]
                 header=[RE1, *, *]
                 columns=[Coal, Gas, Solar, Wind]
                 row key=RE1, values=[40, 30, 25, 25]

        Strategy:
        1. Map fixed header values to their dimensions.
        2. Identify unmapped dims.
        3. Determine whether column labels or row keys fill them.
        """
        n_dims = len(dims)
        col_labels = block.column_labels

        # Map fixed header values to dimensions.
        mapped_dims: dict[int, str] = {}  # dim_idx → value
        used_dims: set[int] = set()

        for hp, hval in enumerate(header):
            if hval == "*":
                continue
            for di in range(n_dims):
                if di in used_dims:
                    continue
                set_name = self._resolve_set_name(dims[di])
                members = self._set_lookup.get(set_name, [])
                if hval in members:
                    mapped_dims[di] = hval
                    used_dims.add(di)
                    break

        # Find unmapped dimensions.
        unmapped = [di for di in range(n_dims) if di not in used_dims]

        if len(unmapped) == 0:
            # All dims are fixed by header — just emit values.
            # This shouldn't normally happen, but handle gracefully.
            return

        if len(unmapped) == 1:
            # One unmapped dim — filled by column labels.
            # Row key is likely a duplicate of one of the fixed dims.
            target_dim = unmapped[0]
            for row in block.rows:
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue

                    tup = [None] * n_dims
                    for di, dval in mapped_dims.items():
                        tup[di] = dval
                    tup[target_dim] = col_label
                    out[tuple(tup)] = val

        elif len(unmapped) == 2:
            # Two unmapped dims — columns fill one, rows fill the other.
            # Detect which by checking set membership.
            dim_a, dim_b = unmapped

            set_a_name = self._resolve_set_name(dims[dim_a])
            set_a = set(self._set_lookup.get(set_a_name, []))
            set_b_name = self._resolve_set_name(dims[dim_b])
            set_b = set(self._set_lookup.get(set_b_name, []))

            cols_match_a = col_labels and all(c in set_a for c in col_labels)
            cols_match_b = col_labels and all(c in set_b for c in col_labels)

            if cols_match_b and not cols_match_a:
                col_dim, row_dim = dim_b, dim_a
            elif cols_match_a and not cols_match_b:
                col_dim, row_dim = dim_a, dim_b
            else:
                # Default: first unmapped = rows, second = columns
                row_dim, col_dim = dim_a, dim_b

            for row in block.rows:
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue

                    tup = [None] * n_dims
                    for di, dval in mapped_dims.items():
                        tup[di] = dval
                    tup[row_dim] = row.key
                    tup[col_dim] = col_label
                    out[tuple(tup)] = val

    def _expand_single_wildcard(
        self,
        dims: list[str],
        header: list[str],
        wc_pos: int,
        fixed: dict[int, str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Expand a slice with exactly 1 wildcard.

        Row keys fill the wildcard dimension.
        Columns don't contribute a dimension — they are the values.
        OR: column labels contribute a missing dimension.
        """
        n_dims = len(dims)
        n_header = len(header)
        col_labels = block.column_labels

        if n_header == n_dims:
            # Header covers all dimensions. Rows fill the wildcard.
            # If there are columns, they provide the values for each column.
            # But wait — if columns provide labeled data, they must be
            # an additional dimension not in the header.
            # Actually, with 1 wildcard and n_header == n_dims,
            # columns are just repeated values (no extra dimension).
            # Rows provide the wildcard dimension, each value corresponds
            # to a column label (which itself is a member of some dim).
            # But that doesn't match — let me re-think.
            #
            # Example: TechnologyToStorage [UTOPIA,*,*,2]
            #   → 2 wildcards, not 1. This case shouldn't reach here.
            #
            # Example: VariableCost [UTOPIA,*,1,*] with dims [R,T,M,Y]
            #   → 2 wildcards. Also not 1.
            #
            # Single wildcard with n_header == n_dims would mean
            # column labels are just value labels (e.g., for a
            # single-row table). Row key is the wildcard, columns
            # are labeled data points.
            for row in block.rows:
                row_key = row.key
                for ci, col_label in enumerate(col_labels):
                    if ci >= len(row.values):
                        break
                    val = _to_number(row.values[ci])
                    if default_val is not None and val == default_val:
                        continue

                    tup = list(header)
                    tup[wc_pos] = row_key
                    # col_label should map to... hmm, this needs
                    # column as another dimension. But we only have 1 wildcard.
                    # This means columns are NOT a separate dimension.
                    # They're just indexed by position for a single value.
                    # Actually — with only 1 wildcard and columns present,
                    # the column labels must represent values, not dim members.
                    # This case seems unlikely in OSeMOSYS.
                    out[tuple(tup)] = val

        elif n_header < n_dims:
            # Header covers fewer dims than expected.
            # The missing dimension is provided by column labels.
            # Row keys provide the wildcard dimension.
            #
            # This shouldn't happen in standard patterns, but let's handle it.
            missing_dim_idx = None
            header_dim_map: list[int] = []
            used = set()
            for hi, h in enumerate(header):
                if h == "*":
                    header_dim_map.append(-1)  # wildcard, to be filled
                else:
                    # Match fixed header to a dimension.
                    for di in range(n_dims):
                        if di not in used:
                            set_name = self._resolve_set_name(dims[di])
                            members = self._set_lookup.get(set_name, [])
                            if h in members or dims[di] == "REGION":
                                header_dim_map.append(di)
                                used.add(di)
                                break
                    else:
                        header_dim_map.append(-1)

            # Find the dimension not covered by header.
            covered = set(header_dim_map) - {-1}
            missing = [d for d in range(n_dims) if d not in covered]

            if missing and wc_pos < len(header_dim_map):
                # Row fills the wildcard dim, columns fill the first missing dim.
                wc_dim = header_dim_map[wc_pos] if header_dim_map[wc_pos] != -1 else missing[0]
                col_dim = missing[-1] if len(missing) > 0 else n_dims - 1

                for row in block.rows:
                    for ci, col_label in enumerate(col_labels):
                        if ci >= len(row.values):
                            break
                        val = _to_number(row.values[ci])
                        if default_val is not None and val == default_val:
                            continue

                        tup = [None] * n_dims
                        for hi, di in enumerate(header_dim_map):
                            if di >= 0 and hi != wc_pos:
                                tup[di] = header[hi]
                        tup[wc_dim] = row.key
                        tup[col_dim] = col_label
                        out[tuple(tup)] = val

    def _expand_two_wildcards(
        self,
        dims: list[str],
        header: list[str],
        wc_positions: list[int],
        fixed: dict[int, str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Expand a slice with exactly 2 wildcards.

        One wildcard is filled by row keys, the other by column labels.
        """
        n_dims = len(dims)
        n_header = len(header)

        # Map header positions to dimension indices.
        dim_map = self._map_header_to_dims(header, dims)

        if dim_map is None:
            return

        # Determine which wildcard maps to rows and which to columns.
        wc_dim_indices = [dim_map[wp] for wp in wc_positions]

        # Convention: the LAST wildcard (rightmost) in the header
        # corresponds to column labels (typically YEAR, the last indexed dim).
        # The other wildcard corresponds to row keys.
        row_wc_header_pos = wc_positions[0]
        col_wc_header_pos = wc_positions[1]
        row_dim_idx = dim_map[row_wc_header_pos]
        col_dim_idx = dim_map[col_wc_header_pos]

        for row in block.rows:
            row_key = row.key
            for ci, col_label in enumerate(block.column_labels):
                if ci >= len(row.values):
                    break
                val = _to_number(row.values[ci])
                if default_val is not None and val == default_val:
                    continue

                tup: list[Optional[str]] = [None] * n_dims
                # Fill fixed positions.
                for hp, di in enumerate(dim_map):
                    if hp not in wc_positions:
                        tup[di] = header[hp]
                # Fill wildcards.
                tup[row_dim_idx] = row_key
                tup[col_dim_idx] = col_label

                out[tuple(tup)] = val

    def _map_header_to_dims(
        self,
        header: list[str],
        dims: list[str],
    ) -> Optional[list[int]]:
        """Map each header position to a dimension index.

        Returns a list where result[header_pos] = dimension_index.
        Returns None if mapping fails.
        """
        n_dims = len(dims)
        n_header = len(header)

        if n_header != n_dims:
            # Header length doesn't match dim count — try best-effort.
            # This can happen if the file has a different OSeMOSYS version.
            return self._map_header_to_dims_fuzzy(header, dims)

        # Simple positional mapping: header[i] → dims[i].
        # Validate by checking that fixed values match their expected sets.
        dim_map = list(range(n_dims))

        for hp, (hval, di) in enumerate(zip(header, dim_map)):
            if hval == "*":
                continue
            # Check that hval belongs to the set for dims[di].
            set_name = self._resolve_set_name(dims[di])
            members = self._set_lookup.get(set_name, [])
            if members and hval not in members:
                # Value doesn't match — try fuzzy mapping.
                return self._map_header_to_dims_fuzzy(header, dims)

        return dim_map

    def _map_header_to_dims_fuzzy(
        self,
        header: list[str],
        dims: list[str],
    ) -> Optional[list[int]]:
        """Fuzzy mapping for when header doesn't positionally align with dims.

        Uses set membership to determine which dimension each header
        position corresponds to.
        """
        n_dims = len(dims)
        n_header = len(header)
        dim_map = [-1] * n_header
        used_dims: set[int] = set()

        # First pass: map fixed values.
        for hp in range(n_header):
            if header[hp] == "*":
                continue
            for di in range(n_dims):
                if di in used_dims:
                    continue
                set_name = self._resolve_set_name(dims[di])
                members = self._set_lookup.get(set_name, [])
                if header[hp] in members:
                    dim_map[hp] = di
                    used_dims.add(di)
                    break

        # Second pass: map wildcards to remaining dimensions.
        remaining = [di for di in range(n_dims) if di not in used_dims]
        wc_positions = [hp for hp in range(n_header) if header[hp] == "*"]

        if len(wc_positions) != len(remaining):
            # Can't map — dimension mismatch.
            # Fall back to positional mapping.
            if n_header == n_dims:
                return list(range(n_dims))
            return None

        for wc_hp, rem_di in zip(wc_positions, remaining):
            dim_map[wc_hp] = rem_di

        # Validate no -1 remains.
        if -1 in dim_map:
            return list(range(min(n_dims, n_header)))

        return dim_map


# ---------------------------------------------------------------------------
# CLI entry point for quick testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from Classes.Case.GMPLParser import GMPLParser

    if len(sys.argv) < 2:
        print("Usage: python SliceInterpreter.py <data_file.txt>")
        sys.exit(1)

    filepath = sys.argv[1]
    parse_result = GMPLParser.parse_file(filepath)
    interp = SliceInterpreter(parse_result)
    normalized = interp.interpret()

    print(f"Interpreted {len(normalized)} parameters with data.\n")

    for pname, data in normalized.items():
        n = len(data)
        sample = list(data.items())[:3]
        print(f"\n{pname} ({n} tuples):")
        for tup, val in sample:
            print(f"  {tup} → {val}")
        if n > 3:
            print(f"  ... ({n} total)")
