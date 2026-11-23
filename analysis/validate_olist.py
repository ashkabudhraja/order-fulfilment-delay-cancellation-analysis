from pathlib import Path
import pandas as pd

# Find the data folder relative to this Python file
data_folder = Path(__file__).resolve().parent.parent / "data"

print("Looking for files in:", data_folder)
print("Data folder exists:", data_folder.exists())

required_files = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
    "olist_order_reviews_dataset.csv",
]

for filename in required_files:
    file_path = data_folder / filename

    if file_path.is_file():
        print(f"FOUND: {filename}")
    else:
        print(f"MISSING: {filename}")
        

orders = pd.read_csv(data_folder / "olist_orders_dataset.csv")
order_items = pd.read_csv(data_folder / "olist_order_items_dataset.csv")
products = pd.read_csv(data_folder / "olist_products_dataset.csv")
category_translation = pd.read_csv(
    data_folder / "product_category_name_translation.csv"
)
reviews = pd.read_csv(data_folder / "olist_order_reviews_dataset.csv")

datasets = {
    "Orders": orders,
    "Order Items": order_items,
    "Products": products,
    "Category Translation": category_translation,
    "Reviews": reviews
}

for name, df in datasets.items():
    print(f"\n--- {name} ---")
    print("Rows and columns:", df.shape)
    print("Column names:", df.columns.tolist())
    print(df.head(3))


for name, df in datasets.items():
    print(f"\n--- {name}: Data Quality ---")

    print("Duplicate rows:", df.duplicated().sum())

    missing_values = df.isnull().sum()
    missing_values = missing_values[missing_values > 0]

    if missing_values.empty:
        print("Missing values: None")
    else:
        print("Missing values:")
        print(missing_values.sort_values(ascending=False))


print("\n--- ORDER STATUS DISTRIBUTION ---")

print(
    orders["order_status"]
    .value_counts(dropna=False)
)

print("\nUnique order statuses:")
print(orders["order_status"].unique())


date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

print("\n--- DELIVERY DATE VALIDATION ---")

for col in date_columns:
    print(f"\n{col}")
    print("Missing values:", orders[col].isna().sum())

    parsed_dates = pd.to_datetime(orders[col], errors="coerce")
    invalid_dates = orders[col].notna() & parsed_dates.isna()

    print("Invalid non-empty dates:", invalid_dates.sum())



print("\n--- ID VALIDATION ---")

print(
    "Orders: duplicate order IDs =",
    orders["order_id"].duplicated().sum()
)

print(
    "Order items: duplicate order_id + order_item_id pairs =",
    order_items.duplicated(
        subset=["order_id", "order_item_id"]
    ).sum()
)

print(
    "Products: duplicate product IDs =",
    products["product_id"].duplicated().sum()
)

print(
    "Reviews: duplicate review IDs =",
    reviews["review_id"].duplicated().sum()
)


order_ids = set(orders["order_id"])

item_order_ids = set(order_items["order_id"])
review_order_ids = set(reviews["order_id"])

print("\n--- TABLE RELATIONSHIP VALIDATION ---")

print(
    "Item records linked to unknown orders:",
    (~order_items["order_id"].isin(order_ids)).sum()
)

print(
    "Review records linked to unknown orders:",
    (~reviews["order_id"].isin(order_ids)).sum()
)

print(
    "Distinct orders in orders table:",
    orders["order_id"].nunique()
)

print(
    "Distinct orders in order items table:",
    order_items["order_id"].nunique()
)

print(
    "Distinct orders in reviews table:",
    reviews["order_id"].nunique()
)


# STEP 7A: Missing delivery dates by order status

print("\n--- MISSING DELIVERY DATES BY STATUS ---")

date_check = orders.copy()

date_check["order_delivered_customer_date"] = pd.to_datetime(
    date_check["order_delivered_customer_date"],
    errors="coerce"
)

date_check["order_delivered_carrier_date"] = pd.to_datetime(
    date_check["order_delivered_carrier_date"],
    errors="coerce"
)

print(
    date_check.groupby("order_status")
    .agg(
        total_orders=("order_id", "count"),
        missing_carrier_date=(
            "order_delivered_carrier_date",
            lambda x: x.isna().sum()
        ),
        missing_customer_delivery_date=(
            "order_delivered_customer_date",
            lambda x: x.isna().sum()
        )
    )
    .to_string()
)


