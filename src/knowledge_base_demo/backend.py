from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import re
from typing import Iterable

from fastapi import APIRouter, HTTPException, Query, status
from framework_core import Base, BoundaryDefinition, BoundaryItem, Capability, VerificationInput, VerificationResult, verify
from project_runtime.knowledge_base import KnowledgeBaseProjectConfig, SeedArticle, load_knowledge_base_project
from pydantic import BaseModel, Field

KNOWLEDGE_BASE_API_CAPABILITIES = (
    Capability("C1", "Provide stable list, detail, and tag query endpoints"),
    Capability("C2", "Provide stable create and optional update write endpoints"),
    Capability("C3", "Accept knowledge workbench contracts with one consistent result surface"),
    Capability("C4", "Exclude storage-engine, indexing, and permission-engine internals"),
)

KNOWLEDGE_BASE_API_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("LIST", "list endpoint supports keyword, tag, status, and pagination"),
        BoundaryItem("DETAIL", "detail endpoint returns body, tags, summary, and related slugs"),
        BoundaryItem("TAGS", "tag endpoint supports filter panel bootstrap"),
        BoundaryItem("WRITE", "write endpoint supports configured write states"),
        BoundaryItem("RESULT", "query and write results use one stable contract surface"),
        BoundaryItem("AUTH", "write actions must keep an explicit authorization strategy"),
        BoundaryItem("TRACE", "request parameters and write outcomes stay observable"),
    )
)

KNOWLEDGE_BASE_API_BASES = (
    Base("B1", "query surface base", "L1.M0[R1,R3]"),
    Base("B2", "write surface base", "L1.M0[R2,R3]"),
    Base("B3", "contract governance base", "L1.M0[R1,R2,R3]"),
)


@dataclass(frozen=True)
class KnowledgeArticleRecord:
    slug: str
    title: str
    summary: str
    body: str
    tags: tuple[str, ...]
    status: str
    updated_at: str
    related_slugs: tuple[str, ...] = ()


class KnowledgeArticleSummary(BaseModel):
    slug: str
    title: str
    summary: str
    tags: list[str]
    status: str
    updated_at: str


class KnowledgeArticleDetail(KnowledgeArticleSummary):
    body: str
    related_slugs: list[str]


class KnowledgeArticleListResponse(BaseModel):
    items: list[KnowledgeArticleSummary]
    total: int
    page: int
    page_size: int


class KnowledgeTagItem(BaseModel):
    name: str
    count: int


class KnowledgeTagListResponse(BaseModel):
    items: list[KnowledgeTagItem]


class KnowledgeArticleWritePayload(BaseModel):
    title: str = Field()
    summary: str = Field()
    body: str = Field()
    tags: list[str] = Field(default_factory=list)
    status: str | None = Field(default=None)


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "knowledge-note"


def _today_iso() -> str:
    return date.today().isoformat()


def _resolve_project_config(project_config: KnowledgeBaseProjectConfig | None) -> KnowledgeBaseProjectConfig:
    return project_config or load_knowledge_base_project()


def _seed_article_to_record(article: SeedArticle) -> KnowledgeArticleRecord:
    return KnowledgeArticleRecord(
        slug=article.slug,
        title=article.title,
        summary=article.summary,
        body=article.body,
        tags=article.tags,
        status=article.status,
        updated_at=article.updated_at,
        related_slugs=article.related_slugs,
    )


def _normalize_tags(raw_tags: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({item.strip().lower() for item in raw_tags if item.strip()}))


def _to_summary(article: KnowledgeArticleRecord) -> KnowledgeArticleSummary:
    return KnowledgeArticleSummary(
        slug=article.slug,
        title=article.title,
        summary=article.summary,
        tags=list(article.tags),
        status=article.status,
        updated_at=article.updated_at,
    )


def _to_detail(article: KnowledgeArticleRecord) -> KnowledgeArticleDetail:
    summary = _to_summary(article)
    return KnowledgeArticleDetail(
        **summary.model_dump(),
        body=article.body,
        related_slugs=list(article.related_slugs),
    )


