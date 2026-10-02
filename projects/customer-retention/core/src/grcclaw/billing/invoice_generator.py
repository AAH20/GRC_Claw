"""
Invoice Generator for GRC_Claw.

Generates professional invoices from billing cycles, with support
for multiple formats, templates, and delivery methods.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from .models import (
    BillingCycle,
    BillingLineItem,
    BillingStatus,
    Invoice,
)


class InvoiceGenerator:
    """
    Generates invoices from billing cycles.

    Supports multiple output formats (JSON, HTML, text), customizable
    templates, and automatic invoice numbering.
    """

    def __init__(self):
        self._invoice_counter = 0
        self._templates: dict[str, str] = {}
        self._company_info = {
            "name": "GRC_Claw Inc.",
            "address": "123 Compliance Way, San Francisco, CA 94105",
            "email": "billing@grcclaw.com",
            "phone": "+1-555-GRC-CLAW",
            "website": "https://grcclaw.com",
            "tax_id": "US-12-3456789",
        }

    def set_company_info(self, info: dict) -> None:
        """Set company information for invoice headers."""
        self._company_info.update(info)

    def register_template(self, name: str, template: str) -> None:
        """Register a custom invoice template."""
        self._templates[name] = template

    def generate_invoice(
        self,
        cycle: BillingCycle,
        tenant_info: dict | None = None,
        due_days: int = 30,
        notes: list[str] | None = None,
        purchase_order: str | None = None,
        template: str | None = None,
    ) -> Invoice:
        """
        Generate an invoice from a billing cycle.

        Args:
            cycle: The billing cycle to invoice.
            tenant_info: Tenant information for the invoice header.
            due_days: Number of days until payment is due.
            notes: Additional notes for the invoice.
            purchase_order: Optional purchase order number.
            template: Optional template name to use.

        Returns:
            A fully populated Invoice object.
        """
        self._invoice_counter += 1

        # Parse dates for due date calculation
        try:
            issue_dt = datetime.fromisoformat(cycle.period_end.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            issue_dt = datetime.now(UTC)

        due_dt = issue_dt + timedelta(days=due_days)

        # Create invoice line items from cycle line items
        invoice_items = []
        for item in cycle.line_items:
            inv_item = BillingLineItem(
                description=item.description,
                dimension=item.dimension,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                discount_pct=item.discount_pct,
                metadata=item.metadata,
            )
            invoice_items.append(inv_item)

        # Build notes
        all_notes = list(cycle.notes)
        if notes:
            all_notes.extend(notes)

        invoice = Invoice(
            invoice_number=f"INV-{datetime.now(UTC).strftime('%Y%m')}-{self._invoice_counter:05d}",
            tenant_id=cycle.tenant_id,
            billing_cycle_id=cycle.cycle_id,
            status=BillingStatus.ISSUED,
            line_items=invoice_items,
            discount_amount=cycle.discount_amount,
            tax_rate=cycle.tax_rate,
            currency=cycle.currency,
            issue_date=issue_dt.isoformat(),
            due_date=due_dt.isoformat(),
            notes=all_notes,
            purchase_order=purchase_order,
        )

        # Copy tenant info into metadata
        if tenant_info:
            invoice.metadata = {"tenant_info": tenant_info}

        # Calculate totals
        invoice.calculate_totals()

        return invoice

    def generate_bulk_invoices(
        self,
        cycles: list[BillingCycle],
        tenant_info_map: dict[str, dict] | None = None,
        due_days: int = 30,
    ) -> list[Invoice]:
        """
        Generate invoices for multiple billing cycles.

        Args:
            cycles: List of billing cycles.
            tenant_info_map: Map of tenant_id to tenant info.
            due_days: Days until payment due.

        Returns:
            List of generated invoices.
        """
        tenant_info_map = tenant_info_map or {}
        invoices = []
        for cycle in cycles:
            tenant_info = tenant_info_map.get(cycle.tenant_id)
            invoice = self.generate_invoice(
                cycle=cycle,
                tenant_info=tenant_info,
                due_days=due_days,
            )
            invoices.append(invoice)
        return invoices

    def render_json(self, invoice: Invoice) -> str:
        """Render an invoice as JSON."""
        data = {
            "invoice_id": invoice.invoice_id,
            "invoice_number": invoice.invoice_number,
            "tenant_id": invoice.tenant_id,
            "status": invoice.status.value,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "currency": invoice.currency,
            "line_items": [
                {
                    "description": li.description,
                    "dimension": li.dimension.value if li.dimension else None,
                    "quantity": li.quantity,
                    "unit": li.unit,
                    "unit_price": li.unit_price,
                    "subtotal": li.subtotal,
                    "discount_pct": li.discount_pct,
                    "discount_amount": li.discount_amount,
                    "total": li.total,
                }
                for li in invoice.line_items
            ],
            "subtotal": invoice.subtotal,
            "discount_amount": invoice.discount_amount,
            "tax_rate": invoice.tax_rate,
            "tax_amount": invoice.tax_amount,
            "total": invoice.total,
            "amount_paid": invoice.amount_paid,
            "amount_due": invoice.amount_due,
            "notes": invoice.notes,
            "terms": invoice.terms,
            "purchase_order": invoice.purchase_order,
            "company": self._company_info,
        }
        return json.dumps(data, indent=2)

    def render_html(self, invoice: Invoice) -> str:
        """Render an invoice as HTML."""
        line_items_html = ""
        for li in invoice.line_items:
            line_items_html += f"""
            <tr>
                <td>{li.description}</td>
                <td>{li.quantity:,.2f}</td>
                <td>{li.unit}</td>
                <td>${li.unit_price:,.4f}</td>
                <td>${li.subtotal:,.2f}</td>
                <td>{li.discount_pct}%</td>
                <td>${li.total:,.2f}</td>
            </tr>"""

        notes_html = ""
        if invoice.notes:
            notes_html = "<div class='notes'><h3>Notes</h3><ul>"
            for note in invoice.notes:
                notes_html += f"<li>{note}</li>"
            notes_html += "</ul></div>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice {invoice.invoice_number}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #333; }}
        .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
        .company-info h1 {{ margin: 0; color: #1a1a2e; }}
        .invoice-meta {{ text-align: right; }}
        .invoice-meta h2 {{ margin: 0; color: #16213e; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .totals {{ margin-top: 20px; text-align: right; }}
        .totals .row {{ display: flex; justify-content: flex-end; gap: 20px; margin: 5px 0; }}
        .totals .label {{ font-weight: 600; min-width: 150px; }}
        .totals .amount {{ min-width: 120px; }}
        .grand-total {{ font-size: 1.2em; font-weight: 700; border-top: 2px solid #333; padding-top: 10px; }}
        .notes {{ margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 4px; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }}
        .status-issued {{ background: #e3f2fd; color: #1565c0; }}
        .status-paid {{ background: #e8f5e9; color: #2e7d32; }}
        .status-overdue {{ background: #ffebee; color: #c62828; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-info">
            <h1>{self._company_info['name']}</h1>
            <p>{self._company_info['address']}</p>
            <p>{self._company_info['email']} | {self._company_info['phone']}</p>
            <p>Tax ID: {self._company_info['tax_id']}</p>
        </div>
        <div class="invoice-meta">
            <h2>INVOICE</h2>
            <p><strong>{invoice.invoice_number}</strong></p>
            <p>Issue Date: {invoice.issue_date[:10]}</p>
            <p>Due Date: {invoice.due_date[:10]}</p>
            <p>Status: <span class="status status-{invoice.status.value}">{invoice.status.value.upper()}</span></p>
            {f'<p>PO: {invoice.purchase_order}</p>' if invoice.purchase_order else ''}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit</th>
                <th>Unit Price</th>
                <th>Subtotal</th>
                <th>Discount</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {line_items_html}
        </tbody>
    </table>

    <div class="totals">
        <div class="row"><span class="label">Subtotal:</span><span class="amount">${invoice.subtotal:,.2f}</span></div>
        <div class="row"><span class="label">Discount:</span><span class="amount">-${invoice.discount_amount:,.2f}</span></div>
        <div class="row"><span class="label">Tax ({invoice.tax_rate}%):</span><span class="amount">${invoice.tax_amount:,.2f}</span></div>
        <div class="row grand-total"><span class="label">Total:</span><span class="amount">${invoice.total:,.2f} {invoice.currency}</span></div>
        <div class="row"><span class="label">Amount Paid:</span><span class="amount">${invoice.amount_paid:,.2f}</span></div>
        <div class="row"><span class="label">Amount Due:</span><span class="amount">${invoice.amount_due:,.2f}</span></div>
    </div>

    {notes_html}

    <div style="margin-top: 40px; text-align: center; color: #999; font-size: 0.85em;">
        <p>Terms: {invoice.terms}</p>
        <p>{self._company_info['website']}</p>
    </div>
</body>
</html>"""
        return html

    def render_text(self, invoice: Invoice) -> str:
        """Render an invoice as plain text."""
        lines = [
            "=" * 70,
            f"  {self._company_info['name']}",
            f"  {self._company_info['address']}",
            f"  {self._company_info['email']}",
            "=" * 70,
            "",
            f"  INVOICE: {invoice.invoice_number}",
            f"  Issue Date: {invoice.issue_date[:10]}",
            f"  Due Date:   {invoice.due_date[:10]}",
            f"  Status:     {invoice.status.value.upper()}",
            "",
            "-" * 70,
            "  LINE ITEMS",
            "-" * 70,
        ]

        for li in invoice.line_items:
            lines.append(f"  {li.description}")
            lines.append(f"    {li.quantity:,.2f} {li.unit} x ${li.unit_price:,.4f} = ${li.total:,.2f}")

        lines.extend([
            "-" * 70,
            f"  Subtotal:        ${invoice.subtotal:>12,.2f}",
            f"  Discount:        ${invoice.discount_amount:>12,.2f}",
            f"  Tax ({invoice.tax_rate}%):     ${invoice.tax_amount:>12,.2f}",
            "=" * 70,
            f"  TOTAL:           ${invoice.total:>12,.2f} {invoice.currency}",
            f"  Amount Paid:     ${invoice.amount_paid:>12,.2f}",
            f"  Amount Due:      ${invoice.amount_due:>12,.2f}",
            "=" * 70,
        ])

        if invoice.notes:
            lines.extend(["", "  NOTES:"])
            for note in invoice.notes:
                lines.append(f"    - {note}")

        lines.extend([
            "",
            f"  Terms: {invoice.terms}",
            f"  {self._company_info['website']}",
        ])

        return "\n".join(lines)

    def render(self, invoice: Invoice, format: str = "json") -> str:
        """
        Render an invoice in the specified format.

        Args:
            invoice: The invoice to render.
            format: Output format - 'json', 'html', or 'text'.

        Returns:
            Rendered invoice string.
        """
        if format == "json":
            return self.render_json(invoice)
        elif format == "html":
            return self.render_html(invoice)
        elif format == "text":
            return self.render_text(invoice)
        else:
            raise ValueError(f"Unsupported format: {format}")
