import json
from pathlib import Path

from app.pipeline.graph import run_pipeline


def main() -> None:
    root = Path(__file__).resolve().parent
    cases_path = root / "input" / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    result = run_pipeline(cases, output_dir=str(root / "output"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