class KnowledgeRepository:
    def __init__(
        self,
        project_config: KnowledgeBaseProjectConfig | None = None,
        seed: Iterable[KnowledgeArticleRecord] | None = None,
    ) -> None:
        self.project_config = _resolve_project_config(project_config)
        self.constraints = self.project_config.backend_constraint_profile
        default_seed = tuple(_seed_article_to_record(article) for article in self.project_config.seed_articles)
        self._articles = list(seed or default_seed)

    def resolve_write_status(self, raw_status: str | None) -> str:
        normalized = (raw_status or "").strip().lower()
        if normalized:
            return normalized
        return "draft" if self.project_config.composition_profile.supports_draft else "published"

    def list_articles(
        self,
        *,
        keyword: str = "",
        tag: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[KnowledgeArticleRecord], int]:
        keyword_normalized = keyword.strip().lower()
        tag_normalized = tag.strip().lower() if tag else None
        status_normalized = status_filter.strip().lower() if status_filter else None

        filtered = []
        for article in self._articles:
            haystack = " ".join((article.title, article.summary, article.body)).lower()
            if keyword_normalized and keyword_normalized not in haystack:
                continue
            if tag_normalized and tag_normalized not in {item.lower() for item in article.tags}:
                continue
            if status_normalized and article.status != status_normalized:
                continue
            filtered.append(article)

        filtered.sort(key=lambda item: (item.updated_at, item.title), reverse=True)
        total = len(filtered)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return filtered[start:end], total

    def get_article(self, slug: str) -> KnowledgeArticleRecord | None:
        for article in self._articles:
            if article.slug == slug:
                return article
        return None

    def list_tags(self) -> list[KnowledgeTagItem]:
        counts: dict[str, int] = {}
        for article in self._articles:
            for tag in article.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return [KnowledgeTagItem(name=name, count=count) for name, count in sorted(counts.items())]

    def validate_write_payload(self, payload: KnowledgeArticleWritePayload) -> list[str]:
        errors: list[str] = []
        constraints = self.constraints
        resolved_status = self.resolve_write_status(payload.status)
        title = payload.title.strip()
        summary = payload.summary.strip()
        body = payload.body.strip()
        tags = _normalize_tags(payload.tags)

        if not constraints.min_title_length <= len(title) <= constraints.max_title_length:
            errors.append(
                f"title length must be between {constraints.min_title_length} and {constraints.max_title_length}"
            )
        if not constraints.min_summary_length <= len(summary) <= constraints.max_summary_length:
            errors.append(
                f"summary length must be between {constraints.min_summary_length} and {constraints.max_summary_length}"
            )
        if not constraints.min_body_length <= len(body) <= constraints.max_body_length:
            errors.append(
                f"body length must be between {constraints.min_body_length} and {constraints.max_body_length}"
            )
        if len(tags) > constraints.max_tags_per_article:
            errors.append(f"tags must contain at most {constraints.max_tags_per_article} items")
        if resolved_status not in constraints.allowed_statuses:
            errors.append(f"status must be one of {', '.join(constraints.allowed_statuses)}")
        return errors

    def create_article(self, payload: KnowledgeArticleWritePayload) -> KnowledgeArticleRecord:
        resolved_status = self.resolve_write_status(payload.status)
        slug_base = _slugify(payload.title)
        slug = slug_base
        suffix = 2
        while self.get_article(slug) is not None:
            slug = f"{slug_base}-{suffix}"
            suffix += 1

        article = KnowledgeArticleRecord(
            slug=slug,
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            body=payload.body.strip(),
            tags=_normalize_tags(payload.tags),
            status=resolved_status,
            updated_at=_today_iso(),
            related_slugs=tuple(),
        )
        self._articles.insert(0, article)
        return article

    def update_article(
        self,
        slug: str,
        payload: KnowledgeArticleWritePayload,
    ) -> KnowledgeArticleRecord | None:
        resolved_status = self.resolve_write_status(payload.status)
        for index, article in enumerate(self._articles):
            if article.slug != slug:
                continue

            updated = replace(
                article,
                title=payload.title.strip(),
                summary=payload.summary.strip(),
                body=payload.body.strip(),
                tags=_normalize_tags(payload.tags),
                status=resolved_status,
                updated_at=_today_iso(),
            )
            self._articles[index] = updated
            return updated

        return None

