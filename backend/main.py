from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg

from config.settings import DATABASE_URL

from backend.services.openalex import (
    search_authors as search_openalex,
    get_author_works
)

from backend.services.semantic_scholar import (
    search_authors as search_semantic_scholar
)

from backend.services.crossref import (
    search_works as search_crossref
)

from backend.matching.unified_candidates import (
    build_unified_candidates
)

from backend.processing.publication_normalizer import (
    normalize_openalex_work
)


app = FastAPI(
    title="Researcher Profile Dashboard API",
    description="API for researcher profile and publication data",
    version="1.0.0"
)


# --------------------------------
# CORS
# --------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------
# Find researchers in PostgreSQL
# --------------------------------

def find_researchers_in_database(name: str):

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    name,
                    institution,
                    institution_author_id,
                    core_field,
                    openalex_author_id,
                    semantic_scholar_author_id
                FROM researchers
                WHERE name ILIKE %s
                ORDER BY name
                """,
                (f"%{name}%",)
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "institution": row[2],
            "institution_author_id": row[3],
            "core_field": row[4],
            "openalex_author_id": row[5],
            "semantic_scholar_author_id": row[6]
        }
        for row in rows
    ]


# --------------------------------
# Save publication
# --------------------------------

def save_publication_for_researcher(
    researcher_id: int,
    publication: dict
):

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO publications (
                    title,
                    publication_year,
                    publication_date,
                    doi,
                    publication_type,
                    venue,
                    publisher,
                    citation_count,
                    openalex_work_id
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (openalex_work_id)
                DO UPDATE SET
                    updated_at = NOW()
                RETURNING id
                """,
                (
                    publication.get("title"),
                    publication.get("publication_year"),
                    publication.get("publication_date"),
                    publication.get("doi"),
                    publication.get("publication_type"),
                    publication.get("venue"),
                    publication.get("publisher"),
                    publication.get("citation_count"),
                    publication.get("openalex_work_id"),
                )
            )

            publication_id = cur.fetchone()[0]

            # Save publication-author relations
            for author in publication.get("authors", []):

                cur.execute(
                    """
                    SELECT id
                    FROM publication_authors
                    WHERE publication_id = %s
                      AND researcher_id = %s
                      AND author_name = %s
                    """,
                    (
                        publication_id,
                        researcher_id,
                        author.get("name"),
                    )
                )

                existing_author = cur.fetchone()

                if existing_author:
                    continue

                cur.execute(
                    """
                    INSERT INTO publication_authors (
                        publication_id,
                        researcher_id,
                        author_name,
                        author_position,
                        is_corresponding
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        publication_id,
                        researcher_id,
                        author.get("name"),
                        author.get("position"),
                        author.get(
                            "is_corresponding",
                            False
                        ),
                    )
                )

        conn.commit()

    return publication_id


# --------------------------------
# Root
# --------------------------------

@app.get("/")
def root():

    return {
        "message": "Researcher Profile Dashboard API is running"
    }


# --------------------------------
# Health
# --------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# --------------------------------
# Author Search
# --------------------------------

@app.get("/authors/search")
def search_author(name: str):

    # =================================
    # 1. Search PostgreSQL first
    # =================================

    database_results = find_researchers_in_database(name)

    if database_results:

        researcher = database_results[0]

        # =================================
        # 2. Get all stored researcher data
        # =================================

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:

                # ---------------------------------
                # Publication count
                # ---------------------------------

                cur.execute(
                    """
                    SELECT COUNT(DISTINCT p.id)
                    FROM publications p
                    INNER JOIN publication_authors pa
                        ON p.id = pa.publication_id
                    WHERE pa.researcher_id = %s
                    """,
                    (researcher["id"],)
                )

                publication_count = cur.fetchone()[0]

                # ---------------------------------
                # Researcher metrics
                # ---------------------------------

                cur.execute(
                    """
                    SELECT
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
                    FROM researcher_metrics
                    WHERE researcher_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (researcher["id"],)
                )

                metrics_row = cur.fetchone()

                # ---------------------------------
                # Researcher indices
                # ---------------------------------

                cur.execute(
                    """
                    SELECT
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
                    FROM researcher_indices
                    WHERE researcher_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (researcher["id"],)
                )

                indices_row = cur.fetchone()

                # ---------------------------------
                # Author role metrics
                # ---------------------------------

                cur.execute(
                    """
                    SELECT
                        first_author_h_index,
                        second_author_h_index,
                        co_author_h_index,
                        corresponding_author_h_index
                    FROM author_role_metrics
                    WHERE researcher_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (researcher["id"],)
                )

                role_metrics_row = cur.fetchone()

        # =================================
        # 3. Convert metrics to JSON
        # =================================

        researcher_metrics = None

        if metrics_row:

            researcher_metrics = {
                "first_year_of_publication": metrics_row[0],
                "total_papers": metrics_row[1],
                "papers_authors_gt_5": metrics_row[2],
                "first_author_papers": metrics_row[3],
                "corresponding_author_papers": metrics_row[4],
                "first_or_corresponding_papers": metrics_row[5],
                "years_active": metrics_row[6],
                "openalex_h_index": metrics_row[7],
                "openalex_i10_index": metrics_row[8],
                "openalex_total_citations": metrics_row[9],
                "bracket": metrics_row[10],
                "last_retrieved": metrics_row[11]
            }

        # =================================
        # 4. Convert indices to JSON
        # =================================

        researcher_indices = None

        if indices_row:

            researcher_indices = {
                "m_quotient": indices_row[0],
                "hyperindex_m_quotient": indices_row[1],
                "ar_index": indices_row[2],
                "hyperindex_ar_index": indices_row[3],
                "local_h_index": indices_row[4],
                "g_index": indices_row[5],
                "a_index": indices_row[6],
                "r_index": indices_row[7],
                "h2_index": indices_row[8],
                "hg_index": indices_row[9],
                "m_index": indices_row[10],
                "q2_index": indices_row[11],
                "e_index": indices_row[12],
                "hw_index": indices_row[13],
                "sh_index": indices_row[14]
            }

        # =================================
        # 5. Convert author role metrics
        # =================================

        author_role_metrics = None

        if role_metrics_row:

            author_role_metrics = {
                "first_author_h_index": role_metrics_row[0],
                "second_author_h_index": role_metrics_row[1],
                "co_author_h_index": role_metrics_row[2],
                "corresponding_author_h_index": role_metrics_row[3]
            }

        # =================================
        # 6. Return database result
        # =================================

        return {
            "search_name": name,
            "source": "database",
            "researcher": researcher,
            "metrics": researcher_metrics,
            "indices": researcher_indices,
            "author_role_metrics": author_role_metrics,
            "publication_count": publication_count
        }

    # =================================
    # 7. Search OpenAlex
    # =================================

    openalex_data = search_openalex(
        name,
        per_page=100
    )

    # =================================
    # 8. Search Semantic Scholar
    # =================================

    semantic_data = search_semantic_scholar(
        name,
        limit=5
    )

    # =================================
    # 9. Search Crossref
    # =================================

    crossref_data = search_crossref(
        name,
        rows=5
    )

    # =================================
    # 10. Build unified candidates
    # =================================

    candidates = build_unified_candidates(
        name,
        openalex_data,
        semantic_data,
        crossref_data
    )

    return {
        "search_name": name,

        "source_status": {

            "openalex": {
                "results": len(
                    openalex_data.get("results", [])
                ),
                "error": openalex_data.get("error")
            },

            "semantic_scholar": {
                "results": len(
                    semantic_data.get("data", [])
                ),
                "error": semantic_data.get("error")
            },

            "crossref": {
                "results": len(
                    crossref_data.get(
                        "message", {}
                    ).get(
                        "items", []
                    )
                ),
                "error": crossref_data.get("error")
            }
        },

        "candidates": candidates
    }


# --------------------------------
# Researcher Publications
# --------------------------------

@app.get("/authors/{researcher_id}/publications")
def get_researcher_publications(researcher_id: int):

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    p.id,
                    p.title,
                    p.publication_year,
                    p.publication_date,
                    p.doi,
                    p.publication_type,
                    p.venue,
                    p.publisher,
                    p.citation_count,
                    p.openalex_work_id
                FROM publications p
                INNER JOIN publication_authors pa
                    ON p.id = pa.publication_id
                WHERE pa.researcher_id = %s
                ORDER BY p.publication_year DESC, p.id DESC
                """,
                (researcher_id,)
            )

            rows = cur.fetchall()

    publications = [
        {
            "id": row[0],
            "title": row[1],
            "publication_year": row[2],
            "publication_date": row[3],
            "doi": row[4],
            "publication_type": row[5],
            "venue": row[6],
            "publisher": row[7],
            "citation_count": row[8],
            "openalex_work_id": row[9]
        }
        for row in rows
    ]

    return {
        "researcher_id": researcher_id,
        "publication_count": len(publications),
        "publications": publications
    }