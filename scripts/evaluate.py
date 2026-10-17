import argparse
from pathlib import Path

from stats.config import AppConfig
from stats.elasticsearch_provider import ElasticsearchProvider
from stats.embedding_provider import EmbeddingProvider
from stats.gold_set_builder import GoldSetBuilder
from stats.labels_loader import LabelsLoader
from stats.metric_calculator import MetricCalculator
from stats.query_loader import QueryLoader
from stats.report_writer import ReportWriter
from stats.retrieval_evaluator import RetrievalEvaluator
from stats.search_service import SearchService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--queries", default="eval/queries.jsonl")
    parser.add_argument("--labels", default="eval/labels.jsonl")
    parser.add_argument("--modes", default="keyword,hybrid,oracle")
    parser.add_argument("--cutoffs", default="5,10")
    parser.add_argument("--out-md", default="eval/report.md")
    parser.add_argument("--out-json", default="eval/report.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config: AppConfig = AppConfig()
    provider = ElasticsearchProvider(config)
    embeddings = EmbeddingProvider(config)
    search_service = SearchService(provider, embeddings)
    evaluator = RetrievalEvaluator(
        search_service=search_service,
        embeddings=embeddings,
        gold_builder=GoldSetBuilder(provider),
        metrics=MetricCalculator(),
        cutoffs=[int(value) for value in args.cutoffs.split(",")],
    )
    cases = QueryLoader(Path(args.queries)).load()
    labels = LabelsLoader(Path(args.labels)).load()
    modes = [value.strip() for value in args.modes.split(",") if value.strip()]
    report = evaluator.evaluate(cases, modes, labels)
    writer = ReportWriter(report)
    writer.write(Path(args.out_md), Path(args.out_json))
    print(writer.to_markdown())


if __name__ == "__main__":
    main()
