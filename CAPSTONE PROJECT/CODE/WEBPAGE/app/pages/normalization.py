"""
Page 3: Normalization (1NF → 2NF → 3NF)
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import streamlit as st


def render() -> None:
    """
    Render the Database Normalization educational page.
    Explains the step-by-step transformation of raw Olist CSV datasets
    into a Third Normal Form (3NF) relational database schema.
    """
    st.title("Database Normalization: 1NF → 2NF → 3NF")
    st.markdown(
        "A comprehensive guide to the relational design methodology applied to the "
        "Brazilian E-Commerce dataset by Olist. This section documents how raw, denormalized "
        "CSV files are systematically decomposed to eliminate redundancy, avoid update anomalies, "
        "and enforce referential integrity."
    )

    # ─────────────────────────────────────────────────────────────
    # Section 1: Original CSV Structure
    # ─────────────────────────────────────────────────────────────
    with st.expander("📁 Section 1 — Original CSV Structure & Denormalization Issues", expanded=True):
        st.markdown(
            """
            The raw Kaggle Olist dataset comprises **9 flat CSV files**. While suitable for ad-hoc 
            data science exploration, the raw files exhibit severe denormalization, redundancy, 
            and data anomalies when treated as database relations:
            """
        )

        st.markdown(
            """
            | File Name | Primary Entity | Raw Columns | Relational Role |
            | :--- | :--- | :--- | :--- |
            | `olist_customers_dataset.csv` | Customers | `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` | Customer accounts & addresses |
            | `olist_geolocation_dataset.csv` | Spatial / Postal | `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state` | Geographic coordinate lookup |
            | `olist_order_items_dataset.csv` | Order Lines | `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value` | Line-item transactional details |
            | `olist_order_payments_dataset.csv` | Payment Splits | `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value` | Multi-method payments |
            | `olist_order_reviews_dataset.csv` | Reviews | `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp` | Customer feedback & ratings |
            | `olist_orders_dataset.csv` | Orders Master | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` | Order status & timestamps |
            | `olist_products_dataset.csv` | Products Catalog | `product_id`, `product_category_name`, `product_name_lenght`, `product_description_lenght`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | Physical product catalog |
            | `olist_sellers_dataset.csv` | Merchants | `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state` | Merchant directory |
            | `product_category_name_translation.csv` | Category Lookup | `product_category_name`, `product_category_name_english` | Portuguese to English dictionary |
            """
        )

        st.markdown("#### Denormalization Pitfalls in Raw Files:")
        st.markdown(
            """
            1. **Massive Geolocation Duplication**:
               - The raw `olist_geolocation_dataset.csv` contains over **1,000,000 rows** for approximately **19,015 distinct zip code prefixes**.
               - A single 5-digit zip code prefix is repeated up to thousands of times with slight variations in GPS coordinates and inconsistent city name casing/accents.
               - Lacks a primary key in its raw form.

            2. **Transitive Location Redundancy**:
               - Both `olist_customers_dataset.csv` and `olist_sellers_dataset.csv` explicitly store `city` and `state` alongside the zip code prefix.
               - If a city's administrative boundary or spelling changes, tens of thousands of customer and merchant rows must be modified.

            3. **Embedded Unstandardized Product Categories**:
               - Product records embed Portuguese category strings directly (`product_category_name`), while English translations reside in a separate unlinked lookup file.
               - Spelling mismatches or NULL categories cause orphaned records without foreign key validation.

            4. **Missing Relational Constraints**:
               - In flat CSVs, foreign keys (`customer_id`, `product_id`, `seller_id`, `order_id`) are untyped text strings with no engine-enforced integrity or cascade semantics.
            """
        )

    # ─────────────────────────────────────────────────────────────
    # Section 2: Functional Dependencies
    # ─────────────────────────────────────────────────────────────
    with st.expander("🔑 Section 2 — Functional Dependencies (FDs)"):
        st.markdown(
            """
            A **Functional Dependency** $X \\rightarrow Y$ denotes that attribute set $X$ uniquely determines 
            the values of attribute set $Y$. In our normalized 3NF relational schema, the following 
            functional dependencies are formally identified for each table:
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 1. `geolocation`")
            st.latex(r"\text{zip\_prefix} \longrightarrow \{\text{city}, \text{state}, \text{avg\_lat}, \text{avg\_lng}\}")
            st.caption("Each 5-digit zip code prefix uniquely determines city, state, and aggregated centroid coordinates.")

            st.markdown("##### 2. `customers`")
            st.latex(r"\text{customer\_id} \longrightarrow \{\text{customer\_unique\_id}, \text{zip\_prefix}\}")
            st.caption("A per-order customer token determines the master customer UUID and location reference.")

            st.markdown("##### 3. `sellers`")
            st.latex(r"\text{seller\_id} \longrightarrow \{\text{zip\_prefix}\}")
            st.caption("Each seller account uniquely determines its operating postal prefix.")

            st.markdown("##### 4. `product_categories`")
            st.latex(r"\text{category\_name} \longrightarrow \{\text{category\_name\_en}\}")
            st.caption("The primary Portuguese category name determines its English translation.")

            st.markdown("##### 5. `products`")
            st.latex(r"\text{product\_id} \longrightarrow \begin{cases} \text{category\_name}, \text{weight\_g}, \\ \text{length\_cm}, \text{height\_cm}, \\ \text{width\_cm}, \text{photos\_qty} \end{cases}")
            st.caption("A product identifier determines category and physical packaging dimensions.")

        with col2:
            st.markdown("##### 6. `orders`")
            st.latex(r"\text{order\_id} \longrightarrow \begin{cases} \text{customer\_id}, \text{order\_status}, \\ \text{order\_purchase\_timestamp}, \\ \text{order\_approved\_at}, \\ \text{order\_delivered\_carrier\_date}, \\ \text{order\_delivered\_customer\_date}, \\ \text{order\_estimated\_delivery\_date} \end{cases}")
            st.caption("An order identifier uniquely determines customer association and fulfillment milestones.")

            st.markdown("##### 7. `order_items` (Composite Key)")
            st.latex(r"\{\text{order\_id}, \text{order\_item\_id}\} \longrightarrow \begin{cases} \text{product\_id}, \text{seller\_id}, \\ \text{shipping\_limit\_date}, \\ \text{price}, \text{freight\_value} \end{cases}")
            st.caption("The item line within an order determines product, seller, price, and shipping freight.")

            st.markdown("##### 8. `order_payments` (Composite Key)")
            st.latex(r"\{\text{order\_id}, \text{payment\_sequential}\} \longrightarrow \{\text{payment\_type}, \text{installments}, \text{payment\_value}\}")
            st.caption("The sequential split index within an order determines payment method and amount.")

            st.markdown("##### 9. `order_reviews` (Composite Key)")
            st.latex(r"\{\text{review\_id}, \text{order\_id}\} \longrightarrow \begin{cases} \text{review\_score}, \text{review\_comment\_title}, \\ \text{review\_comment\_message}, \\ \text{review\_creation\_date}, \\ \text{review\_answer\_timestamp} \end{cases}")
            st.caption("Review ID scoped to an order determines customer score, text feedback, and timestamps.")

    # ─────────────────────────────────────────────────────────────
    # Section 3: Candidate Keys
    # ─────────────────────────────────────────────────────────────
    with st.expander("🎯 Section 3 — Candidate Keys & Chosen Primary Keys"):
        st.markdown(
            """
            A **Candidate Key** is a minimal superkey — a minimal set of attributes that uniquely 
            identifies any record in the relation. For each relation, one candidate key is selected as the 
            **Primary Key (PK)** to enforce entity integrity.
            """
        )

        st.markdown(
            """
            | Table Name | Candidate Key(s) | Chosen Primary Key (PK) | Key Nature | Rationale |
            | :--- | :--- | :--- | :--- | :--- |
            | `geolocation` | `{zip_prefix}` | `zip_prefix` | Natural Key | Deduplicated postal prefix uniquely partitions geographic regions in Brazil. |
            | `customers` | `{customer_id}` | `customer_id` | Surrogate Key | Unique 32-char MD5 token issued for each distinct order placement. |
            | `sellers` | `{seller_id}` | `seller_id` | Surrogate Key | Unique 32-char MD5 token identifying each registered seller. |
            | `product_categories` | `{category_name}`, `{category_name_en}` | `category_name` | Natural Key | Primary Portuguese category key; English name is an alternate unique candidate key. |
            | `products` | `{product_id}` | `product_id` | Surrogate Key | Unique 32-char MD5 hash representing each catalog item. |
            | `orders` | `{order_id}` | `order_id` | Surrogate Key | Unique 32-char MD5 hash assigned to each checkout transaction. |
            | `order_items` | `{order_id, order_item_id}` | `{order_id, order_item_id}` | Composite Key | An order contains sequential line items (1, 2, ...); both attributes are required for uniqueness. |
            | `order_payments` | `{order_id, payment_sequential}` | `{order_id, payment_sequential}` | Composite Key | Orders may be paid with split tenders; sequential index distinguishes splits within an order. |
            | `order_reviews` | `{review_id, order_id}` | `{review_id, order_id}` | Composite Key | Resolves edge-cases in the Kaggle dataset where multi-order surveys or duplicate review tokens occur. |
            """
        )

    # ─────────────────────────────────────────────────────────────
    # Section 4: First Normal Form (1NF)
    # ─────────────────────────────────────────────────────────────
    with st.expander("1️⃣ Section 4 — First Normal Form (1NF)"):
        st.markdown("### First Normal Form (1NF)")
        st.markdown(
            """
            #### Formal Rules of 1NF:
            1. **Atomic Values**: Each attribute value must be atomic (indivisible). No repeating groups, sets, arrays, or comma-delimited strings are allowed within a single attribute.
            2. **No Repeating Column Groups**: There must be no numbered columns representing multiples of an entity (e.g., `item_1`, `item_2`, `item_3`).
            3. **Explicit Primary Key**: Each tuple in the relation must be uniquely identifiable via a designated primary key.
            4. **Consistent Domain Types**: All values in an attribute must belong to the same underlying domain.
            """
        )

        st.markdown("#### How Olist Satisfies 1NF:")
        st.markdown(
            """
            - **Scalar Data Types**: All columns in our MySQL schema use strictly atomic SQL primitives (`VARCHAR`, `CHAR`, `INT`, `DECIMAL`, `DATETIME`, `TEXT`).
            - **Relational Line Items**: Instead of storing multiple products inside an array or multiple columns on `orders`, items are modeled as distinct rows in `order_items`.
            - **Deduplication of Geolocation**: In the raw dataset, `olist_geolocation_dataset.csv` contained over 1,000,000 non-atomic GPS observations per postal area. During ETL, coordinates were aggregated into single atomic averages (`avg_lat`, `avg_lng`), guaranteeing that `zip_prefix` uniquely identifies a single atomic row.
            """
        )

        st.info(
            "💡 **1NF Example**: Rather than having `orders(order_id, customer_id, product_1, product_2, product_3)`, "
            "each product purchase is normalized into individual atomic rows in `order_items(order_id, order_item_id, product_id, ...)`."
        )

    # ─────────────────────────────────────────────────────────────
    # Section 5: Second Normal Form (2NF)
    # ─────────────────────────────────────────────────────────────
    with st.expander("2️⃣ Section 5 — Second Normal Form (2NF)"):
        st.markdown("### Second Normal Form (2NF)")
        st.markdown(
            """
            #### Formal Rules of 2NF:
            1. The relation must be in **First Normal Form (1NF)**.
            2. **No Partial Dependencies**: Every non-prime attribute (attributes not part of any candidate key) must be **fully functionally dependent** on the entire primary key, rather than on a proper subset of a composite primary key.

            > *Note: Any table whose primary key is a single attribute (such as `orders`, `products`, `customers`, `sellers`, `geolocation`, and `product_categories`) is **automatically in 2NF** once it satisfies 1NF.*
            """
        )

        st.markdown("#### Verification of Composite Primary Key Relations:")
        st.markdown(
            """
            In our schema, three relations feature composite primary keys:

            1. **`order_items` — Composite PK: `{order_id, order_item_id}`**:
               - Attributes: `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value`.
               - **Dependency check**: Does `price` or `product_id` depend on `order_id` alone? **No**, because an order often contains multiple distinct products from different sellers.
               - Does `price` depend on `order_item_id` alone? **No**, because item sequence number `1` exists in thousands of orders with completely different prices.
               - Therefore, all non-key attributes are fully functionally dependent on `{order_id, order_item_id}`. No partial dependencies exist.

            2. **`order_payments` — Composite PK: `{order_id, payment_sequential}`**:
               - Attributes: `payment_type`, `installments`, `payment_value`.
               - **Dependency check**: A customer might pay an order split across two credit cards or a voucher plus boleto. `payment_value` describes that specific installment sequence of that specific order. Neither `order_id` alone nor `payment_sequential` alone is sufficient.

            3. **`order_reviews` — Composite PK: `{review_id, order_id}`**:
               - Attributes: `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`.
               - All feedback attributes depend strictly on the composite key.
            """
        )

        st.success(
            "✅ **2NF Verified**: None of the non-prime attributes in `order_items`, `order_payments`, or `order_reviews` "
            "depend on a partial subset of the primary key."
        )

    # ─────────────────────────────────────────────────────────────
    # Section 6: Third Normal Form (3NF)
    # ─────────────────────────────────────────────────────────────
    with st.expander("3️⃣ Section 6 — Third Normal Form (3NF)"):
        st.markdown("### Third Normal Form (3NF)")
        st.markdown(
            """
            #### Formal Rules of 3NF:
            1. The relation must be in **Second Normal Form (2NF)**.
            2. **No Transitive Dependencies**: No non-prime attribute should be transitively dependent on the primary key.
            Formally, for every non-trivial functional dependency $X \\rightarrow A$:
            - $X$ is a **Superkey**, OR
            - $A$ is a **Prime Attribute** (part of a candidate key).
            
            In plain terms: *Every non-key attribute must depend on the key, the whole key, and nothing but the key.*
            """
        )

        st.markdown("#### 3NF Normalization Steps Applied to Olist:")

        st.markdown(
            """
            ##### 1. Eliminating Location Transitive Dependencies in Customers and Sellers
            - **Raw Structure**: In the original CSVs, `customers` contained:
              `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state`.
            - **Transitive Dependency Chain**:
            """
        )
        st.latex(r"\text{customer\_id} \longrightarrow \text{zip\_prefix} \longrightarrow \{\text{city}, \text{state}\}")
        st.markdown(
            """
            - Because `zip_prefix` is not a candidate key of `customers`, this violated 3NF. If a zip code's city spelling changed, thousands of customer rows required updating (**Update Anomaly**).
            - **3NF Resolution**: Decompose into:
              - `geolocation(zip_prefix, city, state, avg_lat, avg_lng)` [PK: `zip_prefix`]
              - `customers(customer_id, customer_unique_id, zip_prefix)` [FK: `zip_prefix` references `geolocation`]
              - `sellers(seller_id, zip_prefix)` [FK: `zip_prefix` references `geolocation`]
            - **Result**: City and state are stored exactly once per postal prefix. Zero transitive redundancy.
            """
        )

        st.markdown(
            """
            ##### 2. Eliminating Category Translation Transitive Dependencies
            - **Raw Structure**: Products contained Portuguese `product_category_name`. If we had merged the English translation into `products`:
            """
        )
        st.latex(r"\text{product\_id} \longrightarrow \text{category\_name} \longrightarrow \text{category\_name\_en}")
        st.markdown(
            """
            - `category_name` is not a candidate key of `products`, creating a transitive dependency.
            - **3NF Resolution**: Isolate the lookup into `product_categories`:
              - `product_categories(category_name, category_name_en)` [PK: `category_name`]
              - `products(product_id, category_name, ...)` [FK: `category_name` references `product_categories`]
            - **Result**: Category translation metadata is isolated from individual product catalog entries.
            """
        )

    # ─────────────────────────────────────────────────────────────
    # Section 7: Resulting Tables Summary
    # ─────────────────────────────────────────────────────────────
    with st.expander("📊 Section 7 — Resulting 3NF Tables Summary", expanded=True):
        st.markdown(
            """
            The normalized schema consists of **9 tables** in full Third Normal Form (3NF), 
            governed by relational integrity constraints and explicit foreign keys:
            """
        )

        st.markdown(
            """
            | Table Name | Primary Key (PK) | Foreign Keys (FKs) | Columns | Entity Description |
            | :--- | :--- | :--- | :---: | :--- |
            | `geolocation` | `zip_prefix` | *None* | 5 | Master Brazilian postal centroids with unique zip prefixes and coordinates. |
            | `customers` | `customer_id` | `zip_prefix → geolocation(zip_prefix)` | 3 | Customer order instances linked to their postal location. |
            | `sellers` | `seller_id` | `zip_prefix → geolocation(zip_prefix)` | 2 | Registered merchants linked to their dispatch postal location. |
            | `product_categories` | `category_name` | *None* | 2 | Master catalog of category names with English translations. |
            | `products` | `product_id` | `category_name → product_categories(category_name)` | 7 | Catalog items with physical packaging weights and dimensions. |
            | `orders` | `order_id` | `customer_id → customers(customer_id)` | 8 | Transaction lifecycle records and order fulfillment timestamps. |
            | `order_items` | `{order_id, order_item_id}` | `order_id → orders(order_id)`<br>`product_id → products(product_id)`<br>`seller_id → sellers(seller_id)` | 7 | Normalized line items with individual price and shipping freight. |
            | `order_payments` | `{order_id, payment_sequential}` | `order_id → orders(order_id)` | 5 | Split-payment installments and payment method breakdown. |
            | `order_reviews` | `{review_id, order_id}` | `order_id → orders(order_id)` | 7 | Customer ratings (1–5) and review comment timestamps. |
            """
        )

        st.markdown(
            """
            > [!TIP]
            > **Benefits of the 3NF Schema Architecture:**
            > - **Zero Redundancy**: Geographic city/state names and category translations are stored in exactly one place.
            > - **Anomalies Eliminated**: Insertion, deletion, and update anomalies are prevented by relational foreign keys.
            > - **Optimized Storage**: Replaced repetitive text strings with fixed-length foreign keys and indexed tokens.
            > - **Query Performance**: Facilitates fast index scans and join paths on primary and foreign keys.
            """
        )
