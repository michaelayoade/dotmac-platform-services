"""
Billing module exceptions
"""

from dotmac.platform.core.exceptions import DotMacError


class BillingError(DotMacError):
    """Base exception for all billing-related errors"""

    pass


class InvoiceError(BillingError):
    """Base exception for invoice-related errors"""

    pass


class InvoiceNotFoundError(InvoiceError):
    """Invoice not found error"""

    pass


class InvalidInvoiceStatusError(InvoiceError):
    """Invalid invoice status for requested operation"""

    pass


class PaymentError(BillingError):
    """Base exception for payment-related errors"""

    pass


class PaymentNotFoundError(PaymentError):
    """Payment not found error"""

    pass


class PaymentMethodNotFoundError(PaymentError):
    """Payment method not found error"""

    pass


class PaymentProcessingError(PaymentError):
    """Error processing payment"""

    pass


class InsufficientFundsError(PaymentError):
    """Insufficient funds for payment"""

    pass


class CreditNoteError(BillingError):
    """Base exception for credit note-related errors"""

    pass


class CreditNoteNotFoundError(CreditNoteError):
    """Credit note not found error"""

    pass


class InvalidCreditNoteStatusError(CreditNoteError):
    """Invalid credit note status for requested operation"""

    pass


class InsufficientCreditError(CreditNoteError):
    """Insufficient credit amount available"""

    pass


class TaxError(BillingError):
    """Base exception for tax-related errors"""

    pass


class TaxCalculationError(TaxError):
    """Error calculating tax"""

    pass


class TaxRateNotFoundError(TaxError):
    """Tax rate not found for location"""

    pass


class CurrencyError(BillingError):
    """Base exception for currency-related errors"""

    pass


class CurrencyConversionError(CurrencyError):
    """Error converting between currencies"""

    pass


class UnsupportedCurrencyError(CurrencyError):
    """Currency not supported"""

    pass


class ConfigurationError(BillingError):
    """Billing configuration error"""

    pass


class IdempotencyError(BillingError):
    """Idempotency key conflict error"""

    pass