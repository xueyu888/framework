from project_runtime.aitrans import (
    AitransProject,
    DEFAULT_AITRANS_IMPLEMENTATION_CONFIG_FILE,
    DEFAULT_AITRANS_PRODUCT_SPEC_FILE,
    load_aitrans_project,
    materialize_aitrans_project,
)
from project_runtime.dispatcher import detect_project_template, load_project, materialize_project
from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_FILE,
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_LAYOUT,
    KNOWLEDGE_BASE_PRODUCT_SPEC_LAYOUT,
    KNOWLEDGE_BASE_TEMPLATE_ID,
    KnowledgeBaseProject,
    SeedDocumentSource,
    assert_supported_project_template,
    build_implementation_effect_manifest,
    build_knowledge_base_runtime_app_from_spec,
    compile_knowledge_document_source,
    detect_project_template_id,
    load_knowledge_base_project,
    materialize_knowledge_base_project,
)


# Compatibility aliases while the workspace finishes migrating off the old
# multi-template registry abstraction.
load_registered_project = load_knowledge_base_project
materialize_registered_project = materialize_knowledge_base_project


__all__ = [
    "AitransProject",
    "DEFAULT_AITRANS_IMPLEMENTATION_CONFIG_FILE",
    "DEFAULT_AITRANS_PRODUCT_SPEC_FILE",
    "DEFAULT_KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_FILE",
    "DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE",
    "KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_LAYOUT",
    "KNOWLEDGE_BASE_PRODUCT_SPEC_LAYOUT",
    "KNOWLEDGE_BASE_TEMPLATE_ID",
    "KnowledgeBaseProject",
    "SeedDocumentSource",
    "assert_supported_project_template",
    "build_implementation_effect_manifest",
    "build_knowledge_base_runtime_app_from_spec",
    "compile_knowledge_document_source",
    "detect_project_template_id",
    "load_knowledge_base_project",
    "load_registered_project",
    "materialize_knowledge_base_project",
    "materialize_registered_project",
]
