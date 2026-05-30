import csv
import io
import json
from dataclasses import dataclass

MAX_FILE_SIZE = 100 * 1024 * 1024


@dataclass
class ParseError:
    line_number: int
    message: str
    raw_line: str | None = None


class CSVParser:
    def parse(self, file_bytes: bytes) -> list[dict]:
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError("File exceeds 100MB limit")
        for encoding in ("utf-8", "latin-1"):
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode file")

        sample = text[:4096]
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",|\t")
            delimiter = dialect.delimiter
        except csv.Error:
            if "|" in sample and sample.count("|") > sample.count(","):
                delimiter = "|"
            elif "\t" in sample:
                delimiter = "\t"

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return [dict(row) for row in reader]


class JSONLParser:
    def parse(self, file_bytes: bytes) -> tuple[list[dict], list[ParseError]]:
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError("File exceeds 100MB limit")
        text = file_bytes.decode("utf-8", errors="replace")
        records: list[dict] = []
        errors: list[ParseError] = []
        for i, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(ParseError(line_number=i, message=str(e), raw_line=line[:200]))
        return records, errors


def detect_and_parse(file_bytes: bytes, filename: str) -> tuple[list[dict], list[ParseError]]:
    lower = filename.lower()
    if lower.endswith(".jsonl") or lower.endswith(".ndjson"):
        return JSONLParser().parse(file_bytes)
    if lower.endswith(".csv"):
        return CSVParser().parse(file_bytes), []
    if file_bytes.strip().startswith(b"{"):
        records, errors = JSONLParser().parse(file_bytes)
        if records:
            return records, errors
    return CSVParser().parse(file_bytes), []
