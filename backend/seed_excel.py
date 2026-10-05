from pathlib import Path
import re

import pandas as pd
import psycopg
from dotenv import load_dotenv


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

EXCEL_FILES = [
    DATA_DIR / "bracketed_cleaned_DU_Full_Index_Suite.xlsx",
    DATA_DIR / "bracketed_cleaned_JMI_Full_Index_Suite.xlsx",
    DATA_DIR / "bracketed_cleaned_JNU_Full_Index_Suite.xlsx",
    DATA_DIR / "bracketed_cleaned_PRIVATE_Full_Index_Suite.xlsx",
]


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = __import__("os").getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL was not found in .env")


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """Convert pandas empty values to None."""
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return None

    return value


def clean_openalex_id(value):
    """
    Convert:
        A123456789
    or:
        https://openalex.org/A123456789

    into:
        A123456789
    """
    value = clean_value(value)

    if value is None:
        return None

    value = str(value).strip()

    match = re.search(r"(A\d+)$", value)

    if match:
        return match.group(1)

    return value


def number(value):
    """Convert numeric Excel values safely."""
    value = clean_value(value)

    if value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def decimal(value):
    """Convert numeric index values safely."""
    value = clean_value(value)

    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ============================================================
# EXCEL → DATABASE
# ============================================================

