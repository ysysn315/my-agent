from app.rag.metadata_filters import (
    build_base_metadata,
    merge_chunk_metadata,
    matches_metadata_filters,
    normalize_metadata_filters,
)


def test_build_base_metadata_infers_title_and_doc_type():
    metadata = build_base_metadata("cpu_high_usage.md", ingested_at=1711900800)

    assert metadata["source"] == "cpu_high_usage.md"
    assert metadata["title"] == "cpu_high_usage"
    assert metadata["doc_type"] == "markdown"
    assert metadata["ingested_at"] == 1711900800
    assert metadata["timestamp"] == 1711900800


def test_merge_chunk_metadata_builds_markdown_section_path():
    base_metadata = build_base_metadata("ops_guide.md", title="ops_guide", ingested_at=1711900800)
    merged = merge_chunk_metadata(
        base_metadata=base_metadata,
        chunk_metadata={
            "header1": "故障排查",
            "header2": "CPU 过高",
            "header3": "处理步骤",
            "chunk_index": 0,
        },
    )

    assert merged["title"] == "ops_guide"
    assert merged["section_path"] == "故障排查/CPU 过高/处理步骤"


def test_merge_chunk_metadata_keeps_explicit_document_title():
    base_metadata = build_base_metadata("ops_guide.md", title="统一运维手册", ingested_at=1711900800)
    merged = merge_chunk_metadata(
        base_metadata=base_metadata,
        chunk_metadata={
            "header1": "故障排查",
            "header2": "CPU 过高",
        },
    )

    assert merged["title"] == "统一运维手册"
    assert merged["section_path"] == "故障排查/CPU 过高"


def test_normalize_metadata_filters_supports_timestamp_aliases():
    normalized = normalize_metadata_filters(
        {
            "doc_type": "markdown",
            "timestamp_from": "1711900800",
            "timestamp_to": 1711900900,
            "unknown": "ignored",
        }
    )

    assert normalized == {
        "doc_type": "markdown",
        "ingested_at_from": 1711900800,
        "ingested_at_to": 1711900900,
    }


def test_matches_metadata_filters_supports_exact_contains_and_range():
    metadata = {
        "source": "cpu_high_usage.md",
        "title": "CPU 使用率过高排查",
        "doc_type": "markdown",
        "sheet_name": None,
        "section_path": "概述/排查步骤/常见原因",
        "timestamp": 1711900850,
        "ingested_at": 1711900850,
    }

    assert matches_metadata_filters(
        metadata,
        {
            "doc_type": "markdown",
            "timestamp": 1711900850,
            "title_contains": "使用率过高",
            "section_path_contains": "排查步骤",
            "ingested_at_from": 1711900800,
            "ingested_at_to": 1711900900,
        },
    )
    assert not matches_metadata_filters(metadata, {"sheet_name": "Sheet1"})
