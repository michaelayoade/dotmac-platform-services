# DotMac Billing Module - Complete Implementation Guide

## Overview

The DotMac Billing Module is a comprehensive billing system with full multi-tenant support, designed to handle invoices, payments, credit notes, tax calculations, and financial reporting. The module is built with Python/FastAPI on the backend and React/TypeScript on the frontend.

## Key Features

### 1. Multi-Tenant Architecture
- **Complete Tenant Isolation**: All billing data is isolated by `tenant_id`
- **Tenant Resolution**: Supports tenant identification via headers, query params, or request state
- **Database-Level Isolation**: All queries automatically filter by tenant

### 2. Core Billing Components

#### Invoices
- Create, view, update, and void invoices
- Draft and finalized invoice states
- Automatic invoice numbering (INV-2024-000001)
- Line items with tax and discount calculations
- Idempotency support to prevent duplicate creation
- Credit application tracking
- Overdue invoice detection

#### Payments
- Multiple payment method support (card, bank, digital wallet, crypto)
- Payment provider abstraction (Stripe, PayPal, etc.)
- Payment retry logic with exponential backoff
- Refund processing
- Payment method verification (micro-deposits for bank accounts)

#### Credit Notes
- Full and partial refunds
- Adjustments and corrections
- Write-offs and goodwill credits
- Automatic application to invoices
- Customer credit balance tracking

#### Tax System
- Configurable tax rates by location
- Multiple tax types (Sales Tax, VAT, GST, HST)
- Tax exemption management
- Integration with external tax providers (Avalara, TaxJar)

#### Currency Support
- Multi-currency invoicing
- Exchange rate management
- Currency-specific decimal precision
- Automatic currency conversion

## Architecture

### Backend Structure
```
src/dotmac/platform/billing/
├── core/                  # Core models and entities
│   ├── models.py         # Pydantic models
│   ├── entities.py       # SQLAlchemy entities
│   ├── enums.py         # Billing enumerations
│   └── exceptions.py    # Custom exceptions
├── invoicing/           # Invoice management
│   ├── service.py      # Business logic
│   └── router.py       # API endpoints
├── payments/            # Payment processing
├── credit_notes/        # Credit note management
├── tax/                 # Tax calculations
├── currency/            # Currency management
├── settings/            # Configuration
└── reporting/           # Financial reports
```

### Database Schema

#### Key Tables
- `invoices` - Invoice records with tenant isolation
- `invoice_line_items` - Invoice line items
- `payments` - Payment transactions
- `payment_methods` - Customer payment methods
- `credit_notes` - Credit notes and refunds
- `transactions` - Financial transaction ledger
- `customer_credits` - Customer credit balances

All tables include:
- Tenant ID for multi-tenant isolation
- Audit fields (created_at, updated_at, created_by, updated_by)
- Soft delete support where applicable
- Idempotency keys for duplicate prevention

## API Endpoints

### Invoice Management
```
POST   /api/v1/billing/invoices              Create invoice
GET    /api/v1/billing/invoices/{id}         Get invoice
GET    /api/v1/billing/invoices              List invoices
POST   /api/v1/billing/invoices/{id}/finalize    Finalize invoice
POST   /api/v1/billing/invoices/{id}/void        Void invoice
POST   /api/v1/billing/invoices/{id}/mark-paid   Mark as paid
POST   /api/v1/billing/invoices/{id}/apply-credit    Apply credit
```

### Payment Processing
```
POST   /api/v1/billing/payments              Process payment
GET    /api/v1/billing/payments/{id}         Get payment
POST   /api/v1/billing/payments/{id}/refund  Refund payment
```

### Credit Notes
```
POST   /api/v1/billing/credit-notes          Create credit note
GET    /api/v1/billing/credit-notes/{id}     Get credit note
POST   /api/v1/billing/credit-notes/{id}/issue   Issue credit note
POST   /api/v1/billing/credit-notes/{id}/apply   Apply to invoice
POST   /api/v1/billing/credit-notes/{id}/void    Void credit note
```

### Settings & Configuration
```
GET    /api/v1/billing/settings/tax          Get tax settings
PUT    /api/v1/billing/settings/tax          Update tax settings
POST   /api/v1/billing/settings/tax/rates    Create tax rate
GET    /api/v1/billing/settings/invoices     Get invoice settings
PUT    /api/v1/billing/settings/invoices     Update invoice settings
```

## Frontend Components

### Invoice List Component
- Displays invoices with filtering and pagination
- Shows invoice statistics (outstanding, overdue, draft, paid)
- Status chips with color coding
- Action buttons for viewing, sending, downloading
- Responsive design with Material-UI