# STEP 7B: Investigate repeated review IDs

print("\n--- REVIEW ID INVESTIGATION ---")

duplicate_review_rows = reviews[
    reviews.duplicated(subset=["review_id"], keep=False)
].sort_values("review_id")

print("Rows with a repeated review ID:", len(duplicate_review_rows))
print("Number of distinct repeated review IDs:",
      duplicate_review_rows["review_id"].nunique())

print("\nSample repeated review IDs:")
print(duplicate_review_rows.head(12).to_string(index=False))

print("\nOrders with multiple review records:")
print(
    reviews.groupby("order_id")["review_id"]
    .count()
    .gt(1)
    .sum()
)


# STEP 7C: Investigate missing product categories

print("\n--- PRODUCT CATEGORY INVESTIGATION ---")

print(
    "Products with missing category:",
    products["product_category_name"].isna().sum()
)

items_with_products = order_items.merge(
    products[["product_id", "product_category_name"]],
    on="product_id",
    how="left",
    validate="many_to_one"
)

print(
    "Order-item rows with missing category:",
    items_with_products["product_category_name"].isna().sum()
)

print(
    "Distinct products with missing category:",
    items_with_products.loc[
        items_with_products["product_category_name"].isna(),
        "product_id"
    ].nunique()
)


# STEP 8: Preliminary late-delivery analysis

print("\n--- PRELIMINARY LATE-DELIVERY ANALYSIS ---")

delivery_data = orders.copy()

delivery_data["order_delivered_customer_date"] = pd.to_datetime(
    delivery_data["order_delivered_customer_date"],
    errors="coerce"
)

delivery_data["order_estimated_delivery_date"] = pd.to_datetime(
    delivery_data["order_estimated_delivery_date"],
    errors="coerce"
)

eligible = delivery_data[
    (delivery_data["order_status"] == "delivered")
    & delivery_data["order_delivered_customer_date"].notna()
    & delivery_data["order_estimated_delivery_date"].notna()
].copy()

eligible["is_late"] = (
    eligible["order_delivered_customer_date"]
    > eligible["order_estimated_delivery_date"]
)

eligible["delay_days"] = (
    eligible["order_delivered_customer_date"]
    - eligible["order_estimated_delivery_date"]
).dt.total_seconds() / 86400

late_orders = eligible[eligible["is_late"]]

eligible_count = len(eligible)
late_count = len(late_orders)

late_rate = (
    late_count / eligible_count * 100
    if eligible_count > 0 else 0
)

average_delay = (
    late_orders["delay_days"].mean()
    if late_count > 0 else 0
)

print("Eligible delivered orders:", eligible_count)
print("Late delivered orders:", late_count)
print(f"Late delivery rate: {late_rate:.2f}%")
print(f"Average delay among late orders: {average_delay:.2f} days")


# STEP 9A: Investigate repeated review IDs

print("\n--- STEP 9A: REVIEW ID INVESTIGATION ---")

# Get all rows belonging to repeated review IDs
repeated_reviews = reviews[
    reviews.duplicated(subset=["review_id"], keep=False)
].copy()

# Count how many different orders use each review ID
review_id_summary = (
    repeated_reviews.groupby("review_id")
    .agg(
        row_count=("review_id", "size"),
        distinct_orders=("order_id", "nunique"),
        distinct_scores=("review_score", "nunique"),
        distinct_creation_dates=("review_creation_date", "nunique"),
        distinct_answer_dates=("review_answer_timestamp", "nunique")
    )
    .reset_index()
)

print("Repeated review ID groups:", len(review_id_summary))

print("\nNumber of repeated IDs linked to multiple orders:")
print((review_id_summary["distinct_orders"] > 1).sum())

print("\nRepeated IDs with conflicting review scores:")
print((review_id_summary["distinct_scores"] > 1).sum())

print("\nRepeated IDs with conflicting creation dates:")
print((review_id_summary["distinct_creation_dates"] > 1).sum())

print("\nRepeated IDs with conflicting answer timestamps:")
print((review_id_summary["distinct_answer_dates"] > 1).sum())

print("\nSample of repeated ID summary:")
print(review_id_summary.head(10).to_string(index=False))


# Check whether repeated rows have identical review content
review_content_columns = [
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp"
]

