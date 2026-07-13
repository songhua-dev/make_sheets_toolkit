def process_batch(rows: list) -> dict:
    cleaned_rows = []
    total_processed = len(rows)
    incomplete_count = 0

    for row in rows:
        product_name = row.get("Product Name")
        if not product_name or str(product_name).strip() == "":
            incomplete_count += 1
            continue
        row["Product Name"] = str(product_name).lower()

        # 檢查 Price (Call for price 或 空白)
        price = row.get("Price")
        if not price or str(price).strip() == "" or str(price).upper() == "CALL FOR PRICE":
            incomplete_count += 1
            continue

        # 檢查其他欄位
        if not row.get("Company") or str(row.get("Company")).strip() == "":
            incomplete_count += 1
            continue
        if not row.get("Tel") or str(row.get("Tel")).strip() == "":
            incomplete_count += 1
            continue
        if not row.get("Location") or str(row.get("Location")).strip() == "":
            incomplete_count += 1
            continue

        # 如果通過所有檢查，加入清單
        cleaned_rows.append(row)

    return {
        "cleaned_data": cleaned_rows,
        "total_processed": total_processed,
        "incomplete_count": incomplete_count,
        "success_count": total_processed - incomplete_count
    }