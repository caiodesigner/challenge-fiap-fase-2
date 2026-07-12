import re
from pathlib import Path
from urllib.parse import unquote

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:")
REQUIRED_DELIVERABLES = (
    "Dockerfile",
    "docs/relatorio-tecnico.md",
    "docs/arquitetura.md",
    "docs/api.md",
    "docs/evolucao-codigo-base.md",
    "docs/roteiro-video.md",
    "docs/checklist-entrega.md",
    "docs/indice.md",
    "docs/nuvem.md",
    "infra/terraform/main.tf",
    "infra/terraform/outputs.tf",
    "infra/terraform/variables.tf",
    "infra/terraform/versions.tf",
)


def markdown_files() -> list[Path]:
    files = [PROJECT_ROOT / "README.md", PROJECT_ROOT / "CONTRIBUTING.md"]
    files.extend((PROJECT_ROOT / "data").rglob("*.md"))
    files.extend((PROJECT_ROOT / "docs").rglob("*.md"))
    files.extend((PROJECT_ROOT / "reports").rglob("*.md"))
    return sorted(path for path in files if path.exists())


@pytest.mark.parametrize("relative_path", REQUIRED_DELIVERABLES)
def test_required_deliverable_exists(relative_path: str) -> None:
    assert (PROJECT_ROOT / relative_path).is_file()


def test_local_markdown_links_resolve() -> None:
    broken_links: list[str] = []

    for source in markdown_files():
        content = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(content):
            target = raw_target.strip().strip("<>")
            if target.startswith(EXTERNAL_PREFIXES) or target.startswith("#"):
                continue

            path_part = unquote(target.split("#", maxsplit=1)[0])
            destination = (source.parent / path_part).resolve()
            if not destination.exists():
                source_name = source.relative_to(PROJECT_ROOT)
                broken_links.append(f"{source_name}: {raw_target}")

    assert not broken_links, "Links locais inválidos:\n" + "\n".join(broken_links)