def verify_knowledge_base_backend(
    project_config: KnowledgeBaseProjectConfig | None = None,
) -> VerificationResult:
    config = _resolve_project_config(project_config)
    write_surface_pass_criterion = (
        (
            "create and update endpoints accept draft and published writes"
            if config.composition_profile.supports_draft
            else "create and update endpoints accept published writes"
        )
        if config.composition_profile.supports_edit
        else (
            "create endpoint accepts draft and published writes"
            if config.composition_profile.supports_draft
            else "create endpoint accepts published writes"
        )
    )
    boundary_valid, boundary_errors = KNOWLEDGE_BASE_API_BOUNDARY.validate()
    base_result = verify(
        VerificationInput(
            subject="knowledge base backend",
            pass_criteria=[
                "list, detail, and tag endpoints all exist",
                write_surface_pass_criterion,
                "query and write responses keep one stable result structure",
            ],
            evidence={
                "project": config.public_summary(),
                "capabilities": [item.to_dict() for item in KNOWLEDGE_BASE_API_CAPABILITIES],
                "boundary": KNOWLEDGE_BASE_API_BOUNDARY.to_dict(),
                "bases": [item.to_dict() for item in KNOWLEDGE_BASE_API_BASES],
            },
        )
    )
    reasons = [*boundary_errors, *base_result.reasons]
    return VerificationResult(
        passed=boundary_valid and base_result.passed,
        reasons=reasons,
        evidence=base_result.evidence,
    )


def build_knowledge_base_router(
    project_config: KnowledgeBaseProjectConfig | None = None,
    repository: KnowledgeRepository | None = None,
) -> APIRouter:
    config = _resolve_project_config(project_config)
    constraints = config.backend_constraint_profile
    repo = repository or KnowledgeRepository(config)
    router = APIRouter(
        prefix=config.route_boundary_values.api_prefix,
        tags=[config.metadata.project_id],
    )

    @router.get("/articles", response_model=KnowledgeArticleListResponse)
    def list_articles(
        keyword: str = "",
        tag: str | None = None,
        status_filter: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=constraints.default_page_size, ge=1, le=constraints.max_page_size),
    ) -> KnowledgeArticleListResponse:
        if status_filter is not None and status_filter not in constraints.allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"status_filter must be one of {', '.join(constraints.allowed_statuses)}",
            )
        items, total = repo.list_articles(
            keyword=keyword,
            tag=tag,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        return KnowledgeArticleListResponse(
            items=[_to_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @router.get("/articles/{slug}", response_model=KnowledgeArticleDetail)
    def get_article(slug: str) -> KnowledgeArticleDetail:
        article = repo.get_article(slug)
        if article is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        return _to_detail(article)

    @router.get("/tags", response_model=KnowledgeTagListResponse)
    def list_tags() -> KnowledgeTagListResponse:
        return KnowledgeTagListResponse(items=repo.list_tags())

    @router.post("/articles", response_model=KnowledgeArticleDetail, status_code=status.HTTP_201_CREATED)
    def create_article(payload: KnowledgeArticleWritePayload) -> KnowledgeArticleDetail:
        errors = repo.validate_write_payload(payload)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="; ".join(errors),
            )
        article = repo.create_article(payload)
        return _to_detail(article)

    if config.composition_profile.supports_edit:

        @router.put("/articles/{slug}", response_model=KnowledgeArticleDetail)
        def update_article(slug: str, payload: KnowledgeArticleWritePayload) -> KnowledgeArticleDetail:
            errors = repo.validate_write_payload(payload)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="; ".join(errors),
                )
            article = repo.update_article(slug, payload)
            if article is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
            return _to_detail(article)

    return router
