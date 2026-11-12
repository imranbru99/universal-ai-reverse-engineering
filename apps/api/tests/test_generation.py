from pathlib import Path

from workers.generation.next_fastapi import generate_independent_project


def test_generate_zip(tmp_path: Path):
    zip_path = generate_independent_project(
        tmp_path,
        project_name="Demo Bookstore",
        entities=[
            {
                "name": "Book",
                "description": "Catalog item",
                "fields": [{"name": "title", "data_type": "string", "nullable": False}],
            }
        ],
        states=[{"title": "Catalog", "url": "/catalog", "classification": "OBSERVED"}],
    )
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"
    readme = (tmp_path / "reconstructed-app" / "README.md").read_text(encoding="utf-8")
    assert "Independent Reconstruction" in readme
    assert "INFERRED" in (tmp_path / "reconstructed-app" / "docs" / "PROVENANCE.md").read_text(encoding="utf-8")