def seed_file(conn, excel_path):
    print()
    print("=" * 70)
    print(f"Processing: {excel_path.name}")
    print("=" * 70)

    df = pd.read_excel(excel_path, sheet_name="All")

    print(f"Rows found: {len(df)}")

    inserted_or_updated = 0

    for _, row in df.iterrows():

        name = clean_value(row["Author Name"])
        institution = clean_value(row["Institution"])
        institution_author_id = clean_value(row["ID"])
        core_field = clean_value(row["Core Field"])
        openalex_author_id = clean_openalex_id(
            row["OpenAlex Author ID"]
        )

        if not name:
            continue

        # ----------------------------------------------------
        # 1. RESEARCHER
        # ----------------------------------------------------

        researcher_id = None

        if openalex_author_id:
            existing = conn.execute(
                """
                SELECT id
                FROM researchers
                WHERE openalex_author_id = %s
                LIMIT 1
                """,
                (openalex_author_id,),
            ).fetchone()

            if existing:
                researcher_id = existing[0]

        if researcher_id is None:
            existing = conn.execute(
                """
                SELECT id
                FROM researchers
                WHERE name = %s
                  AND institution = %s
                LIMIT 1
                """,
                (name, institution),
            ).fetchone()

            if existing:
                researcher_id = existing[0]

        if researcher_id:
            conn.execute(
                """
                UPDATE researchers
                SET
                    name = %s,
                    institution = %s,
                    institution_author_id = %s,
                    core_field = %s,
                    openalex_author_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    name,
                    institution,
                    institution_author_id,
                    core_field,
                    openalex_author_id,
                    researcher_id,
                ),
            )

        else:
            result = conn.execute(
                """
                INSERT INTO researchers (
                    name,
                    institution,
                    institution_author_id,
                    core_field,
                    openalex_author_id,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING id
                """,
                (
                    name,
                    institution,
                    institution_author_id,
                    core_field,
                    openalex_author_id,
                ),
            )

            researcher_id = result.fetchone()[0]

        # ----------------------------------------------------
        # 2. RESEARCHER METRICS
        # ----------------------------------------------------

        metrics = {
            "first_year_of_publication": number(
                row["First Year of Publication"]
            ),
            "total_papers": number(
                row["Total No. of Papers"]
            ),
            "papers_authors_gt_5": number(
                row["No. of Papers (Authors > 5)"]
            ),
            "first_author_papers": number(
                row["No. of Papers (First Author)"]
            ),
            "corresponding_author_papers": number(
                row["No. of Papers (Corresponding Author)"]
            ),
            "first_or_corresponding_papers": number(
                row["No. of Papers (First OR Corresponding Author)"]
            ),
            "years_active": decimal(
                row["Years Active (Y)"]
            ),
            "openalex_h_index": number(
                row["OpenAlex Profile H-Index"]
            ),
            "openalex_i10_index": number(
                row["OpenAlex Profile i10-Index"]
            ),
            "openalex_total_citations": number(
                row["OpenAlex Profile Total Citations"]
            ),
            "bracket": clean_value(
                row["Bracket"]
            ),
        }

        existing = conn.execute(
            """
            SELECT id
            FROM researcher_metrics
            WHERE researcher_id = %s
            LIMIT 1
            """,
            (researcher_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE researcher_metrics
                SET
                    first_year_of_publication = %s,
                    total_papers = %s,
                    papers_authors_gt_5 = %s,
                    first_author_papers = %s,
                    corresponding_author_papers = %s,
                    first_or_corresponding_papers = %s,
                    years_active = %s,
                    openalex_h_index = %s,
                    openalex_i10_index = %s,
                    openalex_total_citations = %s,
                    bracket = %s,
                    last_retrieved = NOW()
                WHERE researcher_id = %s
                """,
                (
                    metrics["first_year_of_publication"],
                    metrics["total_papers"],
                    metrics["papers_authors_gt_5"],
                    metrics["first_author_papers"],
                    metrics["corresponding_author_papers"],
                    metrics["first_or_corresponding_papers"],
                    metrics["years_active"],
                    metrics["openalex_h_index"],
                    metrics["openalex_i10_index"],
                    metrics["openalex_total_citations"],
                    metrics["bracket"],
                    researcher_id,
                ),
            )

        else:
            conn.execute(
                """
                INSERT INTO researcher_metrics (
                    researcher_id,
                    first_year_of_publication,
                    total_papers,
                    papers_authors_gt_5,
                    first_author_papers,
                    corresponding_author_papers,
                    first_or_corresponding_papers,
                    years_active,
                    openalex_h_index,
                    openalex_i10_index,
                    openalex_total_citations,
                    bracket,
                    last_retrieved
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, NOW()
                )
                """,
                (
                    researcher_id,
                    metrics["first_year_of_publication"],
                    metrics["total_papers"],
                    metrics["papers_authors_gt_5"],
                    metrics["first_author_papers"],
                    metrics["corresponding_author_papers"],
                    metrics["first_or_corresponding_papers"],
                    metrics["years_active"],
                    metrics["openalex_h_index"],
                    metrics["openalex_i10_index"],
                    metrics["openalex_total_citations"],
                    metrics["bracket"],
                ),
            )

        # ----------------------------------------------------
        # 3. RESEARCHER INDICES
        # ----------------------------------------------------

        index_values = (
            decimal(row["M-Quotient (M = h/Y)"]),
            decimal(row["HyperIndex (M-Quotient)"]),
            decimal(row["AR-Index"]),
            decimal(row["HyperIndex (AR-Index)"]),
            decimal(row["Local H-Index"]),
            decimal(row["g-index"]),
            decimal(row["A-index"]),
            decimal(row["r-index"]),
            decimal(row["h(2)-index"]),
            decimal(row["hg-index"]),
            decimal(row["m-index (Median Citations in h-core)"]),
            decimal(row["q2-index"]),
            decimal(row["e-index"]),
            decimal(row["hw-index"]),
            decimal(row["Sh-index (Authorship-Weighted, Karthik et al. 2025)"]),
        )

        existing = conn.execute(
            """
            SELECT id
            FROM researcher_indices
            WHERE researcher_id = %s
            LIMIT 1
            """,
            (researcher_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE researcher_indices
                SET
                    m_quotient = %s,
                    hyperindex_m_quotient = %s,
                    ar_index = %s,
                    hyperindex_ar_index = %s,
                    local_h_index = %s,
                    g_index = %s,
                    a_index = %s,
                    r_index = %s,
                    h2_index = %s,
                    hg_index = %s,
                    m_index = %s,
                    q2_index = %s,
                    e_index = %s,
                    hw_index = %s,
                    sh_index = %s
                WHERE researcher_id = %s
                """,
                (*index_values, researcher_id),
            )

        else:
            conn.execute(
                """
                INSERT INTO researcher_indices (
                    researcher_id,
                    m_quotient,
                    hyperindex_m_quotient,
                    ar_index,
                    hyperindex_ar_index,
                    local_h_index,
                    g_index,
                    a_index,
                    r_index,
                    h2_index,
                    hg_index,
                    m_index,
                    q2_index,
                    e_index,
                    hw_index,
                    sh_index
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (researcher_id, *index_values),
            )

        # ----------------------------------------------------
        # 4. AUTHOR ROLE METRICS
        # ----------------------------------------------------

        role_values = (
            number(row["H-index (First Author papers only)"]),
            number(row["H-index (Second Author papers only)"]),
            number(row["H-index (Co-Author papers only)"]),
            number(row["H-index (Corresponding Author papers only)"]),
        )

        existing = conn.execute(
            """
            SELECT id
            FROM author_role_metrics
            WHERE researcher_id = %s
            LIMIT 1
            """,
            (researcher_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE author_role_metrics
                SET
                    first_author_h_index = %s,
                    second_author_h_index = %s,
                    co_author_h_index = %s,
                    corresponding_author_h_index = %s
                WHERE researcher_id = %s
                """,
                (*role_values, researcher_id),
            )

        else:
            conn.execute(
                """
                INSERT INTO author_role_metrics (
                    researcher_id,
                    first_author_h_index,
                    second_author_h_index,
                    co_author_h_index,
                    corresponding_author_h_index
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (researcher_id, *role_values),
            )

        inserted_or_updated += 1

    print(f"Processed: {inserted_or_updated}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("RESEARCHER PROFILE DASHBOARD")
    print("Excel → PostgreSQL Seed")
    print("=" * 70)

    for file in EXCEL_FILES:
        if not file.exists():
            raise FileNotFoundError(
                f"Excel file not found: {file}"
            )

    with psycopg.connect(DATABASE_URL) as conn:

        for excel_file in EXCEL_FILES:
            try:
                seed_file(conn, excel_file)

                # Commit this Excel file separately
                conn.commit()

                print(f"Committed: {excel_file.name}")

            except Exception as error:
                # Roll back the current file if it fails
                conn.rollback()

                print()
                print("=" * 70)
                print(f"FAILED: {excel_file.name}")
                print("=" * 70)
                print(f"Error: {error}")

                raise

    print()
    print("=" * 70)
    print("SEED COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()