### Usage Example
```tsx
import InvoiceList from '@/components/billing/InvoiceList';

function BillingDashboard() {
  const tenantId = useTenantContext();

  return (
    <InvoiceList
      tenantId={tenantId}
      onInvoiceSelect={(invoice) => {
        // Handle invoice selection
      }}
    />
  );
}
```

## Security Features

### Idempotency
All create operations support idempotency keys to prevent duplicate transactions:
```python
invoice = await invoice_service.create_invoice(
    tenant_id=tenant_id,
    idempotency_key="unique-key-123",
    # ... other params
)
```

### Tenant Isolation
Every service method requires tenant_id:
```python
invoice = await invoice_service.get_invoice(
    tenant_id=tenant_id,
    invoice_id=invoice_id
)
```

### Audit Trail
All entities track:
- Who created/updated records (created_by, updated_by)
- When changes occurred (created_at, updated_at)
- Soft deletion for data recovery

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dotmac

# Payment Providers
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Tax Providers
AVALARA_API_KEY=...
TAXJAR_API_TOKEN=...

# Currency API
EXCHANGE_RATE_API_KEY=...
```

### Billing Settings
```python
{
    "default_currency": "USD",
    "supported_currencies": ["USD", "EUR", "GBP"],
    "invoice_number_format": "INV-{year}-{sequence:06d}",
    "invoice_due_days": 30,
    "tax_calculation_enabled": true,
    "auto_charge_enabled": false,
    "dunning_enabled": true
}
```

## Testing

### Unit Tests
```bash
# Run billing module tests
pytest tests/billing/ -v

# With coverage
pytest tests/billing/ --cov=src/dotmac/platform/billing --cov-report=term-missing
```

### Test Coverage Areas
- Invoice creation with tenant isolation
- Idempotency key handling
- Payment processing and refunds
- Credit note application
- Tax calculations
- Currency conversions
- Webhook processing

## Migration Guide

### Running Migrations
```bash
# Create billing tables
alembic upgrade billing_001

# Rollback if needed
alembic downgrade -1
```

### Initial Setup
1. Run database migrations
2. Configure payment provider credentials
3. Set up tax rates for your jurisdictions
4. Configure invoice numbering format
5. Set default currency and supported currencies
6. Configure webhook endpoints

## Integration Points

### With Existing Platform Services
- **Auth Service**: User authentication and permissions
- **Tenant Service**: Multi-tenant data isolation
- **User Management**: Customer profiles and contacts
- **Communications**: Invoice delivery and payment notifications
- **Analytics**: Revenue tracking and billing metrics
- **Secrets Management**: Secure storage of API keys

### External Services
- **Payment Processors**: Stripe, PayPal, Square
- **Tax Services**: Avalara, TaxJar
- **Accounting Systems**: QuickBooks, Xero
- **Email Providers**: SendGrid, Mailgun

## Best Practices

### 1. Always Use Idempotency Keys
```python
idempotency_key = f"invoice-{customer_id}-{order_id}"
invoice = await create_invoice(idempotency_key=idempotency_key, ...)
```

### 2. Handle Currency Properly
```python
# Always store amounts in minor units (cents)
amount_cents = int(amount_dollars * 100)

# Display with proper formatting
display_amount = amount_cents / 100
```

### 3. Implement Retry Logic
```python
async def process_payment_with_retry(payment_data):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await process_payment(payment_data)
        except PaymentError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Validate Tax Calculations
```python
# Always validate tax calculations match expected rates
calculated_tax = subtotal * tax_rate
assert abs(calculated_tax - expected_tax) < 0.01  # Allow for rounding
```

## Troubleshooting

### Common Issues

1. **Invoice Number Conflicts**
   - Ensure unique constraints on invoice_number
   - Use database sequences or locks for generation

2. **Payment Processing Failures**
   - Check payment provider API status
   - Verify webhook signatures
   - Review retry logic and timeouts

3. **Tax Calculation Errors**
   - Verify tax rates are current
   - Check address validation
   - Ensure proper exemption handling

4. **Multi-Tenant Data Leaks**
   - Always include tenant_id in queries
   - Test with multiple tenants
   - Audit database queries regularly

## Future Enhancements

### Planned Features
- [ ] Recurring billing automation
- [ ] Usage-based billing
- [ ] Dunning management
- [ ] Advanced reporting dashboards
- [ ] Mobile app support
- [ ] Bulk invoice operations
- [ ] Custom invoice templates
- [ ] Multi-language support
- [ ] Blockchain payment support
- [ ] AI-powered fraud detection

## Support

For issues or questions:
- GitHub Issues: https://github.com/dotmac/platform-services/issues
- Documentation: https://docs.dotmac.io/billing
- API Reference: https://api.dotmac.io/docs

## License

Copyright (c) 2024 DotMac Platform Services. All rights reserved.