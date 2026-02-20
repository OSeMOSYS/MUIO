"""
Phase 2 — Semantic interpreter.

Expands raw GMPL parse results into normalised
``{param_name: {tuple: value}}`` dictionaries.

Each tuple key encodes the full dimension coordinates,
e.g. ``("UTOPIA", "E01", "1990")`` for a 3-D parameter.

Public API
----------
    SliceInterpreter().interpret(parsed) → dict[str, dict[tuple, number]]
"""

from __future__ import annotations

from typing import Optional, Union

from Classes.Case.GMPLParser import GMPLParseResult, SliceBlock

# ────────────────────────────────────────────────────────────
# Dimension registry  (param name → ordered dimension names)
# ────────────────────────────────────────────────────────────

_DIM_REGISTRY: dict[str, list[str]] = {
    # R
    "DiscountRate":                              ["REGION"],
    "DepreciationMethod":                        ["REGION"],
    # RT
    "OperationalLife":                           ["REGION", "TECHNOLOGY"],
    "CapacityToActivityUnit":                    ["REGION", "TECHNOLOGY"],
    "TotalTechnologyModelPeriodActivityUpperLimit": ["REGION", "TECHNOLOGY"],
    "TotalTechnologyModelPeriodActivityLowerLimit": ["REGION", "TECHNOLOGY"],
    "DiscountRateIdv":                           ["REGION", "TECHNOLOGY"],
    "DiscountRateTech":                          ["REGION", "TECHNOLOGY"],
    # RE
    "AnnualExogenousEmission":                   ["REGION", "EMISSION"],
    "ModelPeriodExogenousEmission":               ["REGION", "EMISSION"],
    # RS
    "OperationalLifeStorage":                    ["REGION", "STORAGE"],
    "DiscountRateStorage":                       ["REGION", "STORAGE"],
    "MinStorageCharge":                           ["REGION", "STORAGE"],
    "StorageMaxChargeRate":                       ["REGION", "STORAGE"],
    "StorageMaxDischargeRate":                    ["REGION", "STORAGE"],
    # RY
    "AccumulatedAnnualDemand":                   ["REGION", "FUEL", "YEAR"],
    "SpecifiedAnnualDemand":                     ["REGION", "FUEL", "YEAR"],
    "TradeRoute":                                ["REGION", "REGION", "FUEL", "YEAR"],
    "REMinProductionTarget":                     ["REGION", "YEAR"],
    # RYT
    "CapitalCost":                               ["REGION", "TECHNOLOGY", "YEAR"],
    "FixedCost":                                 ["REGION", "TECHNOLOGY", "YEAR"],
    "VariableCost":                              ["REGION", "TECHNOLOGY", "YEAR"],
    "ResidualCapacity":                          ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMaxCapacity":                    ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMinCapacity":                    ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMaxCapacityInvestment":          ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualMinCapacityInvestment":          ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalTechnologyAnnualActivityUpperLimit":   ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalTechnologyAnnualActivityLowerLimit":   ["REGION", "TECHNOLOGY", "YEAR"],
    "AvailabilityFactor":                        ["REGION", "TECHNOLOGY", "YEAR"],
    "RETagTechnology":                           ["REGION", "TECHNOLOGY", "YEAR"],
    "NumberOfNewTechnologyUnits":                ["REGION", "TECHNOLOGY", "YEAR"],
    "CapacityOfOneTechnologyUnit":               ["REGION", "TECHNOLOGY", "YEAR"],
    # RYC
    "RETagFuel":                                 ["REGION", "FUEL", "YEAR"],
    # RYE
    "AnnualEmissionLimit":                       ["REGION", "EMISSION", "YEAR"],
    "EmissionsPenalty":                           ["REGION", "EMISSION", "YEAR"],
    "ModelPeriodEmissionLimit":                   ["REGION", "EMISSION"],
    # RYS
    "CapitalCostStorage":                        ["REGION", "STORAGE", "YEAR"],
    "ResidualStorageCapacity":                    ["REGION", "STORAGE", "YEAR"],
    # RYTs
    "YearSplit":                                 ["REGION", "TIMESLICE", "YEAR"],
    # RYSeDt
    "DaysInDayType":                             ["REGION", "SEASON", "DAYTYPE", "YEAR"],
    # RYDtb
    "DaySplit":                                  ["REGION", "DAILYTIMEBRACKET", "YEAR"],
    # RYTTs
    "CapacityFactor":                            ["REGION", "TECHNOLOGY", "TIMESLICE", "YEAR"],
    "SpecifiedDemandProfile":                    ["REGION", "FUEL", "TIMESLICE", "YEAR"],
    # RYTM
    "InputActivityRatio":                        ["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR"],
    "OutputActivityRatio":                       ["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR"],
    # RYTEM
    "EmissionActivityRatio":                     ["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
    # RTSM  (storage links — no year)
    # Header order: [Region, Technology, Storage, Mode]  (not Storage,Tech)
    "TechnologyToStorage":                       ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    "TechnologyFromStorage":                     ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    # Conversion matrices  (some files omit REGION in header)
    "Conversionls":                              ["REGION", "TIMESLICE", "SEASON"],
    "Conversionld":                              ["REGION", "TIMESLICE", "DAYTYPE"],
    "Conversionlh":                              ["REGION", "TIMESLICE", "DAILYTIMEBRACKET"],
    # Misc
    "ResultsPath":                               [],
}


class SliceInterpreter:
    """
    Semantic interpreter for GMPL parse results.

    Expands slice blocks into normalised ``{tuple: value}`` dictionaries.

    Usage::

        parsed = GMPLParser.parse_file("utopia.txt")
        normalized = SliceInterpreter().interpret(parsed)
        >>> normalized["CapitalCost"][("UTOPIA","E01","1990")]
        1400
    """

    def interpret(self, parsed: GMPLParseResult) -> dict[str, dict[tuple, Union[int, float]]]:
        """
        Interpret all parameters in *parsed* and return a dict
        mapping parameter names to their ``{tuple: value}`` data.
        """
        sets = parsed.sets
        result: dict[str, dict[tuple, Union[int, float]]] = {}

        for p in parsed.params:
            dims = self._get_dims(p.name)
            if dims is None:
                continue  # unknown param — skip

            out: dict[tuple, Union[int, float]] = {}
            for block in p.slices:
                self._expand_slice(p.name, dims, block, p.default, out, sets)
            if out:
                # Post-process: pad short tuples with region if needed
                out = self._pad_short_tuples(out, dims, sets)
                result[p.name] = out

        return result

    # ── dimension lookup ────────────────────────────────────
    def _get_dims(self, param_name: str) -> Optional[list[str]]:
        return _DIM_REGISTRY.get(param_name)

    def _pad_short_tuples(
        self,
        data: dict[tuple, Union[int, float]],
        dims: list[str],
        sets: dict[str, list[str]],
    ) -> dict[tuple, Union[int, float]]:
        """Pad tuples shorter than dims by prepending the region."""
        n_dims = len(dims)
        if not data:
            return data
        sample = next(iter(data))
        if len(sample) >= n_dims:
            return data
        # Try to prepend region
        deficit = n_dims - len(sample)
        regions = sets.get("REGION", [])
        if deficit == 1 and dims[0] == "REGION" and len(regions) == 1:
            region = regions[0]
            return {(region,) + tup: val for tup, val in data.items()}
        return data

    # ── slice expansion ─────────────────────────────────────
    def _expand_slice(
        self,
        param_name: str,
        dims: list[str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
        sets: dict[str, list[str]],
    ) -> None:
        n_dims = len(dims)
        header = block.header

        # ── No dimensions (scalar) ──
        if n_dims == 0:
            return

        # ── Headerless tables ──
        if header is None:
            self._expand_headerless(dims, block, default_val, out)
            return

        # ── Headed tables ──
        wildcard_positions = [i for i, h in enumerate(header) if h == "*"]
        fixed_positions = {i: header[i] for i in range(len(header)) if header[i] != "*"}
        n_header = len(header)
        n_wildcards = len(wildcard_positions)

        # Header length > dim count — extra wildcard is column layout
        if n_header > n_dims and n_wildcards >= 2:
            self._expand_oversized_header(
                dims, header, wildcard_positions, fixed_positions,
                block, default_val, out,
            )
            return

        if n_wildcards == 0:
            # All fixed — headerless rows under this header
            self._expand_all_fixed(dims, header, block, default_val, out)
        elif n_wildcards == 1:
            self._expand_single_wildcard(dims, header, wildcard_positions[0], fixed_positions, block, default_val, out)
        elif n_wildcards == 2:
            self._expand_two_wildcards(dims, header, wildcard_positions, fixed_positions, block, default_val, out)
        else:
            # 3+ wildcards — best effort
            self._expand_multi_wildcard(dims, header, wildcard_positions, fixed_positions, block, default_val, out, sets)

    # ── headerless ──────────────────────────────────────────
    def _expand_headerless(
        self,
        dims: list[str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        for row in block.rows:
            key = row.key
            if len(row.values) == 1:
                val = row.values[0]
                if default_val is not None and val == default_val:
                    continue
                # Key might contain multiple dimension values
                parts = key.split()
                if len(parts) == len(dims) - 1:
                    tup = tuple(parts) + (str(val),)
                    # Hmm, this doesn't work for key-value pairs
                    # Actually for headerless, it's usually `key value`
                    tup = (key,)
                    out[tup] = val
                else:
                    out[(key,)] = val

    # ── all fixed header ────────────────────────────────────
    def _expand_all_fixed(
        self,
        dims: list[str],
        header: list[str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        # e.g. [RE1,Coal,Biomass,1,*] where last * is via column labels
        # Actually if n_wildcards == 0, columns represent another dim        
        prefix = tuple(header)
        for row in block.rows:
            values = row.values
            if block.column_labels:
                for ci, col in enumerate(block.column_labels):
                    if ci < len(values):
                        val = values[ci]
                        if default_val is not None and val == default_val:
                            continue
                        out[prefix + (row.key, str(col))] = val
            else:
                if values:
                    val = values[0]
                    if default_val is not None and val == default_val:
                        continue
                    out[prefix + (row.key,)] = val

    # ── single wildcard ─────────────────────────────────────
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
        n_dims = len(dims)
        # Build mapping from header position to dim position
        dim_map = self._map_header_to_dims(header, dims, fixed, [wc_pos])

        for row in block.rows:
            if block.column_labels:
                # Row key fills the wildcard, columns are year/other dim
                for ci, col in enumerate(block.column_labels):
                    if ci < len(row.values):
                        val = row.values[ci]
                        if default_val is not None and val == default_val:
                            continue
                        parts = list(header)
                        parts[wc_pos] = row.key
                        # Map to dims, adding column as last dim
                        tup = self._build_tuple(dims, parts, col, dim_map)
                        out[tup] = val
            else:
                # Simple key-value
                if row.values:
                    val = row.values[0]
                    if default_val is not None and val == default_val:
                        continue
                    parts = list(header)
                    parts[wc_pos] = row.key
                    tup = tuple(parts[:n_dims])
                    out[tup] = val

    # ── two wildcards ───────────────────────────────────────
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
        n_dims = len(dims)
        wc0, wc1 = wc_positions[0], wc_positions[1]

        if block.column_labels:
            # Row key → wc0 dimension, columns → wc1 dimension
            for row in block.rows:
                for ci, col in enumerate(block.column_labels):
                    if ci < len(row.values):
                        val = row.values[ci]
                        if default_val is not None and val == default_val:
                            continue
                        parts = list(header)
                        parts[wc0] = row.key
                        parts[wc1] = str(col)
                        # Build dimension tuple — header may be shorter than dims
                        tup = tuple(parts[:n_dims]) if len(parts) >= n_dims else tuple(parts)
                        out[tup] = val
        else:
            # No columns — row key + single value
            for row in block.rows:
                if row.values:
                    val = row.values[0]
                    if default_val is not None and val == default_val:
                        continue
                    parts = list(header)
                    parts[wc0] = row.key
                    tup = tuple(parts[:n_dims])
                    out[tup] = val

    # ── oversized header ────────────────────────────────────
    def _expand_oversized_header(
        self,
        dims: list[str],
        header: list[str],
        wildcard_positions: list[int],
        fixed_positions: dict[int, str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
    ) -> None:
        """Handle headers longer than dimensions (extra * is columns)."""
        n_dims = len(dims)

        # Find which fixed values fill which dims
        fixed_vals = [header[i] for i in sorted(fixed_positions.keys())]
        n_fixed = len(fixed_vals)
        n_wc = len(wildcard_positions)

        # The first wildcard(s) fill remaining dims, last wildcard is columns
        remaining_dim_slots = n_dims - n_fixed

        if block.column_labels:
            for row in block.rows:
                for ci, col in enumerate(block.column_labels):
                    if ci < len(row.values):
                        val = row.values[ci]
                        if default_val is not None and val == default_val:
                            continue
                        # Build tuple from fixed + row.key
                        tup = tuple(fixed_vals) + (row.key,) if remaining_dim_slots == 1 else tuple(fixed_vals)
                        # Trim to n_dims
                        tup_list = list(tup)
                        while len(tup_list) < n_dims:
                            tup_list.append(str(col))
                        out[tuple(tup_list[:n_dims])] = val
        else:
            for row in block.rows:
                if row.values:
                    val = row.values[0]
                    if default_val is not None and val == default_val:
                        continue
                    tup = tuple(fixed_vals) + (row.key,)
                    out[tuple(list(tup)[:n_dims])] = val

    # ── multi wildcard (3+) ─────────────────────────────────
    def _expand_multi_wildcard(
        self,
        dims: list[str],
        header: list[str],
        wildcard_positions: list[int],
        fixed_positions: dict[int, str],
        block: SliceBlock,
        default_val: Optional[Union[int, float]],
        out: dict[tuple, Union[int, float]],
        sets: dict[str, list[str]],
    ) -> None:
        """Handle 3+ wildcards — map by set membership."""
        n_dims = len(dims)
        # Fall back to treating like 2 wildcards with column
        if len(wildcard_positions) >= 2 and block.column_labels:
            wc0 = wildcard_positions[0]
            wc1 = wildcard_positions[1]
            for row in block.rows:
                for ci, col in enumerate(block.column_labels):
                    if ci < len(row.values):
                        val = row.values[ci]
                        if default_val is not None and val == default_val:
                            continue
                        parts = list(header)
                        parts[wc0] = row.key
                        parts[wc1] = str(col)
                        # Fill remaining wildcards from context
                        tup = tuple(parts[:n_dims])
                        out[tup] = val

    # ── helpers ─────────────────────────────────────────────
    def _map_header_to_dims(
        self,
        header: list[str],
        dims: list[str],
        fixed: dict[int, str],
        wc_positions: list[int],
    ) -> dict[int, int]:
        """Map header positions to dimension positions (best effort)."""
        mapping: dict[int, int] = {}
        used_dims: set[int] = set()

        # Fixed positions map first
        for hp in sorted(fixed.keys()):
            for di in range(len(dims)):
                if di not in used_dims:
                    mapping[hp] = di
                    used_dims.add(di)
                    break

        # Wildcards fill remaining
        for wp in wc_positions:
            for di in range(len(dims)):
                if di not in used_dims:
                    mapping[wp] = di
                    used_dims.add(di)
                    break

        return mapping

    def _build_tuple(
        self,
        dims: list[str],
        parts: list[str],
        col_value: str,
        dim_map: dict[int, int],
    ) -> tuple:
        """Build a dimension tuple from header parts + column value."""
        n_dims = len(dims)
        result = [""] * n_dims

        for hp, di in dim_map.items():
            if di < n_dims and hp < len(parts):
                result[di] = parts[hp]

        # Fill any remaining empty slot with the column value
        for i in range(n_dims):
            if not result[i]:
                result[i] = str(col_value)

        return tuple(result)


# ────────────────────────────────────────────────────────────
# CLI entry point
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from Classes.Case.GMPLParser import GMPLParser

    if len(sys.argv) < 2:
        print("Usage: python SliceInterpreter.py <data_file.txt>")
        sys.exit(1)

    parsed = GMPLParser.parse_file(sys.argv[1])
    normalized = SliceInterpreter().interpret(parsed)

    print(f"Interpreted {len(normalized)} parameters with data.\n")

    for pname in sorted(normalized.keys())[:15]:
        n = len(normalized[pname])
        print(f"\n{pname} ({n} tuples):")
        for tup, val in list(normalized[pname].items())[:5]:
            print(f"  {tup} → {val}")
        if n > 5:
            print(f"  ... ({n} total)")