content_variation = (
    repeated_reviews.groupby("review_id")[review_content_columns]
    .nunique(dropna=False)
)

print("\nRepeated IDs with differing review content:")
print((content_variation > 1).any(axis=1).sum())


# STEP 9B: Compare timestamp-based and calendar-date-based lateness

print("\n--- STEP 9B: LATE-DELIVERY DEFINITION COMPARISON ---")

delivery_data = orders.copy()

# Convert delivery fields to datetime
delivery_data["order_delivered_customer_date"] = pd.to_datetime(
    delivery_data["order_delivered_customer_date"],
    errors="coerce"
)

delivery_data["order_estimated_delivery_date"] = pd.to_datetime(
    delivery_data["order_estimated_delivery_date"],
    errors="coerce"
)

# Only delivered orders with both required dates
eligible = delivery_data[
    (delivery_data["order_status"] == "delivered")
    & delivery_data["order_delivered_customer_date"].notna()
    & delivery_data["order_estimated_delivery_date"].notna()
].copy()

# Method 1: Compare full timestamps
eligible["late_by_timestamp"] = (
    eligible["order_delivered_customer_date"]
    > eligible["order_estimated_delivery_date"]
)

# Method 2: Compare calendar dates only
eligible["late_by_calendar_date"] = (
    eligible["order_delivered_customer_date"].dt.date
    > eligible["order_estimated_delivery_date"].dt.date
)

eligible_count = len(eligible)

timestamp_late_count = eligible["late_by_timestamp"].sum()
calendar_late_count = eligible["late_by_calendar_date"].sum()

timestamp_rate = timestamp_late_count / eligible_count * 100
calendar_rate = calendar_late_count / eligible_count * 100

print("Eligible delivered orders:", eligible_count)

print("\nFull timestamp method:")
print("Late orders:", timestamp_late_count)
print(f"Late-delivery rate: {timestamp_rate:.2f}%")

print("\nCalendar-date method:")
print("Late orders:", calendar_late_count)
print(f"Late-delivery rate: {calendar_rate:.2f}%")

print("\nOrders classified differently by the two methods:")
print(
    (
        eligible["late_by_timestamp"]
        != eligible["late_by_calendar_date"]
    ).sum()
)


# STEP 10: Cancellation and unavailable order analysis

print("\n--- STEP 10: CANCELLATION ANALYSIS ---")

total_orders = len(orders)

status_counts = orders["order_status"].value_counts()

canceled_orders = status_counts.get("canceled", 0)
unavailable_orders = status_counts.get("unavailable", 0)

canceled_rate = canceled_orders / total_orders * 100
unavailable_rate = unavailable_orders / total_orders * 100

combined_orders = canceled_orders + unavailable_orders
combined_rate = combined_orders / total_orders * 100

print("Total orders:", total_orders)

print("\nCanceled orders:", canceled_orders)
print(f"Canceled order percentage: {canceled_rate:.2f}%")

print("\nUnavailable orders:", unavailable_orders)
print(f"Unavailable order percentage: {unavailable_rate:.2f}%")

print("\nCombined canceled + unavailable orders:", combined_orders)
print(f"Combined percentage: {combined_rate:.2f}%")

print("\nAll order statuses:")
print(status_counts.to_string())


# STEP 11: Monthly cancellation and unavailable-order trends

print("\n--- STEP 11: MONTHLY ORDER STATUS TRENDS ---")

monthly_data = orders.copy()

monthly_data["order_purchase_timestamp"] = pd.to_datetime(
    monthly_data["order_purchase_timestamp"],
    errors="coerce"
)

monthly_data = monthly_data.dropna(
    subset=["order_purchase_timestamp"]
)

monthly_data["purchase_month"] = (
    monthly_data["order_purchase_timestamp"].dt.to_period("M")
)

monthly_summary = (
    monthly_data.groupby("purchase_month")
    .agg(
        total_orders=("order_id", "count"),
        canceled_orders=(
            "order_status",
            lambda x: (x == "canceled").sum()
        ),
        unavailable_orders=(
            "order_status",
            lambda x: (x == "unavailable").sum()
        )
    )
    .reset_index()
)

monthly_summary["canceled_pct"] = (
    monthly_summary["canceled_orders"]
    / monthly_summary["total_orders"] * 100
)

monthly_summary["unavailable_pct"] = (
    monthly_summary["unavailable_orders"]
    / monthly_summary["total_orders"] * 100
)

