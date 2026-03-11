from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    build_knowledge_base_runtime_app_from_spec,
)

PRODUCT_SPEC_FILE_ENV = "SHELF_PRODUCT_SPEC_FILE"
DEFAULT_PRODUCT_SPEC_FILE = DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE


def build_project_app(product_spec_file: str | Path | None = None) -> FastAPI:
    resolved_file = (
        product_spec_file
        or os.environ.get(PRODUCT_SPEC_FILE_ENV)
        or DEFAULT_PRODUCT_SPEC_FILE
    )
    return build_knowledge_base_runtime_app_from_spec(resolved_file)


app = build_project_app()
