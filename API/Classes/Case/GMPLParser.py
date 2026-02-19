"""
GMPLParser — Phase 1: Pure GMPL syntax extraction.

Parses a GMPL data file (.txt / .dat) and extracts its structural
representation WITHOUT applying any semantic interpretation or
transformation.  No renaming, no pivoting, no ID generation.

Output data structures
----------------------
parsed_sets : dict[str, list[str]]
    { "TECHNOLOGY": ["E01", "E21", ...], "FUEL": ["DSL", "ELC", ...], ... }

parsed_params : list[ParsedParam]
    Each ParsedParam is a dataclass with:
        name           : str            – parameter name
        default        : str | None     – raw default value string
        slices         : list[SliceBlock]
    Each SliceBlock is a dataclass with:
        header         : list[str]      – raw slice header tokens, e.g. ["RE1","*","*"]
        column_labels  : list[str]      – column header tokens, e.g. ["2020","2025","2030"]
        rows           : list[RowEntry]
    Each RowEntry is a dataclass with:
        key            : str            – row label (left-most token)
        values         : list[str]      – raw value strings
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RowEntry:
    """A single data row inside a slice block."""
    key: str
    values: list[str]

    def __repr__(self) -> str:
        vals = ", ".join(self.values[:5])
        suffix = ", ..." if len(self.values) > 5 else ""
        return f"RowEntry(key={self.key!r}, values=[{vals}{suffix}])"


@dataclass
class SliceBlock:
    """One sub-block within a parameter, identified by its slice header."""
    header: list[str]
    column_labels: list[str] = field(default_factory=list)
    rows: list[RowEntry] = field(default_factory=list)

    def __repr__(self) -> str:
        hdr = ",".join(self.header) if self.header else "<no-header>"
        cols = ", ".join(self.column_labels[:5])
        col_suffix = ", ..." if len(self.column_labels) > 5 else ""
        return (
            f"SliceBlock(header=[{hdr}], "
            f"columns=[{cols}{col_suffix}], "
            f"rows({len(self.rows)})={self.rows!r})"
        )


@dataclass
class ParsedParam:
    """A single `param` block with its default value and slice data."""
    name: str
    default: Optional[str] = None
    slices: list[SliceBlock] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ParsedParam(name={self.name!r}, "
            f"default={self.default!r}, "
            f"slices({len(self.slices)})={self.slices!r})"
        )


@dataclass
class GMPLParseResult:
    """Complete parse result for one GMPL data file."""
    sets: dict[str, list[str]] = field(default_factory=dict)
    params: list[ParsedParam] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Sets ({len(self.sets)}):"]
        for name, members in self.sets.items():
            lines.append(f"  {name}: {members}")
        lines.append(f"\nParams ({len(self.params)}):")
        for p in self.params:
            n_rows = sum(len(s.rows) for s in p.slices)
            lines.append(
                f"  {p.name} (default={p.default}, "
                f"slices={len(p.slices)}, total_rows={n_rows})"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tokeniser helpers
# ---------------------------------------------------------------------------

def _strip_comment(line: str) -> str:
    """Remove inline comments.  '#' inside strings is not handled (N/A here)."""
    idx = line.find("#")
    if idx >= 0:
        return line[:idx]
    return line


def _clean(line: str) -> str:
    """Strip comments, replace tabs with spaces, strip outer whitespace."""
    return _strip_comment(line).replace("\t", " ").strip()


def _split_tokens(text: str) -> list[str]:
    """Split on whitespace, discarding empty strings.

    Also splits glued tokens like ``999:=`` into ``['999', ':=']``
    and ``0.`` into ``['0']`` (trailing dot on numbers).
    """
    raw = text.split()
    result: list[str] = []
    for tok in raw:
        # Split glued ':=' — e.g., '999:=' → '999', ':='
        if tok.endswith(":=") and len(tok) > 2:
            result.append(tok[:-2])
            result.append(":=")
        # Split glued ':=' in the middle — e.g., 'default:='
        elif ":=" in tok and not tok.startswith(":="):
            parts = tok.split(":=", 1)
            if parts[0]:
                result.append(parts[0])
            result.append(":=")
            if parts[1]:
                result.append(parts[1])
        else:
            result.append(tok)
    return result


def _join_lines(lines: list[str]) -> str:
    """Collapse a list of raw lines into one continuous string,
    stripping comments and normalising whitespace."""
    parts: list[str] = []
    for raw in lines:
        cleaned = _clean(raw)
        if cleaned:
            parts.append(cleaned)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class GMPLParser:
    """
    Phase 1 parser: pure syntax extraction from a GMPL data file.

    Usage
    -----
    >>> result = GMPLParser.parse_file("path/to/data.txt")
    >>> print(result.summary())
    """

    @staticmethod
    def parse_file(filepath: str | Path) -> GMPLParseResult:
        """Parse a GMPL data file and return structured representation."""
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8-sig") as f:
            raw_lines = f.readlines()
        return GMPLParser._parse_lines(raw_lines)

    @staticmethod
    def parse_string(text: str) -> GMPLParseResult:
        """Parse GMPL content from a string."""
        return GMPLParser._parse_lines(text.splitlines(keepends=True))

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_lines(raw_lines: list[str]) -> GMPLParseResult:
        result = GMPLParseResult()

        # Flatten into a single token stream terminated by semicolons.
        # We process statement-by-statement where each statement ends
        # at ';'.
        statements = GMPLParser._split_into_statements(raw_lines)

        for stmt in statements:
            tokens = _split_tokens(stmt)
            if not tokens:
                continue

            keyword = tokens[0].lower()

            if keyword == "set":
                GMPLParser._handle_set(tokens, result)
            elif keyword == "param":
                GMPLParser._handle_param(tokens, stmt, result)
            elif keyword == "end":
                break  # end; — stop processing
            # Ignore everything else (e.g. bare comments, decorative lines)

        return result

    @staticmethod
    def _split_into_statements(raw_lines: list[str]) -> list[str]:
        """Split the file into statements delimited by ';'.

        Comments and blank lines are stripped.  The ';' itself is NOT
        included in the returned statement text.
        """
        statements: list[str] = []
        buf: list[str] = []

        for raw in raw_lines:
            cleaned = _clean(raw)
            if not cleaned:
                continue

            # Check for 'end;' as a special terminator.
            if cleaned.lower().rstrip("; ") == "end":
                # Flush anything in buffer, then add sentinel.
                if buf:
                    statements.append(" ".join(buf))
                    buf.clear()
                statements.append("end")
                break

            # A line may contain one or more ';' (e.g. inline terminators).
            while ";" in cleaned:
                idx = cleaned.index(";")
                before = cleaned[:idx].strip()
                if before:
                    buf.append(before)
                # Flush buffer as one complete statement.
                statements.append(" ".join(buf))
                buf.clear()
                cleaned = cleaned[idx + 1:].strip()

            if cleaned:
                buf.append(cleaned)

        # Anything left in buffer (no trailing ';') — flush as-is.
        if buf:
            statements.append(" ".join(buf))

        return statements

    # ------------------------------------------------------------------
    # set handler
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_set(tokens: list[str], result: GMPLParseResult) -> None:
        """Parse  set NAME := member1 member2 ... """
        # tokens: ['set', 'NAME', ':=', 'A', 'B', ...]
        # or:     ['set', 'NAME', ':=']  (empty set)
        if len(tokens) < 2:
            return

        name = tokens[1]
        # Find ':=' to locate start of members.
        members: list[str] = []
        assign_found = False
        for i, tok in enumerate(tokens):
            if tok == ":=":
                assign_found = True
                members = tokens[i + 1:]
                break
            # Handle ':=' split across tokens (e.g. ':' and '=')
            if tok == ":" and i + 1 < len(tokens) and tokens[i + 1] == "=":
                assign_found = True
                members = tokens[i + 2:]
                break

        if not assign_found:
            # No ':=' — members are everything after the name
            members = tokens[2:]

        result.sets[name] = members

    # ------------------------------------------------------------------
    # param handler
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_param(tokens: list[str], raw_stmt: str, result: GMPLParseResult) -> None:
        """Parse a full param statement.

        This handles:
        - param Name default Val :=          (empty body)
        - param Name default Val := [data]   (body with data)
        - param Name := value                (scalar assignment like ResultsPath)
        """
        if len(tokens) < 2:
            return

        name = tokens[1]
        default_val: Optional[str] = None

        # Locate 'default' keyword and ':=' separator.
        # Also handle params with no 'default' that use bare ':' as
        # column header start (e.g., 'param YearSplit : 1990 ... :=')
        assign_idx: Optional[int] = None
        bare_colon_idx: Optional[int] = None  # Position of bare ':' (not ':=')
        i = 2
        while i < len(tokens):
            tok_lower = tokens[i].lower()
            if tok_lower == "default":
                if i + 1 < len(tokens) and tokens[i + 1] != ":=":
                    default_val = tokens[i + 1]
                    i += 2
                    continue
                else:
                    i += 1
                    continue

            if tokens[i] == ":=":
                assign_idx = i
                break

            # Handle ':' '=' as separate tokens
            if tokens[i] == ":" and i + 1 < len(tokens) and tokens[i + 1] == "=":
                assign_idx = i
                break

            # Track bare ':' (not ':=') — used in headerless tables
            if tokens[i] == ":" and bare_colon_idx is None:
                bare_colon_idx = i

            i += 1

        if assign_idx is None:
            # No ':=' found — malformed, skip
            result.params.append(ParsedParam(name=name, default=default_val))
            return

        # Everything after ':=' is the body.
        body_tokens = tokens[assign_idx + 1:]

        # Handle ':' '=' as two tokens.
        if tokens[assign_idx] == ":":
            body_tokens = tokens[assign_idx + 2:]

        param = ParsedParam(name=name, default=default_val)

        # If we found a bare ':' before ':=' and there's no slice header,
        # the tokens between ':' and ':=' are column labels for a
        # headerless table (e.g., 'param YearSplit : 1990 ... 2010 :=')
        if bare_colon_idx is not None and bare_colon_idx < assign_idx:
            # Column labels are tokens between bare_colon_idx+1 and assign_idx.
            col_labels = tokens[bare_colon_idx + 1 : assign_idx]
            # Filter out any stray '=' from split ':' '='
            col_labels = [c for c in col_labels if c not in ("=", ":")]
            if col_labels:
                implicit_slice = SliceBlock(
                    header=[],
                    column_labels=col_labels,
                )
                param.slices.append(implicit_slice)
                # Body tokens are data rows.
                if body_tokens:
                    GMPLParser._parse_data_rows(body_tokens, implicit_slice)
                result.params.append(param)
                return

        if not body_tokens:
            # Empty body: param X default Y :=
            result.params.append(param)
            return

        # Check for scalar assignment (e.g., param ResultsPath := "results")
        # A scalar has no slice headers and no tabular data.
        if len(body_tokens) == 1 and not body_tokens[0].startswith("["):
            # Single scalar value.
            scalar_block = SliceBlock(header=[], column_labels=[], rows=[
                RowEntry(key=name, values=[body_tokens[0]])
            ])
            param.slices.append(scalar_block)
            result.params.append(param)
            return

        # Parse tabular body.
        GMPLParser._parse_param_body(body_tokens, param)
        result.params.append(param)

    @staticmethod
    def _parse_param_body(body_tokens: list[str], param: ParsedParam) -> None:
        """Parse the body of a param statement into SliceBlocks.

        The body_tokens have already had ';' removed (statement splitting).
        """
        # Strategy: walk through tokens.  We recognise:
        #   [X,Y,...] or [X,Y,...]:  → start of a new slice header
        #   Tokens containing ':=' or ':' then '=' → column header separator
        #   Otherwise → data rows

        current_slice: Optional[SliceBlock] = None
        columns_pending = False  # True when we've started a slice but haven't read columns yet
        i = 0

        while i < len(body_tokens):
            tok = body_tokens[i]

            # ---- Detect slice header: [X,Y,...] or [X,Y,...]: ----
            if tok.startswith("["):
                # A new slice block begins.
                header_str = tok
                # Accumulate tokens until we close the bracket.
                while "]" not in header_str and i + 1 < len(body_tokens):
                    i += 1
                    header_str += " " + body_tokens[i]

                # Clean: remove brackets, trailing ':', split on ','
                header_str = header_str.strip("[] :")
                header_parts = [h.strip() for h in header_str.split(",")]

                current_slice = SliceBlock(header=header_parts)
                param.slices.append(current_slice)
                columns_pending = True
                i += 1
                continue

            # ---- Detect column headers (contains ':=') ----
            # Column header line pattern: val1 val2 ... := or : val1 ... :=
            if columns_pending and current_slice is not None:
                # Scan forward to find ':=' on this logical line.
                col_tokens: list[str] = []
                found_assign = False
                j = i
                while j < len(body_tokens):
                    t = body_tokens[j]
                    if t == ":=":
                        found_assign = True
                        j += 1
                        break
                    # Handle combined token ending with ':='
                    if t.endswith(":="):
                        col_tokens.append(t[:-2])
                        found_assign = True
                        j += 1
                        break
                    # Skip bare ':'
                    if t == ":":
                        j += 1
                        continue
                    col_tokens.append(t)
                    j += 1

                if found_assign:
                    current_slice.column_labels = [c for c in col_tokens if c]
                    columns_pending = False
                    i = j
                    continue
                else:
                    # No ':=' found — these are data rows, not columns.
                    columns_pending = False
                    # Fall through to row parsing.

            # ---- If no current slice, we need an implicit one ----
            if current_slice is None:
                # No slice header seen yet — create an implicit headerless slice.
                # Scan for ':=' first (column labels before it).
                col_tokens_imp: list[str] = []
                found_assign_imp = False
                j = i
                while j < len(body_tokens):
                    t = body_tokens[j]
                    if t == ":=":
                        found_assign_imp = True
                        j += 1
                        break
                    if t.endswith(":="):
                        col_tokens_imp.append(t[:-2])
                        found_assign_imp = True
                        j += 1
                        break
                    if t == ":":
                        j += 1
                        continue
                    col_tokens_imp.append(t)
                    j += 1

                if found_assign_imp:
                    current_slice = SliceBlock(
                        header=[],
                        column_labels=[c for c in col_tokens_imp if c],
                    )
                    param.slices.append(current_slice)
                    columns_pending = False
                    i = j
                    continue
                else:
                    # Just skip — can't parse without structure.
                    i += 1
                    continue

            # ---- Data row parsing ----
            # A data row starts with a row key followed by values.
            # Number of values should match column count.
            if current_slice is not None and current_slice.column_labels:
                GMPLParser._parse_data_rows_from(
                    body_tokens, i, current_slice
                )
                # Advance past all remaining data rows until next slice or end.
                i = GMPLParser._find_next_slice_or_end(body_tokens, i)
                continue

            # Fallback: skip unrecognised token.
            i += 1

    @staticmethod
    def _parse_data_rows(body_tokens: list[str], slice_block: SliceBlock) -> None:
        """Parse all data rows from body_tokens into slice_block."""
        GMPLParser._parse_data_rows_from(body_tokens, 0, slice_block)

    @staticmethod
    def _parse_data_rows_from(
        tokens: list[str], start: int, slice_block: SliceBlock
    ) -> None:
        """Parse data rows starting at `start` until a new slice header or end."""
        num_cols = len(slice_block.column_labels)
        if num_cols == 0:
            return

        i = start
        while i < len(tokens):
            tok = tokens[i]
            # Stop if we hit a new slice header.
            if tok.startswith("["):
                break

            row_key = tok
            values: list[str] = []
            j = i + 1
            while j < len(tokens) and len(values) < num_cols:
                next_tok = tokens[j]
                if next_tok.startswith("[") or next_tok == ":=":
                    break
                values.append(next_tok)
                j += 1

            if values:
                slice_block.rows.append(RowEntry(key=row_key, values=values))
            i = j

    @staticmethod
    def _find_next_slice_or_end(tokens: list[str], start: int) -> int:
        """Find the index of the next '[' token or end of token list."""
        i = start
        while i < len(tokens):
            if tokens[i].startswith("["):
                return i
            i += 1
        return i


# ---------------------------------------------------------------------------
# CLI entry point for quick testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python GMPLParser.py <data_file.txt>")
        sys.exit(1)

    path = sys.argv[1]
    result = GMPLParser.parse_file(path)
    print(result.summary())
    print("\n" + "=" * 60 + "\n")

    # Detailed dump
    for p in result.params:
        print(f"\nparam {p.name} (default={p.default}):")
        for si, s in enumerate(p.slices):
            print(f"  slice[{si}]: header={s.header}")
            print(f"    columns: {s.column_labels}")
            for r in s.rows[:3]:
                print(f"    {r}")
            if len(s.rows) > 3:
                print(f"    ... ({len(s.rows)} rows total)")