monthly_summary["purchase_month"] = (
    monthly_summary["purchase_month"].astype(str)
)

print(monthly_summary.to_string(index=False))


# STEP 12: Monthly late-delivery analysis

print("\n--- STEP 12: MONTHLY LATE-DELIVERY TRENDS ---")

delivery_trend = orders.copy()

delivery_trend["order_purchase_timestamp"] = pd.to_datetime(
    delivery_trend["order_purchase_timestamp"],
    errors="coerce"
)

delivery_trend["order_delivered_customer_date"] = pd.to_datetime(
    delivery_trend["order_delivered_customer_date"],
    errors="coerce"
)

delivery_trend["order_estimated_delivery_date"] = pd.to_datetime(
    delivery_trend["order_estimated_delivery_date"],
    errors="coerce"
)

# Include only delivered orders with both delivery dates available
delivery_trend = delivery_trend[
    (delivery_trend["order_status"] == "delivered")
    & delivery_trend["order_delivered_customer_date"].notna()
    & delivery_trend["order_estimated_delivery_date"].notna()
    & delivery_trend["order_purchase_timestamp"].notna()
].copy()

# Compare calendar dates, not exact timestamps
delivery_trend["late_days"] = (
    delivery_trend["order_delivered_customer_date"].dt.normalize()
    - delivery_trend["order_estimated_delivery_date"].dt.normalize()
).dt.days

delivery_trend["is_late"] = delivery_trend["late_days"] > 0

delivery_trend["purchase_month"] = (
    delivery_trend["order_purchase_timestamp"].dt.to_period("M")
)

monthly_late_summary = (
    delivery_trend.groupby("purchase_month")
    .agg(
        eligible_delivered_orders=("order_id", "count"),
        late_orders=("is_late", "sum"),
        average_late_days=(
            "late_days",
            lambda x: x[x > 0].mean()
        )
    )
    .reset_index()
)

monthly_late_summary["late_delivery_pct"] = (
    monthly_late_summary["late_orders"]
    / monthly_late_summary["eligible_delivered_orders"] * 100
)

monthly_late_summary["purchase_month"] = (
    monthly_late_summary["purchase_month"].astype(str)
)

print("Eligible delivered orders:", len(delivery_trend))

print("\nMonthly late-delivery summary:")
print(
    monthly_late_summary.round(2).to_string(index=False)
)


# STEP 13: Late deliveries by product category

print("\n--- STEP 13: LATE DELIVERIES BY CATEGORY ---")

# Start with delivered orders that have both delivery dates
category_orders = orders[
    (orders["order_status"] == "delivered")
    & orders["order_delivered_customer_date"].notna()
    & orders["order_estimated_delivery_date"].notna()
].copy()

category_orders["order_delivered_customer_date"] = pd.to_datetime(
    category_orders["order_delivered_customer_date"],
    errors="coerce"
)

category_orders["order_estimated_delivery_date"] = pd.to_datetime(
    category_orders["order_estimated_delivery_date"],
    errors="coerce"
)

