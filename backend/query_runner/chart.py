def detect_chart_type(columns: list, rows: list) -> dict | None:
    """Auto-detect best chart type from result shape. Returns chart_config dict or None."""
    if not rows or len(columns) < 2:
        return None

    col_types = []
    for i, col in enumerate(columns):
        sample = next((r[i] for r in rows if r[i] is not None), None)
        name_lower = col.lower()

        # Keyword check takes priority over value type
        if any(k in name_lower for k in ("pct", "percent", "rate", "share")):
            col_types.append("percent")
        elif any(k in name_lower for k in ("date", "month", "year", "week", "period", "day")):
            col_types.append("date")
        elif isinstance(sample, (int, float)):
            col_types.append("numeric")
        elif isinstance(sample, str):
            col_types.append("text")
        else:
            col_types.append("text")

    text_cols = [columns[i] for i, t in enumerate(col_types) if t == "text"]
    date_cols = [columns[i] for i, t in enumerate(col_types) if t == "date"]
    num_cols = [columns[i] for i, t in enumerate(col_types) if t == "numeric"]
    pct_cols = [columns[i] for i, t in enumerate(col_types) if t == "percent"]

    if date_cols and num_cols:
        return {"type": "line", "x_key": date_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    if pct_cols and text_cols:
        return {"type": "pie", "x_key": text_cols[0], "y_key": pct_cols[0], "label": pct_cols[0]}
    if text_cols and num_cols:
        return {"type": "bar", "x_key": text_cols[0], "y_key": num_cols[0], "label": num_cols[0]}
    return None
