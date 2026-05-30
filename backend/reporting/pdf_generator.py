import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path


async def generate_pdf_report(run_data: dict, results: list, output_path: str) -> None:
    try:
        from weasyprint import HTML
    except OSError:
        # Fallback when WeasyPrint system libraries are unavailable (e.g. Windows dev)
        html_path = output_path.replace(".pdf", ".html")
        gap_rows = ""
        for r in results:
            gap_rows += f"<tr><td>{r.get('transaction_id', '—')}</td><td>{r.get('gap_type', '')}</td></tr>"
        content = f"<html><body><h1>Reconciliation Report</h1><p>Run: {run_data.get('run_id')}</p><table>{gap_rows}</table></body></html>"
        Path(html_path).write_text(content, encoding="utf-8")
        Path(output_path).write_bytes(b"%PDF-1.4\n% Fallback PDF - install WeasyPrint GTK deps for full PDF output\n")
        return
    gap_rows = ""
    for r in results:
        gap_rows += f"""
        <tr>
          <td>{r.get('transaction_id', '—')}</td>
          <td>{r.get('platform_amount', 0) / 100:.2f}</td>
          <td>{r.get('bank_amount', 0) / 100:.2f}</td>
          <td>{r.get('monetary_difference', 0) / 100:.2f}</td>
          <td>{r.get('gap_type', '')}</td>
          <td>{r.get('gap_confidence', 0)}</td>
          <td>{r.get('recon_status', '')}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        @page {{ size: A4; margin: 2cm; @bottom-center {{ content: "Page " counter(page) " of " counter(pages); }} }}
        body {{ font-family: sans-serif; font-size: 11px; }}
        h1 {{ font-size: 22px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}
        th {{ background: #f0f0f0; }}
      </style>
    </head>
    <body>
      <h1>Reconciliation Report</h1>
      <p>Run ID: {run_data.get('run_id')}</p>
      <p>Operator: {run_data.get('triggered_by')}</p>
      <p>Generated: {datetime.now(timezone.utc).isoformat()}</p>
      <h2>Executive Summary</h2>
      <table>
        <tr><th>Total Records</th><td>{run_data.get('total_records', 0)}</td></tr>
        <tr><th>Matched</th><td>{run_data.get('matched_count', 0)}</td></tr>
        <tr><th>Flagged</th><td>{run_data.get('flagged_count', 0)}</td></tr>
        <tr><th>Monetary Exposure (INR)</th><td>{run_data.get('total_monetary_exposure_minor_units', 0) / 100:.2f}</td></tr>
      </table>
      <h2>Exception Details</h2>
      <table>
        <tr>
          <th>Transaction ID</th><th>Platform</th><th>Bank</th><th>Diff</th>
          <th>Gap Type</th><th>Confidence</th><th>Status</th>
        </tr>
        {gap_rows}
      </table>
    </body>
    </html>
    """
    HTML(string=html).write_pdf(output_path)


async def generate_csv_report(run_data: dict, results: list, output_path: str) -> None:
    summary_buf = io.StringIO()
    summary_writer = csv.writer(summary_buf)
    summary_writer.writerow(["metric", "value"])
    for key, value in run_data.items():
        summary_writer.writerow([key, value])

    exceptions_buf = io.StringIO()
    if results:
        fieldnames = list(results[0].keys())
        ex_writer = csv.DictWriter(exceptions_buf, fieldnames=fieldnames)
        ex_writer.writeheader()
        ex_writer.writerows(results)
    else:
        exceptions_buf.write("result_id,gap_type,recon_status\n")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("summary.csv", summary_buf.getvalue())
        zf.writestr("exceptions.csv", exceptions_buf.getvalue())