category_orders = category_orders.dropna(
    subset=[
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
)

category_orders["is_late"] = (
    category_orders["order_delivered_customer_date"].dt.date
    > category_orders["order_estimated_delivery_date"].dt.date
)

# Attach order items and product categories
category_data = category_orders[
    ["order_id", "is_late"]
].merge(
    order_items[["order_id", "product_id"]],
    on="order_id",
    how="inner"
)

category_data = category_data.merge(
    products[["product_id", "product_category_name"]],
    on="product_id",
    how="left"
)

category_data = category_data.merge(
    category_translation,
    on="product_category_name",
    how="left"
)

# Use English category names; keep missing categories visible
category_data["category"] = (
    category_data["product_category_name_english"]
    .fillna(category_data["product_category_name"])
    .fillna("Unknown")
)

# One record per order per category
category_order_level = category_data.drop_duplicates(
    subset=["order_id", "category"]
)

category_summary = (
    category_order_level.groupby("category")
    .agg(
        eligible_orders=("order_id", "nunique"),
        late_orders=("is_late", "sum")
    )
    .reset_index()
)

category_summary["late_delivery_pct"] = (
    category_summary["late_orders"]
    / category_summary["eligible_orders"] * 100
)

# Avoid drawing conclusions from categories with very few orders
category_summary = category_summary[
    category_summary["eligible_orders"] >= 100
].copy()

category_summary = category_summary.sort_values(
    "late_delivery_pct",
    ascending=False
)

print("Categories included (minimum 100 eligible orders):",
      len(category_summary))

print("\nTop 15 categories by late-delivery rate:")
print(category_summary.head(15).round(2).to_string(index=False))


# STEP 14: Late deliveries by seller

print("\n--- STEP 14: LATE DELIVERIES BY SELLER ---")

seller_orders = orders[
    (orders["order_status"] == "delivered")
    & orders["order_delivered_customer_date"].notna()
    & orders["order_estimated_delivery_date"].notna()
].copy()

seller_orders["order_delivered_customer_date"] = pd.to_datetime(
    seller_orders["order_delivered_customer_date"],
    errors="coerce"
)

seller_orders["order_estimated_delivery_date"] = pd.to_datetime(
    seller_orders["order_estimated_delivery_date"],
    errors="coerce"
)

seller_orders = seller_orders.dropna(
    subset=[
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
)

seller_orders["is_late"] = (
    seller_orders["order_delivered_customer_date"].dt.date
    > seller_orders["order_estimated_delivery_date"].dt.date
)

# Link delivered orders to sellers
seller_data = seller_orders[
    ["order_id", "is_late"]
].merge(
    order_items[["order_id", "seller_id"]],
    on="order_id",
    how="inner"
)

# One record per order per seller
seller_order_level = seller_data.drop_duplicates(
    subset=["order_id", "seller_id"]
)

seller_summary = (
    seller_order_level.groupby("seller_id")
    .agg(
        eligible_orders=("order_id", "nunique"),
        late_orders=("is_late", "sum")
    )
    .reset_index()
)

seller_summary["late_delivery_pct"] = (
    seller_summary["late_orders"]
    / seller_summary["eligible_orders"] * 100
)

# Require at least 30 eligible orders to reduce small-sample noise
seller_summary = seller_summary[
    seller_summary["eligible_orders"] >= 30
].copy()

seller_summary = seller_summary.sort_values(
    "late_delivery_pct",
    ascending=False
)

print("Sellers with at least 30 eligible orders:",
      len(seller_summary))

print("\nTop 15 sellers by late-delivery rate:")
print(seller_summary.head(15).round(2).to_string(index=False))

print("\nTop 15 sellers by late-order volume:")
print(
    seller_summary.sort_values(
        "late_orders", ascending=False
    ).head(15).round(2).to_string(index=False)
)


# STEP 15: Delivery performance and customer review scores

print("\n--- STEP 15: DELIVERY VS CUSTOMER REVIEWS ---")

# Reuse eligible delivered orders from Step 12
review_delivery = delivery_trend[
    ["order_id", "is_late"]
].copy()

# Convert review scores to numeric and aggregate to one row per order.
# This avoids counting an order multiple times if it has multiple reviews.
reviews_clean = reviews.copy()

reviews_clean["review_score"] = pd.to_numeric(
    reviews_clean["review_score"],
    errors="coerce"
)

order_reviews = (
    reviews_clean.dropna(subset=["review_score"])
    .groupby("order_id")
    .agg(
        average_review_score=("review_score", "mean"),
        review_record_count=("review_score", "size")
    )
    .reset_index()
)

# Attach order-level review scores to delivered orders
review_delivery = review_delivery.merge(
    order_reviews,
    on="order_id",
    how="left"
)

review_delivery["delivery_group"] = (
    review_delivery["is_late"]
    .map({True: "Late", False: "On time"})
)

reviewed_orders = review_delivery.dropna(
    subset=["average_review_score"]
).copy()

review_summary = (
    reviewed_orders.groupby("delivery_group")
    .agg(
        reviewed_orders=("order_id", "nunique"),
        average_review_score=("average_review_score", "mean"),
        low_score_orders=(
            "average_review_score",
            lambda x: (x <= 2).sum()
        )
    )
    .reset_index()
)

review_summary["low_score_pct"] = (
    review_summary["low_score_orders"]
    / review_summary["reviewed_orders"] * 100
)

print("Eligible delivered orders:", len(review_delivery))
print("Orders with review scores:", len(reviewed_orders))

print("\nReview summary by delivery group:")
print(review_summary.round(2).to_string(index=False))
