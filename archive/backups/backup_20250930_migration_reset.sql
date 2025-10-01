--
-- PostgreSQL database dump
--

\restrict qJI1MF59KkTSdEJJpnStYPZIsaDuj6fc965rBIzmZNazORaMMAOwYawqpxDlEna

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: accounttype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.accounttype AS ENUM (
    'CHECKING',
    'SAVINGS',
    'BUSINESS',
    'MONEY_MARKET'
);


ALTER TYPE public.accounttype OWNER TO dotmac_user;

--
-- Name: activitytype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.activitytype AS ENUM (
    'CREATED',
    'UPDATED',
    'STATUS_CHANGED',
    'NOTE_ADDED',
    'TAG_ADDED',
    'TAG_REMOVED',
    'CONTACT_MADE',
    'PURCHASE',
    'SUPPORT_TICKET',
    'LOGIN',
    'EXPORT',
    'IMPORT'
);


ALTER TYPE public.activitytype OWNER TO dotmac_user;

--
-- Name: bankaccountstatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.bankaccountstatus AS ENUM (
    'PENDING',
    'VERIFIED',
    'FAILED',
    'SUSPENDED'
);


ALTER TYPE public.bankaccountstatus OWNER TO dotmac_user;

--
-- Name: bankaccounttype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.bankaccounttype AS ENUM (
    'CHECKING',
    'SAVINGS',
    'BUSINESS_CHECKING',
    'BUSINESS_SAVINGS'
);


ALTER TYPE public.bankaccounttype OWNER TO dotmac_user;

--
-- Name: communicationchannel; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.communicationchannel AS ENUM (
    'EMAIL',
    'SMS',
    'PHONE',
    'IN_APP',
    'PUSH',
    'MAIL'
);


ALTER TYPE public.communicationchannel OWNER TO dotmac_user;

--
-- Name: communicationstatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.communicationstatus AS ENUM (
    'PENDING',
    'SENT',
    'DELIVERED',
    'FAILED',
    'BOUNCED',
    'CANCELLED'
);


ALTER TYPE public.communicationstatus OWNER TO dotmac_user;

--
-- Name: communicationtype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.communicationtype AS ENUM (
    'EMAIL',
    'WEBHOOK',
    'SMS',
    'PUSH'
);


ALTER TYPE public.communicationtype OWNER TO dotmac_user;

--
-- Name: creditapplicationtype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.creditapplicationtype AS ENUM (
    'INVOICE',
    'CUSTOMER_ACCOUNT',
    'REFUND'
);


ALTER TYPE public.creditapplicationtype OWNER TO dotmac_user;

--
-- Name: creditnotestatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.creditnotestatus AS ENUM (
    'DRAFT',
    'ISSUED',
    'APPLIED',
    'VOIDED',
    'PARTIALLY_APPLIED'
);


ALTER TYPE public.creditnotestatus OWNER TO dotmac_user;

--
-- Name: creditreason; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.creditreason AS ENUM (
    'CUSTOMER_REQUEST',
    'BILLING_ERROR',
    'PRODUCT_DEFECT',
    'SERVICE_ISSUE',
    'DUPLICATE_CHARGE',
    'CANCELLATION',
    'GOODWILL',
    'OVERPAYMENT_REFUND',
    'PRICE_ADJUSTMENT',
    'TAX_ADJUSTMENT',
    'OTHER'
);


ALTER TYPE public.creditreason OWNER TO dotmac_user;

--
-- Name: credittype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.credittype AS ENUM (
    'REFUND',
    'ADJUSTMENT',
    'WRITE_OFF',
    'DISCOUNT',
    'ERROR_CORRECTION',
    'OVERPAYMENT',
    'GOODWILL'
);


ALTER TYPE public.credittype OWNER TO dotmac_user;

--
-- Name: customerstatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.customerstatus AS ENUM (
    'PROSPECT',
    'ACTIVE',
    'INACTIVE',
    'SUSPENDED',
    'CHURNED',
    'ARCHIVED'
);


ALTER TYPE public.customerstatus OWNER TO dotmac_user;

--
-- Name: customertier; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.customertier AS ENUM (
    'FREE',
    'BASIC',
    'STANDARD',
    'PREMIUM',
    'ENTERPRISE'
);


ALTER TYPE public.customertier OWNER TO dotmac_user;

--
-- Name: customertype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.customertype AS ENUM (
    'INDIVIDUAL',
    'BUSINESS',
    'ENTERPRISE',
    'PARTNER',
    'VENDOR'
);


ALTER TYPE public.customertype OWNER TO dotmac_user;

--
-- Name: invoicestatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.invoicestatus AS ENUM (
    'DRAFT',
    'OPEN',
    'PAID',
    'VOID',
    'OVERDUE',
    'PARTIALLY_PAID'
);


ALTER TYPE public.invoicestatus OWNER TO dotmac_user;

--
-- Name: paymentmethodstatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.paymentmethodstatus AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'EXPIRED',
    'REQUIRES_VERIFICATION',
    'VERIFICATION_FAILED'
);


ALTER TYPE public.paymentmethodstatus OWNER TO dotmac_user;

--
-- Name: paymentmethodtype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.paymentmethodtype AS ENUM (
    'CARD',
    'BANK_ACCOUNT',
    'DIGITAL_WALLET',
    'CRYPTO',
    'CHECK',
    'WIRE_TRANSFER',
    'CASH'
);


ALTER TYPE public.paymentmethodtype OWNER TO dotmac_user;

--
-- Name: paymentstatus; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.paymentstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'SUCCEEDED',
    'FAILED',
    'REFUNDED',
    'PARTIALLY_REFUNDED',
    'CANCELLED'
);


ALTER TYPE public.paymentstatus OWNER TO dotmac_user;

--
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: dotmac_user
--

CREATE TYPE public.transactiontype AS ENUM (
    'CHARGE',
    'PAYMENT',
    'REFUND',
    'CREDIT',
    'ADJUSTMENT',
    'FEE',
    'WRITE_OFF'
);


ALTER TYPE public.transactiontype OWNER TO dotmac_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_activities; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.audit_activities (
    id uuid NOT NULL,
    activity_type character varying(100) NOT NULL,
    severity character varying(20) NOT NULL,
    user_id character varying(255),
    "timestamp" timestamp with time zone NOT NULL,
    resource_type character varying(100),
    resource_id character varying(255),
    action character varying(100) NOT NULL,
    description text NOT NULL,
    details json,
    ip_address character varying(45),
    user_agent character varying(500),
    request_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255) NOT NULL
);


ALTER TABLE public.audit_activities OWNER TO dotmac_user;

--
-- Name: billing_pricing_rules; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_pricing_rules (
    rule_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    applies_to_product_ids json NOT NULL,
    applies_to_categories json NOT NULL,
    applies_to_all boolean NOT NULL,
    min_quantity numeric(10,0),
    customer_segments json NOT NULL,
    discount_type character varying(20) NOT NULL,
    discount_value numeric(15,2) NOT NULL,
    starts_at timestamp with time zone,
    ends_at timestamp with time zone,
    max_uses numeric(10,0),
    current_uses numeric(10,0) NOT NULL,
    is_active boolean NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.billing_pricing_rules OWNER TO dotmac_user;

--
-- Name: billing_product_categories; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_product_categories (
    category_id character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    default_tax_class character varying(20) NOT NULL,
    sort_order numeric(10,0) NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.billing_product_categories OWNER TO dotmac_user;

--
-- Name: billing_products; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_products (
    product_id character varying(50) NOT NULL,
    sku character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    category character varying(100) NOT NULL,
    product_type character varying(20) NOT NULL,
    base_price numeric(15,2) NOT NULL,
    currency character varying(3) NOT NULL,
    tax_class character varying(20) NOT NULL,
    usage_type character varying(50),
    usage_unit_name character varying(50),
    is_active boolean NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.billing_products OWNER TO dotmac_user;

--
-- Name: billing_rule_usage; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_rule_usage (
    usage_id character varying(50) NOT NULL,
    rule_id character varying(50) NOT NULL,
    customer_id character varying(50) NOT NULL,
    invoice_id character varying(50),
    used_at timestamp with time zone NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.billing_rule_usage OWNER TO dotmac_user;

--
-- Name: billing_subscription_events; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_subscription_events (
    event_id character varying(50) NOT NULL,
    subscription_id character varying(50) NOT NULL,
    event_type character varying(50) NOT NULL,
    event_data json NOT NULL,
    user_id character varying(50),
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.billing_subscription_events OWNER TO dotmac_user;

--
-- Name: billing_subscription_plans; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_subscription_plans (
    plan_id character varying(50) NOT NULL,
    product_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    billing_cycle character varying(20) NOT NULL,
    price numeric(15,2) NOT NULL,
    currency character varying(3) NOT NULL,
    setup_fee numeric(15,2),
    trial_days numeric(10,0),
    included_usage json NOT NULL,
    overage_rates json NOT NULL,
    is_active boolean NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.billing_subscription_plans OWNER TO dotmac_user;

--
-- Name: billing_subscriptions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.billing_subscriptions (
    subscription_id character varying(50) NOT NULL,
    customer_id character varying(50) NOT NULL,
    plan_id character varying(50) NOT NULL,
    current_period_start timestamp with time zone NOT NULL,
    current_period_end timestamp with time zone NOT NULL,
    status character varying(20) NOT NULL,
    trial_end timestamp with time zone,
    cancel_at_period_end boolean NOT NULL,
    canceled_at timestamp with time zone,
    custom_price numeric(15,2),
    usage_records json NOT NULL,
    tenant_id character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    metadata json NOT NULL,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.billing_subscriptions OWNER TO dotmac_user;

--
-- Name: cash_reconciliations; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.cash_reconciliations (
    id character varying(36) NOT NULL,
    register_id character varying(50) NOT NULL,
    reconciliation_date timestamp with time zone NOT NULL,
    opening_float numeric(19,4) NOT NULL,
    closing_float numeric(19,4) NOT NULL,
    expected_cash numeric(19,4) NOT NULL,
    actual_cash numeric(19,4) NOT NULL,
    discrepancy numeric(19,4) NOT NULL,
    reconciled_by character varying(255) NOT NULL,
    notes text,
    shift_id character varying(50),
    meta_data json NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.cash_reconciliations OWNER TO dotmac_user;

--
-- Name: cash_registers; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.cash_registers (
    id integer NOT NULL,
    register_id character varying(50) NOT NULL,
    register_name character varying(100) NOT NULL,
    location character varying(200),
    initial_float numeric(19,4) NOT NULL,
    current_float numeric(19,4) NOT NULL,
    max_cash_limit numeric(19,4),
    is_active boolean NOT NULL,
    requires_daily_reconciliation boolean NOT NULL,
    last_reconciled timestamp with time zone,
    created_by character varying(255) NOT NULL,
    updated_by character varying(255),
    meta_data json NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying(255)
);


ALTER TABLE public.cash_registers OWNER TO dotmac_user;

--
-- Name: cash_registers_id_seq; Type: SEQUENCE; Schema: public; Owner: dotmac_user
--

CREATE SEQUENCE public.cash_registers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cash_registers_id_seq OWNER TO dotmac_user;

--
-- Name: cash_registers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dotmac_user
--

ALTER SEQUENCE public.cash_registers_id_seq OWNED BY public.cash_registers.id;


--
-- Name: cash_transactions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.cash_transactions (
    id character varying(36) NOT NULL,
    register_id character varying(50) NOT NULL,
    transaction_type character varying(50) NOT NULL,
    amount numeric(19,4) NOT NULL,
    balance_after numeric(19,4) NOT NULL,
    reference character varying(100),
    description character varying(500),
    created_by character varying(255) NOT NULL,
    meta_data json NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.cash_transactions OWNER TO dotmac_user;

--
-- Name: communication_logs; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.communication_logs (
    id uuid NOT NULL,
    type public.communicationtype NOT NULL,
    recipient character varying(500) NOT NULL,
    sender character varying(500),
    subject character varying(500),
    text_body text,
    html_body text,
    status public.communicationstatus NOT NULL,
    sent_at timestamp without time zone,
    delivered_at timestamp without time zone,
    failed_at timestamp without time zone,
    error_message text,
    retry_count integer NOT NULL,
    provider character varying(100),
    provider_message_id character varying(500),
    template_id character varying(255),
    template_name character varying(255),
    user_id uuid,
    job_id character varying(255),
    metadata json NOT NULL,
    headers json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.communication_logs OWNER TO dotmac_user;

--
-- Name: communication_stats; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.communication_stats (
    id uuid NOT NULL,
    stats_date timestamp without time zone NOT NULL,
    type public.communicationtype NOT NULL,
    total_sent integer NOT NULL,
    total_delivered integer NOT NULL,
    total_failed integer NOT NULL,
    total_bounced integer NOT NULL,
    total_pending integer NOT NULL,
    avg_delivery_time_seconds double precision,
    metadata json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.communication_stats OWNER TO dotmac_user;

--
-- Name: communication_templates; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.communication_templates (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    type public.communicationtype NOT NULL,
    subject_template text,
    text_template text,
    html_template text,
    variables json NOT NULL,
    required_variables json NOT NULL,
    is_active boolean NOT NULL,
    is_default boolean NOT NULL,
    usage_count integer NOT NULL,
    last_used_at timestamp without time zone,
    metadata json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.communication_templates OWNER TO dotmac_user;

--
-- Name: company_bank_accounts; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.company_bank_accounts (
    id integer NOT NULL,
    account_name character varying(200) NOT NULL,
    account_nickname character varying(100),
    bank_name character varying(200) NOT NULL,
    bank_address text,
    bank_country character varying(2) NOT NULL,
    account_number_encrypted text NOT NULL,
    account_number_last_four character varying(4) NOT NULL,
    routing_number character varying(50),
    swift_code character varying(11),
    iban character varying(34),
    account_type public.accounttype NOT NULL,
    currency character varying(3) NOT NULL,
    status public.bankaccountstatus NOT NULL,
    is_primary boolean NOT NULL,
    is_active boolean NOT NULL,
    accepts_deposits boolean NOT NULL,
    verified_at timestamp with time zone,
    verified_by character varying(255),
    verification_notes text,
    notes text,
    meta_data json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.company_bank_accounts OWNER TO dotmac_user;

--
-- Name: company_bank_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: dotmac_user
--

CREATE SEQUENCE public.company_bank_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.company_bank_accounts_id_seq OWNER TO dotmac_user;

--
-- Name: company_bank_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dotmac_user
--

ALTER SEQUENCE public.company_bank_accounts_id_seq OWNED BY public.company_bank_accounts.id;


--
-- Name: contact_activities; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contact_activities (
    id uuid NOT NULL,
    contact_id uuid NOT NULL,
    activity_type character varying(50) NOT NULL,
    subject character varying(255) NOT NULL,
    description text,
    activity_date timestamp with time zone NOT NULL,
    duration_minutes integer,
    status character varying(50) NOT NULL,
    outcome character varying(100),
    performed_by uuid NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.contact_activities OWNER TO dotmac_user;

--
-- Name: contact_field_definitions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contact_field_definitions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    field_key character varying(100) NOT NULL,
    description text,
    field_type character varying(50) NOT NULL,
    is_required boolean NOT NULL,
    is_unique boolean NOT NULL,
    is_searchable boolean NOT NULL,
    default_value json,
    validation_rules json,
    options json,
    display_order integer NOT NULL,
    placeholder character varying(255),
    help_text text,
    field_group character varying(100),
    is_visible boolean NOT NULL,
    is_editable boolean NOT NULL,
    required_permission character varying(100),
    is_system boolean NOT NULL,
    is_encrypted boolean NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid
);


ALTER TABLE public.contact_field_definitions OWNER TO dotmac_user;

--
-- Name: contact_label_definitions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contact_label_definitions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    color character varying(7),
    icon character varying(50),
    category character varying(50),
    display_order integer NOT NULL,
    is_visible boolean NOT NULL,
    is_system boolean NOT NULL,
    is_default boolean NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid
);


ALTER TABLE public.contact_label_definitions OWNER TO dotmac_user;

--
-- Name: contact_methods; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contact_methods (
    id uuid NOT NULL,
    contact_id uuid NOT NULL,
    type character varying(50) NOT NULL,
    value character varying(500) NOT NULL,
    label character varying(50),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    state_province character varying(100),
    postal_code character varying(20),
    country character varying(2),
    is_primary boolean NOT NULL,
    is_verified boolean NOT NULL,
    is_public boolean NOT NULL,
    verified_at timestamp with time zone,
    verified_by uuid,
    verification_token character varying(255),
    display_order integer NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.contact_methods OWNER TO dotmac_user;

--
-- Name: contact_to_labels; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contact_to_labels (
    contact_id uuid NOT NULL,
    label_definition_id uuid NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    assigned_by uuid
);


ALTER TABLE public.contact_to_labels OWNER TO dotmac_user;

--
-- Name: contacts; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.contacts (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    customer_id uuid,
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    display_name character varying(255) NOT NULL,
    prefix character varying(20),
    suffix character varying(20),
    company character varying(255),
    job_title character varying(255),
    department character varying(255),
    status character varying(50) NOT NULL,
    stage character varying(50) NOT NULL,
    owner_id uuid,
    notes text,
    tags json,
    custom_fields jsonb,
    metadata jsonb,
    birthday timestamp with time zone,
    anniversary timestamp with time zone,
    is_primary boolean NOT NULL,
    is_decision_maker boolean NOT NULL,
    is_billing_contact boolean NOT NULL,
    is_technical_contact boolean NOT NULL,
    is_verified boolean NOT NULL,
    preferred_contact_method character varying(50),
    preferred_language character varying(10),
    timezone character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_contacted_at timestamp with time zone,
    deleted_at timestamp with time zone,
    deleted_by uuid,
    CONSTRAINT check_display_name_not_empty CHECK (((display_name IS NOT NULL) AND ((display_name)::text <> ''::text)))
);


ALTER TABLE public.contacts OWNER TO dotmac_user;

--
-- Name: credit_applications; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.credit_applications (
    application_id uuid NOT NULL,
    credit_note_id uuid NOT NULL,
    applied_to_type public.creditapplicationtype NOT NULL,
    applied_to_id character varying(255) NOT NULL,
    applied_amount integer NOT NULL,
    application_date timestamp with time zone NOT NULL,
    applied_by character varying(255) NOT NULL,
    notes character varying(500),
    extra_data json NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.credit_applications OWNER TO dotmac_user;

--
-- Name: credit_note_line_items; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.credit_note_line_items (
    line_item_id uuid NOT NULL,
    credit_note_id uuid NOT NULL,
    description character varying(500) NOT NULL,
    quantity integer NOT NULL,
    unit_price integer NOT NULL,
    total_price integer NOT NULL,
    original_invoice_line_item_id uuid,
    product_id character varying(255),
    tax_rate double precision NOT NULL,
    tax_amount integer NOT NULL,
    extra_data json NOT NULL
);


ALTER TABLE public.credit_note_line_items OWNER TO dotmac_user;

--
-- Name: credit_notes; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.credit_notes (
    credit_note_id uuid NOT NULL,
    credit_note_number character varying(50),
    idempotency_key character varying(255),
    customer_id character varying(255) NOT NULL,
    invoice_id uuid,
    issue_date timestamp with time zone NOT NULL,
    currency character varying(3) NOT NULL,
    subtotal integer NOT NULL,
    tax_amount integer NOT NULL,
    total_amount integer NOT NULL,
    credit_type public.credittype NOT NULL,
    reason public.creditreason NOT NULL,
    reason_description character varying(500),
    status public.creditnotestatus NOT NULL,
    auto_apply_to_invoice boolean NOT NULL,
    remaining_credit_amount integer NOT NULL,
    notes text,
    internal_notes text,
    extra_data json NOT NULL,
    voided_at timestamp with time zone,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.credit_notes OWNER TO dotmac_user;

--
-- Name: customer_activities; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customer_activities (
    id uuid NOT NULL,
    customer_id uuid NOT NULL,
    activity_type public.activitytype NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    metadata json NOT NULL,
    performed_by uuid,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.customer_activities OWNER TO dotmac_user;

--
-- Name: customer_credits; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customer_credits (
    customer_id character varying(255) NOT NULL,
    tenant_id character varying(255) NOT NULL,
    total_credit_amount integer NOT NULL,
    currency character varying(3) NOT NULL,
    credit_notes json NOT NULL,
    auto_apply_to_new_invoices boolean NOT NULL,
    extra_data json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.customer_credits OWNER TO dotmac_user;

--
-- Name: customer_notes; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customer_notes (
    id uuid NOT NULL,
    customer_id uuid NOT NULL,
    subject character varying(200) NOT NULL,
    content text NOT NULL,
    is_internal boolean NOT NULL,
    created_by_id uuid,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255),
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.customer_notes OWNER TO dotmac_user;

--
-- Name: COLUMN customer_notes.is_internal; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customer_notes.is_internal IS 'Internal note vs customer visible';


--
-- Name: customer_segments; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customer_segments (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    criteria json NOT NULL,
    is_dynamic boolean NOT NULL,
    priority integer NOT NULL,
    member_count integer NOT NULL,
    last_calculated timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255),
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.customer_segments OWNER TO dotmac_user;

--
-- Name: COLUMN customer_segments.criteria; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customer_segments.criteria IS 'Segmentation criteria/rules';


--
-- Name: COLUMN customer_segments.is_dynamic; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customer_segments.is_dynamic IS 'Auto-update membership';


--
-- Name: customer_tags_association; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customer_tags_association (
    id uuid NOT NULL,
    customer_id uuid NOT NULL,
    tag_name character varying(50) NOT NULL,
    tag_category character varying(50),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.customer_tags_association OWNER TO dotmac_user;

--
-- Name: customers; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.customers (
    id uuid NOT NULL,
    customer_number character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    middle_name character varying(100),
    display_name character varying(200),
    company_name character varying(200),
    status public.customerstatus NOT NULL,
    customer_type public.customertype NOT NULL,
    tier public.customertier NOT NULL,
    email character varying(255) NOT NULL,
    email_verified boolean NOT NULL,
    phone character varying(30),
    phone_verified boolean NOT NULL,
    mobile character varying(30),
    address_line1 character varying(200),
    address_line2 character varying(200),
    city character varying(100),
    state_province character varying(100),
    postal_code character varying(20),
    country character varying(2),
    tax_id character varying(50),
    vat_number character varying(50),
    industry character varying(100),
    employee_count integer,
    annual_revenue numeric(15,2),
    preferred_channel public.communicationchannel NOT NULL,
    preferred_language character varying(10) NOT NULL,
    timezone character varying(50) NOT NULL,
    opt_in_marketing boolean NOT NULL,
    opt_in_updates boolean NOT NULL,
    user_id uuid,
    assigned_to uuid,
    segment_id uuid,
    lifetime_value numeric(15,2) NOT NULL,
    total_purchases integer NOT NULL,
    last_purchase_date timestamp with time zone,
    first_purchase_date timestamp with time zone,
    average_order_value numeric(15,2) NOT NULL,
    credit_score integer,
    risk_score integer NOT NULL,
    satisfaction_score integer,
    net_promoter_score integer,
    acquisition_date timestamp with time zone NOT NULL,
    last_contact_date timestamp with time zone,
    birthday timestamp without time zone,
    metadata json NOT NULL,
    custom_fields json NOT NULL,
    tags json NOT NULL,
    external_id character varying(100),
    source_system character varying(50),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255),
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.customers OWNER TO dotmac_user;

--
-- Name: COLUMN customers.customer_number; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customers.customer_number IS 'Unique customer identifier for business operations';


--
-- Name: COLUMN customers.user_id; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customers.user_id IS 'Link to auth user account';


--
-- Name: COLUMN customers.assigned_to; Type: COMMENT; Schema: public; Owner: dotmac_user
--

COMMENT ON COLUMN public.customers.assigned_to IS 'Assigned account manager or support agent';


--
-- Name: invoice_line_items; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.invoice_line_items (
    line_item_id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    description character varying(500) NOT NULL,
    quantity integer NOT NULL,
    unit_price integer NOT NULL,
    total_price integer NOT NULL,
    product_id character varying(255),
    subscription_id character varying(255),
    tax_rate double precision NOT NULL,
    tax_amount integer NOT NULL,
    discount_percentage double precision NOT NULL,
    discount_amount integer NOT NULL,
    extra_data json NOT NULL
);


ALTER TABLE public.invoice_line_items OWNER TO dotmac_user;

--
-- Name: invoices; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.invoices (
    invoice_id uuid NOT NULL,
    invoice_number character varying(50),
    idempotency_key character varying(255),
    customer_id character varying(255) NOT NULL,
    billing_email character varying(255) NOT NULL,
    billing_address json NOT NULL,
    issue_date timestamp with time zone NOT NULL,
    due_date timestamp with time zone NOT NULL,
    currency character varying(3) NOT NULL,
    subtotal integer NOT NULL,
    tax_amount integer NOT NULL,
    discount_amount integer NOT NULL,
    total_amount integer NOT NULL,
    total_credits_applied integer NOT NULL,
    remaining_balance integer NOT NULL,
    credit_applications json NOT NULL,
    status public.invoicestatus NOT NULL,
    payment_status public.paymentstatus NOT NULL,
    subscription_id character varying(255),
    proforma_invoice_id character varying(255),
    notes text,
    internal_notes text,
    extra_data json NOT NULL,
    paid_at timestamp with time zone,
    voided_at timestamp with time zone,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.invoices OWNER TO dotmac_user;

--
-- Name: manual_payments; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.manual_payments (
    id integer NOT NULL,
    payment_reference character varying(100) NOT NULL,
    external_reference character varying(255),
    customer_id uuid NOT NULL,
    invoice_id character varying(255),
    bank_account_id integer,
    payment_method public.paymentmethodtype NOT NULL,
    amount numeric(10,2) NOT NULL,
    currency character varying(3) NOT NULL,
    payment_date timestamp with time zone NOT NULL,
    received_date timestamp with time zone,
    cleared_date timestamp with time zone,
    cash_register_id character varying(50),
    cashier_name character varying(100),
    check_number character varying(50),
    check_bank_name character varying(200),
    sender_name character varying(200),
    sender_bank character varying(200),
    sender_account_last_four character varying(4),
    mobile_number character varying(20),
    mobile_provider character varying(50),
    status character varying(20) NOT NULL,
    reconciled boolean NOT NULL,
    reconciled_at timestamp with time zone,
    reconciled_by character varying(255),
    notes text,
    receipt_url character varying(500),
    attachments json NOT NULL,
    recorded_by character varying(255) NOT NULL,
    approved_by character varying(255),
    approved_at timestamp with time zone,
    meta_data json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.manual_payments OWNER TO dotmac_user;

--
-- Name: manual_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: dotmac_user
--

CREATE SEQUENCE public.manual_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.manual_payments_id_seq OWNER TO dotmac_user;

--
-- Name: manual_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dotmac_user
--

ALTER SEQUENCE public.manual_payments_id_seq OWNED BY public.manual_payments.id;


--
-- Name: payment_invoices; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.payment_invoices (
    payment_id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    amount_applied integer NOT NULL,
    applied_at timestamp with time zone NOT NULL
);


ALTER TABLE public.payment_invoices OWNER TO dotmac_user;

--
-- Name: payment_methods; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.payment_methods (
    payment_method_id uuid NOT NULL,
    customer_id character varying(255) NOT NULL,
    type public.paymentmethodtype NOT NULL,
    status public.paymentmethodstatus NOT NULL,
    provider character varying(50) NOT NULL,
    provider_payment_method_id character varying(255) NOT NULL,
    display_name character varying(100) NOT NULL,
    last_four character varying(4),
    brand character varying(50),
    expiry_month integer,
    expiry_year integer,
    bank_name character varying(100),
    account_type public.bankaccounttype,
    routing_number_last_four character varying(4),
    is_default boolean NOT NULL,
    auto_pay_enabled boolean NOT NULL,
    verified_at timestamp with time zone,
    extra_data json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.payment_methods OWNER TO dotmac_user;

--
-- Name: payment_reconciliations; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.payment_reconciliations (
    id integer NOT NULL,
    reconciliation_date timestamp with time zone NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    bank_account_id integer NOT NULL,
    opening_balance numeric(10,2) NOT NULL,
    closing_balance numeric(10,2) NOT NULL,
    statement_balance numeric(10,2) NOT NULL,
    total_deposits numeric(10,2) NOT NULL,
    total_withdrawals numeric(10,2) NOT NULL,
    unreconciled_count integer NOT NULL,
    discrepancy_amount numeric(10,2) NOT NULL,
    status character varying(20) NOT NULL,
    completed_by character varying(255),
    completed_at timestamp with time zone,
    approved_by character varying(255),
    approved_at timestamp with time zone,
    notes text,
    statement_file_url character varying(500),
    reconciled_items json NOT NULL,
    meta_data json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.payment_reconciliations OWNER TO dotmac_user;

--
-- Name: payment_reconciliations_id_seq; Type: SEQUENCE; Schema: public; Owner: dotmac_user
--

CREATE SEQUENCE public.payment_reconciliations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.payment_reconciliations_id_seq OWNER TO dotmac_user;

--
-- Name: payment_reconciliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dotmac_user
--

ALTER SEQUENCE public.payment_reconciliations_id_seq OWNED BY public.payment_reconciliations.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.payments (
    payment_id uuid NOT NULL,
    idempotency_key character varying(255),
    amount integer NOT NULL,
    currency character varying(3) NOT NULL,
    customer_id character varying(255) NOT NULL,
    status public.paymentstatus NOT NULL,
    payment_method_type public.paymentmethodtype NOT NULL,
    payment_method_details json NOT NULL,
    provider character varying(50) NOT NULL,
    provider_payment_id character varying(255),
    provider_fee integer,
    failure_reason character varying(500),
    retry_count integer NOT NULL,
    next_retry_at timestamp with time zone,
    processed_at timestamp with time zone,
    extra_data json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.payments OWNER TO dotmac_user;

--
-- Name: permission_grants; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.permission_grants (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid,
    permission_id uuid,
    action character varying(20) NOT NULL,
    granted_by uuid NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone,
    metadata json
);


ALTER TABLE public.permission_grants OWNER TO dotmac_user;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.permissions (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    category character varying(50) NOT NULL,
    parent_id uuid,
    is_active boolean NOT NULL,
    is_system boolean NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.permissions OWNER TO dotmac_user;

--
-- Name: role_hierarchy; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.role_hierarchy (
    id uuid NOT NULL,
    parent_role_id uuid NOT NULL,
    child_role_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.role_hierarchy OWNER TO dotmac_user;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.role_permissions (
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO dotmac_user;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    parent_id uuid,
    priority integer NOT NULL,
    is_active boolean NOT NULL,
    is_system boolean NOT NULL,
    is_default boolean NOT NULL,
    max_users integer,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.roles OWNER TO dotmac_user;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.transactions (
    transaction_id uuid NOT NULL,
    amount integer NOT NULL,
    currency character varying(3) NOT NULL,
    transaction_type public.transactiontype NOT NULL,
    description character varying(500) NOT NULL,
    customer_id character varying(255) NOT NULL,
    invoice_id uuid,
    payment_id uuid,
    credit_note_id uuid,
    transaction_date timestamp with time zone NOT NULL,
    extra_data json NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.transactions OWNER TO dotmac_user;

--
-- Name: user_permissions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.user_permissions (
    user_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    granted boolean NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    granted_by uuid,
    expires_at timestamp with time zone,
    reason text
);


ALTER TABLE public.user_permissions OWNER TO dotmac_user;

--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    granted_by uuid,
    expires_at timestamp with time zone,
    metadata json
);


ALTER TABLE public.user_roles OWNER TO dotmac_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    full_name character varying(255),
    phone_number character varying(20),
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    is_superuser boolean NOT NULL,
    roles json NOT NULL,
    permissions json NOT NULL,
    mfa_enabled boolean NOT NULL,
    mfa_secret character varying(255),
    last_login timestamp without time zone,
    last_login_ip character varying(45),
    failed_login_attempts integer NOT NULL,
    locked_until timestamp without time zone,
    metadata json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying(255)
);


ALTER TABLE public.users OWNER TO dotmac_user;

--
-- Name: webhook_deliveries; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.webhook_deliveries (
    id uuid NOT NULL,
    subscription_id uuid NOT NULL,
    event_type character varying(255) NOT NULL,
    event_id character varying(255) NOT NULL,
    event_data json NOT NULL,
    status character varying(50) NOT NULL,
    response_code integer,
    response_body text,
    error_message text,
    attempt_number integer NOT NULL,
    next_retry_at timestamp without time zone,
    duration_ms integer,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.webhook_deliveries OWNER TO dotmac_user;

--
-- Name: webhook_subscriptions; Type: TABLE; Schema: public; Owner: dotmac_user
--

CREATE TABLE public.webhook_subscriptions (
    id uuid NOT NULL,
    url character varying(2048) NOT NULL,
    description character varying(500),
    events json NOT NULL,
    secret character varying(255) NOT NULL,
    headers json NOT NULL,
    is_active boolean NOT NULL,
    retry_enabled boolean NOT NULL,
    max_retries integer NOT NULL,
    timeout_seconds integer NOT NULL,
    success_count integer NOT NULL,
    failure_count integer NOT NULL,
    last_triggered_at timestamp without time zone,
    last_success_at timestamp without time zone,
    last_failure_at timestamp without time zone,
    custom_metadata json NOT NULL,
    tenant_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.webhook_subscriptions OWNER TO dotmac_user;

--
-- Name: cash_registers id; Type: DEFAULT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_registers ALTER COLUMN id SET DEFAULT nextval('public.cash_registers_id_seq'::regclass);


--
-- Name: company_bank_accounts id; Type: DEFAULT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.company_bank_accounts ALTER COLUMN id SET DEFAULT nextval('public.company_bank_accounts_id_seq'::regclass);


--
-- Name: manual_payments id; Type: DEFAULT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.manual_payments ALTER COLUMN id SET DEFAULT nextval('public.manual_payments_id_seq'::regclass);


--
-- Name: payment_reconciliations id; Type: DEFAULT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_reconciliations ALTER COLUMN id SET DEFAULT nextval('public.payment_reconciliations_id_seq'::regclass);


--
-- Data for Name: audit_activities; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.audit_activities (id, activity_type, severity, user_id, "timestamp", resource_type, resource_id, action, description, details, ip_address, user_agent, request_id, created_at, updated_at, tenant_id) FROM stdin;
ef8752a7-504f-4f13-a680-70f03e81a308	user.login	low	ede5c137-8d6d-431f-bef1-91047dcd220c	2025-09-28 19:56:11.448664+00	\N	\N	login_success	User test logged in successfully (cookie-auth)	{"username": "test", "email": "test@example.com", "roles": [], "auth_method": "cookie"}	127.0.0.1	curl/8.7.1	\N	2025-09-28 19:56:11.448672+00	2025-09-28 19:56:11.448673+00	default
190ef6a7-c141-484d-a262-84c0352279c9	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:21:35.259933+00	\N	\N	login_success	User admin logged in successfully (cookie-auth)	{"username": "admin", "email": "admin@example.com", "roles": [], "auth_method": "cookie"}	::1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N	2025-09-28 21:21:35.25994+00	2025-09-28 21:21:35.259941+00	default
37084105-017a-4bd1-aafe-4e429d93fc32	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:28:02.313003+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": []}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:28:02.313316+00	2025-09-28 21:28:02.313317+00	default
1f8ad7e5-de00-40ac-8cb6-3961207717d7	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:30:55.839942+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": []}	::1	curl/8.7.1	\N	2025-09-28 21:30:55.839952+00	2025-09-28 21:30:55.839953+00	default
3951b616-8315-4da0-ba9a-47e967463751	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:33:13.30144+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:33:13.301449+00	2025-09-28 21:33:13.30145+00	default
373836b0-c4a9-46c3-b310-23bc6244ba1e	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:33:26.144391+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:33:26.144398+00	2025-09-28 21:33:26.144399+00	default
e810c508-131b-43f1-a801-a6b94597927b	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:34:05.027827+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:34:05.027845+00	2025-09-28 21:34:05.027846+00	default
ebe3a37c-5bab-442e-8197-4b227526c58e	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:34:14.694523+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:34:14.694541+00	2025-09-28 21:34:14.69455+00	default
255c786b-86c7-49d9-bbfb-b76bda4f817f	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:34:37.915078+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-28 21:34:37.915286+00	2025-09-28 21:34:37.915287+00	default
1331c17d-844c-478b-8f11-b05c5adf5f11	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:35:37.040501+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-28 21:35:37.040507+00	2025-09-28 21:35:37.040507+00	default
f3a97c0e-2a12-4872-b4f0-51e46d4e2690	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:39:21.746198+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-28 21:39:21.746206+00	2025-09-28 21:39:21.746208+00	default
cfe1b61f-3f3d-4925-8ac9-c0a9c3ab945d	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-28 21:40:18.680837+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-28 21:40:18.680846+00	2025-09-28 21:40:18.680847+00	default
91114382-4222-46ad-b49c-ea4319f64aa3	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:35:23.911472+00	\N	\N	login_success	User admin logged in successfully (cookie-auth)	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"], "auth_method": "cookie"}	::1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N	2025-09-29 09:35:23.911478+00	2025-09-29 09:35:23.911479+00	default
8d9ac17d-f344-46b8-aea0-30e1f3a3273b	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:41:23.615618+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-29 09:41:23.615911+00	2025-09-29 09:41:23.615918+00	default
7cfb4e98-044f-431a-9035-0eabe5907ab7	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:46:47.975716+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-29 09:46:47.975956+00	2025-09-29 09:46:47.975957+00	default
c444986b-421c-46a5-9112-56ee63e1d20b	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:48:42.734503+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-29 09:48:42.734544+00	2025-09-29 09:48:42.734545+00	default
0bb401a3-eb93-41c6-b87f-ac5d106df797	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:49:14.620748+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	::1	curl/8.7.1	\N	2025-09-29 09:49:14.620768+00	2025-09-29 09:49:14.620769+00	default
6b3d8964-04d0-46e6-865b-39e921c41ed5	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:51:01.083186+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-29 09:51:01.08319+00	2025-09-29 09:51:01.083191+00	default
f04325aa-cc54-4c45-a211-8e46fcab4dd7	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 09:52:22.319417+00	\N	\N	login_success	User admin logged in successfully	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"]}	127.0.0.1	curl/8.7.1	\N	2025-09-29 09:52:22.319425+00	2025-09-29 09:52:22.319426+00	default
f9b888a4-013e-47ff-804e-1199623a8bc0	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 10:39:44.20963+00	\N	\N	login_success	User admin logged in successfully (cookie-auth)	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"], "auth_method": "cookie"}	::1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N	2025-09-29 10:39:44.209634+00	2025-09-29 10:39:44.209635+00	default
82b326ec-dce4-46a5-86bd-a147627784fa	user.login	low	5051d72d-acc8-49bf-addd-1fed118a4a56	2025-09-29 11:32:57.544086+00	\N	\N	login_success	User admin logged in successfully (cookie-auth)	{"username": "admin", "email": "admin@example.com", "roles": ["admin", "user"], "auth_method": "cookie"}	::1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N	2025-09-29 11:32:57.544091+00	2025-09-29 11:32:57.544092+00	default
4c55904a-c9fe-4c5d-9277-58c382292b0b	user.created	medium	d943a549-bf2f-4bfc-a151-0b970bc050b4	2025-09-29 20:44:03.333262+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-29 20:44:03.333275+00	2025-09-29 20:44:03.333276+00	tenant123
3aa0971c-2a1d-4ab8-a880-fc1666488a84	api.request	high	\N	2025-09-29 20:44:03.868674+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 20:44:03.868681+00	2025-09-29 20:44:03.868682+00	default
2363e4e0-c4dc-48e2-8116-7d67b139a92f	api.request	high	\N	2025-09-29 20:44:04.525888+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 20:44:04.525896+00	2025-09-29 20:44:04.525897+00	default
af90b095-287a-4c5d-bea3-2fa848764406	api.request	high	\N	2025-09-29 20:44:04.851973+00	\N	\N	login_failed	Failed login attempt for username: inactive	{"username": "inactive", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 20:44:04.851992+00	2025-09-29 20:44:04.851993+00	default
2ef8dcf9-9d72-4139-be5d-c47d0fd412df	api.request	medium	\N	2025-09-29 20:44:04.921222+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "test@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-29 20:44:04.921229+00	2025-09-29 20:44:04.921229+00	default
23726690-7eed-448d-bf37-fa44b8f26b00	api.request	high	\N	2025-09-29 20:44:04.972465+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "DB error"}	testclient	testclient	\N	2025-09-29 20:44:04.97247+00	2025-09-29 20:44:04.972471+00	default
c057a07b-aa1b-475d-9bf9-b7407cc7542e	rbac.role.revoked	medium	f9400a5e-017e-453c-9c9b-c8336ff83820	2025-09-29 20:44:07.404364+00	user	a1b221e0-c491-4244-b185-4cbddc7ffba7	revoke_role	Revoked role 'test_role' from user	{"target_user_id": "a1b221e0-c491-4244-b185-4cbddc7ffba7", "role_name": "test_role", "role_id": "8d896ec4-facf-47b6-ab3d-ded22ec5acce", "reason": "Test revocation"}	\N	\N	\N	2025-09-29 20:44:07.404376+00	2025-09-29 20:44:07.404377+00	test_tenant
ce3fb78f-da6f-4102-8e01-1842e2cd49b1	rbac.permission.revoked	medium	8fb6241e-fbe6-488c-8f78-60797be1090f	2025-09-29 20:44:07.44739+00	user	6f3069a7-c221-4401-92c6-d27d7e1c01cd	revoke_permission	Revoked permission 'test.permission' from user	{"target_user_id": "6f3069a7-c221-4401-92c6-d27d7e1c01cd", "permission_name": "test.permission", "permission_id": "c1b77b52-d5a0-4220-8629-2376935732c0", "reason": "Testing permission revocation"}	\N	\N	\N	2025-09-29 20:44:07.447396+00	2025-09-29 20:44:07.447396+00	test_tenant
d550eedb-f6df-4765-a962-5f6a0ae88252	user.login	low	5911472e-8da7-4835-87ce-afcd5835ab16	2025-09-29 20:44:07.54455+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 20:44:07.544555+00	2025-09-29 20:44:07.544556+00	test-tenant
9db15911-97fc-4680-b25f-8a6ecf8cc48d	api.request	high	\N	2025-09-29 20:44:07.602975+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 20:44:07.602981+00	2025-09-29 20:44:07.602982+00	default
e7992907-10b6-4144-b491-67ed55ea5fe6	user.created	medium	faedbe1f-b44e-47f1-aebc-73f93cea37ea	2025-09-29 20:44:07.703178+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 20:44:07.703207+00	2025-09-29 20:44:07.703207+00	test-tenant
a6ac7d55-79d1-4727-9a37-27fcafc3112a	api.request	medium	\N	2025-09-29 20:44:07.836141+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "existing@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-29 20:44:07.836149+00	2025-09-29 20:44:07.836149+00	default
55e17927-430d-4753-80c0-2a213d10c45d	user.created	medium	1201bc4b-2b6f-4fe1-80cb-64014ff28b46	2025-09-29 20:44:08.392999+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 20:44:08.393007+00	2025-09-29 20:44:08.393007+00	test-tenant
4524c19f-37d4-489c-b393-0c5be1e4f0ca	user.created	medium	93f38b83-a996-4dd2-ba2f-6f51be6e58d5	2025-09-29 21:00:58.638831+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-29 21:00:58.64048+00	2025-09-29 21:00:58.640488+00	tenant123
555edf88-5c5e-40ae-9590-66246132c7ba	api.request	high	\N	2025-09-29 21:01:05.669698+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 21:01:05.669903+00	2025-09-29 21:01:05.669906+00	default
c59e5c47-809d-4b24-8a82-856e763b2636	api.request	high	\N	2025-09-29 21:01:07.359846+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 21:01:07.359868+00	2025-09-29 21:01:07.359869+00	default
a95ffef1-9ed2-4a9a-92ca-45fba1e7db21	api.request	high	\N	2025-09-29 21:01:08.166466+00	\N	\N	login_failed	Failed login attempt for username: inactive	{"username": "inactive", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 21:01:08.166485+00	2025-09-29 21:01:08.166486+00	default
490246fa-12a3-4055-bf62-c897e350dfed	api.request	medium	\N	2025-09-29 21:01:08.973098+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "test@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-29 21:01:08.973333+00	2025-09-29 21:01:08.973335+00	default
c70b317d-c47c-41bf-b58f-b0a904e1079c	api.request	high	\N	2025-09-29 21:01:09.554825+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "DB error"}	testclient	testclient	\N	2025-09-29 21:01:09.55483+00	2025-09-29 21:01:09.554831+00	default
680e2fda-406c-4887-8e47-6966db2f3975	rbac.role.revoked	medium	2ce4197d-02c9-4bda-b4aa-3301bb5bc961	2025-09-29 21:01:12.976852+00	user	29ad208a-abe2-4f2b-83a1-ad2658283868	revoke_role	Revoked role 'test_role' from user	{"target_user_id": "29ad208a-abe2-4f2b-83a1-ad2658283868", "role_name": "test_role", "role_id": "8d3520bc-9f6d-406c-a2a9-fdfaa404b150", "reason": "Test revocation"}	\N	\N	\N	2025-09-29 21:01:12.976881+00	2025-09-29 21:01:12.976883+00	test_tenant
b970b69c-5083-4877-8b94-305b15733020	rbac.permission.revoked	medium	009a970d-cde7-4c19-8509-deb8fb7c0c74	2025-09-29 21:01:13.158414+00	user	f756c335-f7ce-42c0-a741-aa63b8c94a93	revoke_permission	Revoked permission 'test.permission' from user	{"target_user_id": "f756c335-f7ce-42c0-a741-aa63b8c94a93", "permission_name": "test.permission", "permission_id": "b3b9fc3d-94ea-4968-886d-9dcaf0ab164d", "reason": "Testing permission revocation"}	\N	\N	\N	2025-09-29 21:01:13.158433+00	2025-09-29 21:01:13.158434+00	test_tenant
bc0ad402-2998-4f2d-abdd-682d172423a3	user.login	low	c8e9e357-60b5-44c9-8a8f-d0098ef487a2	2025-09-29 21:01:13.604633+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 21:01:13.604647+00	2025-09-29 21:01:13.604648+00	test-tenant
fdd7363f-6090-4466-8e96-e76de6cb18cf	api.request	high	\N	2025-09-29 21:01:13.946578+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-29 21:01:13.946587+00	2025-09-29 21:01:13.946588+00	default
d598edd3-01a9-4486-be8a-ace8abad46e2	user.created	medium	0c290359-3861-4686-b27d-87a9db956dc6	2025-09-29 21:01:14.454971+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 21:01:14.455002+00	2025-09-29 21:01:14.455002+00	test-tenant
712047a8-fcbc-4483-b513-ca852d1a8243	api.request	medium	\N	2025-09-29 21:01:14.870865+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "existing@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-29 21:01:14.87088+00	2025-09-29 21:01:14.870881+00	default
407a487b-9391-4cd9-8a1b-143036e35b0b	user.created	medium	dee00db9-04a3-46b2-9e24-6a598af1dff2	2025-09-29 21:01:15.52476+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-29 21:01:15.524771+00	2025-09-29 21:01:15.524772+00	test-tenant
d42365bc-da62-4b4d-b094-33f2953731d4	user.created	medium	cf36da57-a90f-467a-a6cc-65ab89a20238	2025-09-30 02:12:38.067007+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-30 02:12:38.067018+00	2025-09-30 02:12:38.067023+00	tenant123
d780a86c-1ffb-478e-9a37-567968a277b8	api.request	high	\N	2025-09-30 02:12:38.824387+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:12:38.824394+00	2025-09-30 02:12:38.824395+00	default
e13779ce-7ca2-4f3f-ae6c-aabbdc1e20c6	api.request	high	\N	2025-09-30 02:12:39.411237+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:12:39.411246+00	2025-09-30 02:12:39.411248+00	default
5a473d9e-84bb-4cea-8b21-e3bfd1237f3d	api.request	high	\N	2025-09-30 02:12:39.730461+00	\N	\N	login_failed	Failed login attempt for username: inactive	{"username": "inactive", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:12:39.730467+00	2025-09-30 02:12:39.730469+00	default
b4a0450c-e4e1-4a32-ba21-bebb8275222d	api.request	medium	\N	2025-09-30 02:12:39.80567+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "test@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 02:12:39.805677+00	2025-09-30 02:12:39.805679+00	default
54c561ae-5bbf-42f4-befc-3d17ff44dad2	api.request	high	\N	2025-09-30 02:12:39.909129+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "DB error"}	testclient	testclient	\N	2025-09-30 02:12:39.909142+00	2025-09-30 02:12:39.909145+00	default
601e59a2-44bf-4ae9-9e68-acfcbdaeac18	rbac.role.revoked	medium	9d482e59-6d14-404c-a5cc-c081fb229fc1	2025-09-30 02:12:42.473058+00	user	e555b981-8ac7-4a61-920c-8cfb413ef8cc	revoke_role	Revoked role 'test_role' from user	{"target_user_id": "e555b981-8ac7-4a61-920c-8cfb413ef8cc", "role_name": "test_role", "role_id": "bf0e865f-dcdb-4b80-af48-e495aef46432", "reason": "Test revocation"}	\N	\N	\N	2025-09-30 02:12:42.473086+00	2025-09-30 02:12:42.473093+00	test_tenant
b95e989e-ad4d-4623-a449-9e579085bf4d	rbac.permission.revoked	medium	5da0f87e-abee-4c9a-b278-20e0e1ec6402	2025-09-30 02:12:42.545468+00	user	80bf4b62-60be-4477-ac08-65dcfa8d3adc	revoke_permission	Revoked permission 'test.permission' from user	{"target_user_id": "80bf4b62-60be-4477-ac08-65dcfa8d3adc", "permission_name": "test.permission", "permission_id": "dabd8fe0-347d-46bd-84d3-cfdb03e313fa", "reason": "Testing permission revocation"}	\N	\N	\N	2025-09-30 02:12:42.545477+00	2025-09-30 02:12:42.54548+00	test_tenant
d67ba059-7b98-4a2b-92d4-b7ed93bd1d38	user.login	low	3c37b289-7ec5-4019-af89-0ee20f61cdc2	2025-09-30 02:12:42.827405+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:12:42.827427+00	2025-09-30 02:12:42.827429+00	test-tenant
c36d52aa-8d06-46e5-9276-0953adf12927	api.request	high	\N	2025-09-30 02:12:42.955473+00	\N	\N	login_failed	Failed login attempt for username: testuser	{"username": "testuser", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:12:42.955483+00	2025-09-30 02:12:42.955487+00	default
79334ca8-1178-48db-a658-0928199afcd0	user.created	medium	5cfb0cd7-5ccf-43db-bbee-3f8a950f77d7	2025-09-30 02:12:43.242299+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:12:43.242318+00	2025-09-30 02:12:43.24232+00	test-tenant
2554c741-c0e9-4aae-bbf1-fac9254e7a49	api.request	medium	\N	2025-09-30 02:12:43.390883+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "newuser", "email": "existing@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 02:12:43.390896+00	2025-09-30 02:12:43.390898+00	default
340c6b08-c575-4353-a97a-d9b8df65ffa6	user.created	medium	50752a2a-60d7-447c-954a-100e638b862f	2025-09-30 02:12:44.044052+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:12:44.044063+00	2025-09-30 02:12:44.044071+00	test-tenant
d8baa75a-5813-4516-9eba-a6f66e0e8613	user.created	medium	93e3fd22-451c-462d-9a35-e941672906ae	2025-09-30 02:18:05.775464+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-30 02:18:05.77547+00	2025-09-30 02:18:05.775472+00	tenant123
e5ad68b0-4bd7-4ce9-a581-9f9ed3ac1d4e	user.created	medium	0e2327ca-9a1e-4def-9438-e1d48bbf93ad	2025-09-30 02:18:07.261851+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:18:07.261871+00	2025-09-30 02:18:07.261872+00	default
99716236-062b-446b-b033-1a6a9b3071aa	api.request	high	\N	2025-09-30 02:18:09.431488+00	\N	\N	login_failed	Failed login attempt for username: test@example.com	{"username": "test@example.com", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:18:09.431502+00	2025-09-30 02:18:09.431507+00	default
edcabbb1-2afd-4c82-a786-8ee06c3a6b1a	api.request	high	\N	2025-09-30 02:18:09.798608+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:18:09.798616+00	2025-09-30 02:18:09.798617+00	default
6da20cd8-4fe0-4842-aec7-8d171ac94758	user.created	medium	c7de12c4-13ed-4a98-9c80-02140e4d5454	2025-09-30 02:18:10.296475+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:18:10.296562+00	2025-09-30 02:18:10.296566+00	default
2af938d0-09f8-463c-a1be-d5c6decf24ce	user.created	medium	d065ae7e-e2e9-46c8-86b1-2aa86f9a2241	2025-09-30 02:18:10.388026+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": null, "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:18:10.388031+00	2025-09-30 02:18:10.388033+00	default
6844ed61-06b7-4147-8b13-b81700597f2a	rbac.role.assigned	medium	29edd8a6-dc73-4243-af6d-ec15435b8d30	2025-09-30 02:18:14.638568+00	user	c4253a82-c303-4005-b2a1-e477a4391d4f	assign_role	Assigned role 'test_role' to user	{"target_user_id": "c4253a82-c303-4005-b2a1-e477a4391d4f", "role_name": "test_role", "role_id": "c130424d-c75b-437c-a630-07d5cbd63078", "metadata": {"test": "data"}}	\N	\N	\N	2025-09-30 02:18:14.638573+00	2025-09-30 02:18:14.638682+00	test_tenant
9d77c674-c801-4128-a908-14111c7e552d	rbac.permission.granted	medium	6eaa6b39-82c3-44c7-91ee-7b32a2c3cf5f	2025-09-30 02:18:14.690112+00	user	57a5ef78-1b74-4732-adf8-84c77f0eb467	grant_permission	Granted permission 'test.permission' to user	{"target_user_id": "57a5ef78-1b74-4732-adf8-84c77f0eb467", "permission_name": "test.permission", "permission_id": "d573781f-6733-4ab3-b454-d38127fd3f2e", "expires_at": null, "reason": "Testing permission grant"}	\N	\N	\N	2025-09-30 02:18:14.690118+00	2025-09-30 02:18:14.69012+00	test_tenant
8f6195bd-d905-46bc-a312-49d3b5d3eb26	user.login	low	9349b4c1-fca3-4428-9015-df7c90947e89	2025-09-30 02:18:14.840788+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:18:14.840793+00	2025-09-30 02:18:14.840795+00	test-tenant
04773f88-b329-4f63-9582-0ed0e8f39849	api.request	high	\N	2025-09-30 02:18:14.915007+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:18:14.915013+00	2025-09-30 02:18:14.915014+00	default
913f3bc5-bbd7-4152-8456-1f47b244ebf4	user.login	high	09b35445-ca0e-4198-a08a-5121244ca85b	2025-09-30 02:18:14.993711+00	\N	\N	login_disabled_account	Login attempt on disabled account: testuser	{"username": "testuser", "reason": "account_disabled"}	\N	\N	\N	2025-09-30 02:18:14.993721+00	2025-09-30 02:18:14.993723+00	default
85b14198-3527-48d1-9d89-0b24900394c6	api.request	medium	\N	2025-09-30 02:18:15.069687+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "existinguser", "email": "new@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 02:18:15.069693+00	2025-09-30 02:18:15.069694+00	default
db6b07a7-1c84-4de0-a3a3-f83bdf3700b7	api.request	high	\N	2025-09-30 02:18:15.143567+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "Database error"}	testclient	testclient	\N	2025-09-30 02:18:15.143575+00	2025-09-30 02:18:15.143576+00	default
4cf91300-c067-4d7c-9427-f044e49d2a4f	user.created	medium	00fb0fa5-fe93-423a-8384-8bccac70e301	2025-09-30 02:29:25.704595+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-30 02:29:25.704611+00	2025-09-30 02:29:25.704614+00	tenant123
2e9db49f-7301-411e-8d26-d4191fff71bf	user.created	medium	862e092b-052c-4036-92a4-f449510c16b7	2025-09-30 02:29:28.642645+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:29:28.642672+00	2025-09-30 02:29:28.642682+00	default
3bcbb5b0-0de9-459b-9eb9-a6588d1fc80b	api.request	high	\N	2025-09-30 02:29:32.421695+00	\N	\N	login_failed	Failed login attempt for username: test@example.com	{"username": "test@example.com", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:29:32.421715+00	2025-09-30 02:29:32.421719+00	default
efe47905-dc3e-4dd7-ae71-f957508b5a76	api.request	high	\N	2025-09-30 02:29:33.148517+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:29:33.149053+00	2025-09-30 02:29:33.149075+00	default
b5716283-82e8-41d0-add9-f9ff364abb91	user.created	medium	f5b1d9be-57de-4a6e-a0fd-2a5c911374e3	2025-09-30 02:29:33.713064+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:29:33.713071+00	2025-09-30 02:29:33.713073+00	default
b7652afc-0b22-4596-9647-eb2f00671343	user.created	medium	9b2f8ae9-04d4-4684-be5d-b10d1141d579	2025-09-30 02:29:33.821512+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": null, "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:29:33.821519+00	2025-09-30 02:29:33.821521+00	default
51267876-d424-4a56-86ef-2251f11f53fc	rbac.role.assigned	medium	29ffd0b3-2fd1-436e-80f8-9cda3c0ba2d0	2025-09-30 02:29:39.531201+00	user	4cb89632-decb-46b5-ac07-25fc43912767	assign_role	Assigned role 'test_role' to user	{"target_user_id": "4cb89632-decb-46b5-ac07-25fc43912767", "role_name": "test_role", "role_id": "17756c67-a4ee-47a8-a26b-f9048cc54535", "metadata": {"test": "data"}}	\N	\N	\N	2025-09-30 02:29:39.531228+00	2025-09-30 02:29:39.531234+00	test_tenant
ab442962-30bb-4598-bd5b-5aef5e231984	rbac.permission.granted	medium	c433277b-ede4-46d1-8183-a6e52fdae32a	2025-09-30 02:29:39.680923+00	user	0cdb070d-5b74-487d-af52-fa688c36080b	grant_permission	Granted permission 'test.permission' to user	{"target_user_id": "0cdb070d-5b74-487d-af52-fa688c36080b", "permission_name": "test.permission", "permission_id": "cde79e4f-9788-4a6b-a3ee-eae9c21f9981", "expires_at": null, "reason": "Testing permission grant"}	\N	\N	\N	2025-09-30 02:29:39.680929+00	2025-09-30 02:29:39.680931+00	test_tenant
f63a960f-40f7-427b-8e07-a7d33e78bd35	user.login	low	f8ddae12-754f-448e-bfc7-f111fa3bfb09	2025-09-30 02:29:39.934924+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 02:29:39.934933+00	2025-09-30 02:29:39.934934+00	test-tenant
552d7271-008a-4ad7-880f-ccbb459c2b8f	api.request	high	\N	2025-09-30 02:29:40.992528+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 02:29:40.992542+00	2025-09-30 02:29:40.992547+00	default
a181aaa7-5df1-4849-bc9c-b7bc9190b40d	user.login	high	e75d52ca-5646-4075-ba80-058d29fae5fe	2025-09-30 02:29:41.211661+00	\N	\N	login_disabled_account	Login attempt on disabled account: testuser	{"username": "testuser", "reason": "account_disabled"}	\N	\N	\N	2025-09-30 02:29:41.211667+00	2025-09-30 02:29:41.211668+00	default
b223b311-fa2e-4685-aa69-832a6637d9a6	api.request	medium	\N	2025-09-30 02:29:41.362004+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "existinguser", "email": "new@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 02:29:41.36204+00	2025-09-30 02:29:41.362044+00	default
0fa6004a-20be-48be-898e-84db68477553	api.request	high	\N	2025-09-30 02:29:41.524953+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "Database error"}	testclient	testclient	\N	2025-09-30 02:29:41.524962+00	2025-09-30 02:29:41.524964+00	default
41604f15-88a9-4d84-8447-3379c9e26587	user.created	medium	f59b5f60-07c7-4357-8a76-60582c031225	2025-09-30 03:45:56.256203+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-30 03:45:56.25621+00	2025-09-30 03:45:56.256213+00	tenant123
9c0dc65f-9fd0-465e-b713-bdb91bf5ce3f	user.created	medium	1eba02cd-d6e6-410e-87d7-a2b532530e24	2025-09-30 03:45:59.091119+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 03:45:59.091125+00	2025-09-30 03:45:59.091126+00	default
6db690a9-d68a-4216-83c0-225408ab5a18	api.request	high	\N	2025-09-30 03:46:02.219365+00	\N	\N	login_failed	Failed login attempt for username: test@example.com	{"username": "test@example.com", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 03:46:02.219371+00	2025-09-30 03:46:02.219372+00	default
a1cd8c19-2be4-41bb-af7e-a0cc1e0628ea	api.request	high	\N	2025-09-30 03:46:03.473633+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 03:46:03.473638+00	2025-09-30 03:46:03.473639+00	default
467b7525-76dd-48d4-bdae-68397d67b80f	user.created	medium	cfee7a9e-51f1-464b-907c-d1f28cb1c794	2025-09-30 03:46:04.707417+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 03:46:04.707422+00	2025-09-30 03:46:04.707424+00	default
8c094da3-d800-497b-8d21-10cfa6a33168	user.created	medium	b244a7cc-21c8-409e-beba-f649033eadeb	2025-09-30 03:46:06.031631+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": null, "roles": ["user"]}	testclient	testclient	\N	2025-09-30 03:46:06.031636+00	2025-09-30 03:46:06.031638+00	default
995b570c-eb92-40fe-9e53-71f6917e2ac0	rbac.role.assigned	medium	be34e548-b284-4b38-8425-5fbbda3cae32	2025-09-30 03:46:13.288304+00	user	04554447-49e8-469c-8cde-e925e27a5514	assign_role	Assigned role 'test_role' to user	{"target_user_id": "04554447-49e8-469c-8cde-e925e27a5514", "role_name": "test_role", "role_id": "4a345b23-ed86-4929-81f8-534fcbd80479", "metadata": {"test": "data"}}	\N	\N	\N	2025-09-30 03:46:13.288311+00	2025-09-30 03:46:13.288313+00	test_tenant
f629a6cd-780c-40d5-9351-298550a853ab	rbac.permission.granted	medium	e46fc0e4-a263-4c6f-926f-950903bc9928	2025-09-30 03:46:13.9972+00	user	a4566e89-652c-4ae6-b225-73a7b892f967	grant_permission	Granted permission 'test.permission' to user	{"target_user_id": "a4566e89-652c-4ae6-b225-73a7b892f967", "permission_name": "test.permission", "permission_id": "71553aee-4717-4ce3-9659-3e17d119d12e", "expires_at": null, "reason": "Testing permission grant"}	\N	\N	\N	2025-09-30 03:46:13.997206+00	2025-09-30 03:46:13.997207+00	test_tenant
a9730718-20ea-4558-8d63-87a64bd79bf3	user.login	low	716c2817-a7cd-47d0-8314-15bcc5c54457	2025-09-30 03:46:14.805699+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 03:46:14.805704+00	2025-09-30 03:46:14.805705+00	test-tenant
dded8a8f-68bb-42a9-8625-96f6f1ee25f9	api.request	high	\N	2025-09-30 03:46:15.901777+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 03:46:15.901783+00	2025-09-30 03:46:15.901784+00	default
4d9609f2-e954-4bc5-8945-57e775130604	user.login	high	33235ef8-e6fb-4596-9ecd-46e41b4f4a62	2025-09-30 03:46:16.987696+00	\N	\N	login_disabled_account	Login attempt on disabled account: testuser	{"username": "testuser", "reason": "account_disabled"}	\N	\N	\N	2025-09-30 03:46:16.987702+00	2025-09-30 03:46:16.987703+00	default
3dbb6347-262f-422b-92d3-109d10e6b45a	api.request	medium	\N	2025-09-30 03:46:18.058989+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "existinguser", "email": "new@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 03:46:18.058996+00	2025-09-30 03:46:18.058997+00	default
8fe2a563-47c7-43a7-82d6-422c115cfe4c	api.request	high	\N	2025-09-30 03:46:19.334835+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "Database error"}	testclient	testclient	\N	2025-09-30 03:46:19.334847+00	2025-09-30 03:46:19.334853+00	default
28353908-596c-4656-bdcd-c2cf8421e9ac	user.created	medium	b88b29a6-deab-4ff7-8884-3632a26f7bed	2025-09-30 04:05:43.391326+00	\N	\N	registration_success	New user testuser registered successfully	{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "roles": ["user"]}	127.0.0.1	test-user-agent	\N	2025-09-30 04:05:43.391335+00	2025-09-30 04:05:43.391338+00	tenant123
64db7b87-ce37-44ef-ba9d-a52854b08f7b	user.created	medium	a3096336-bfa0-4cc2-a51b-5c6fa336abf4	2025-09-30 04:05:44.979468+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 04:05:44.979917+00	2025-09-30 04:05:44.979967+00	default
2a6ce681-666f-4c39-8c7e-a96575f85de7	api.request	high	\N	2025-09-30 04:05:47.293313+00	\N	\N	login_failed	Failed login attempt for username: test@example.com	{"username": "test@example.com", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 04:05:47.293319+00	2025-09-30 04:05:47.293321+00	default
684c3bb7-2fd0-446c-9bf4-94ecd203edd6	api.request	high	\N	2025-09-30 04:05:47.60072+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 04:05:47.600727+00	2025-09-30 04:05:47.600728+00	default
faa84d00-dc6d-4fab-82ba-c3352a827bba	user.created	medium	9e2e9b0b-e85c-4736-bd6b-c1b3c05195f2	2025-09-30 04:05:47.908342+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": "New User", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 04:05:47.908348+00	2025-09-30 04:05:47.908352+00	default
e6bc87af-c5e4-409c-b8b0-31d21c1b0268	user.created	medium	4c467fae-cce5-495c-8aed-8dec9c74b323	2025-09-30 04:05:47.974693+00	\N	\N	registration_success	New user newuser registered successfully	{"username": "newuser", "email": "new@example.com", "full_name": null, "roles": ["user"]}	testclient	testclient	\N	2025-09-30 04:05:47.974698+00	2025-09-30 04:05:47.974699+00	default
689d19ea-0d23-40dc-8935-78543b5873e9	rbac.role.assigned	medium	62147200-95fb-43ff-941f-a9c16151e6e5	2025-09-30 04:05:51.858999+00	user	b547fc4b-509d-4c76-a077-04698f40b535	assign_role	Assigned role 'test_role' to user	{"target_user_id": "b547fc4b-509d-4c76-a077-04698f40b535", "role_name": "test_role", "role_id": "b735e130-b869-46b4-a42a-bcd682d3181f", "metadata": {"test": "data"}}	\N	\N	\N	2025-09-30 04:05:51.859005+00	2025-09-30 04:05:51.859006+00	test_tenant
2180be56-ab11-46f6-bae1-995abc1086fb	rbac.permission.granted	medium	7358eb52-878f-4b2a-ba8f-4c2a9beab444	2025-09-30 04:05:51.985284+00	user	e3865c2d-9a6e-4ac3-aae3-b4e53c190840	grant_permission	Granted permission 'test.permission' to user	{"target_user_id": "e3865c2d-9a6e-4ac3-aae3-b4e53c190840", "permission_name": "test.permission", "permission_id": "7487b0dc-c623-43bb-8d6e-2561fddde804", "expires_at": null, "reason": "Testing permission grant"}	\N	\N	\N	2025-09-30 04:05:51.985289+00	2025-09-30 04:05:51.985291+00	test_tenant
e7822db2-f8bd-47ba-90e6-0c78b9ec4077	user.login	low	e7adf155-1943-4d4c-89ea-85b0e88e84d1	2025-09-30 04:05:52.233152+00	\N	\N	login_success	User testuser logged in successfully	{"username": "testuser", "email": "test@example.com", "roles": ["user"]}	testclient	testclient	\N	2025-09-30 04:05:52.233157+00	2025-09-30 04:05:52.233158+00	test-tenant
13f0159c-3e72-4c25-bb5d-2449343b9c1e	api.request	high	\N	2025-09-30 04:05:52.31288+00	\N	\N	login_failed	Failed login attempt for username: nonexistent	{"username": "nonexistent", "reason": "invalid_credentials"}	testclient	testclient	\N	2025-09-30 04:05:52.312888+00	2025-09-30 04:05:52.312889+00	default
05575f7a-df63-49fc-91f3-d19610924c95	user.login	high	7caefa87-0fe5-4744-b9a0-0f879093e87d	2025-09-30 04:05:52.410159+00	\N	\N	login_disabled_account	Login attempt on disabled account: testuser	{"username": "testuser", "reason": "account_disabled"}	\N	\N	\N	2025-09-30 04:05:52.410164+00	2025-09-30 04:05:52.410166+00	default
1018eaa2-9d81-4c8c-b8e9-07a3ac8bc47a	api.request	medium	\N	2025-09-30 04:05:52.523636+00	\N	\N	registration_failed	Registration attempt with existing credentials	{"username": "existinguser", "email": "new@example.com", "reason": "user_already_exists"}	testclient	testclient	\N	2025-09-30 04:05:52.523641+00	2025-09-30 04:05:52.523642+00	default
e98fe01b-7e21-4169-bb7a-f4164896fcee	api.request	high	\N	2025-09-30 04:05:52.611026+00	\N	\N	registration_failed	Registration failed during user creation	{"username": "newuser", "email": "new@example.com", "reason": "user_creation_error", "error": "Database error"}	testclient	testclient	\N	2025-09-30 04:05:52.611031+00	2025-09-30 04:05:52.611032+00	default
\.


--
-- Data for Name: billing_pricing_rules; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_pricing_rules (rule_id, name, applies_to_product_ids, applies_to_categories, applies_to_all, min_quantity, customer_segments, discount_type, discount_value, starts_at, ends_at, max_uses, current_uses, is_active, tenant_id, created_at, updated_at, metadata, id, deleted_at) FROM stdin;
\.


--
-- Data for Name: billing_product_categories; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_product_categories (category_id, name, description, default_tax_class, sort_order, tenant_id, created_at, updated_at, metadata, id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: billing_products; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_products (product_id, sku, name, description, category, product_type, base_price, currency, tax_class, usage_type, usage_unit_name, is_active, tenant_id, created_at, updated_at, metadata, id, deleted_at) FROM stdin;
\.


--
-- Data for Name: billing_rule_usage; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_rule_usage (usage_id, rule_id, customer_id, invoice_id, used_at, tenant_id, created_at, updated_at, metadata, id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: billing_subscription_events; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_subscription_events (event_id, subscription_id, event_type, event_data, user_id, tenant_id, created_at, updated_at, metadata, id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: billing_subscription_plans; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_subscription_plans (plan_id, product_id, name, description, billing_cycle, price, currency, setup_fee, trial_days, included_usage, overage_rates, is_active, tenant_id, created_at, updated_at, metadata, id, deleted_at) FROM stdin;
\.


--
-- Data for Name: billing_subscriptions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.billing_subscriptions (subscription_id, customer_id, plan_id, current_period_start, current_period_end, status, trial_end, cancel_at_period_end, canceled_at, custom_price, usage_records, tenant_id, created_at, updated_at, metadata, id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: cash_reconciliations; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.cash_reconciliations (id, register_id, reconciliation_date, opening_float, closing_float, expected_cash, actual_cash, discrepancy, reconciled_by, notes, shift_id, meta_data, tenant_id) FROM stdin;
\.


--
-- Data for Name: cash_registers; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.cash_registers (id, register_id, register_name, location, initial_float, current_float, max_cash_limit, is_active, requires_daily_reconciliation, last_reconciled, created_by, updated_by, meta_data, deleted_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: cash_transactions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.cash_transactions (id, register_id, transaction_type, amount, balance_after, reference, description, created_by, meta_data, tenant_id) FROM stdin;
\.


--
-- Data for Name: communication_logs; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.communication_logs (id, type, recipient, sender, subject, text_body, html_body, status, sent_at, delivered_at, failed_at, error_message, retry_count, provider, provider_message_id, template_id, template_name, user_id, job_id, metadata, headers, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: communication_stats; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.communication_stats (id, stats_date, type, total_sent, total_delivered, total_failed, total_bounced, total_pending, avg_delivery_time_seconds, metadata, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: communication_templates; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.communication_templates (id, name, description, type, subject_template, text_template, html_template, variables, required_variables, is_active, is_default, usage_count, last_used_at, metadata, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: company_bank_accounts; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.company_bank_accounts (id, account_name, account_nickname, bank_name, bank_address, bank_country, account_number_encrypted, account_number_last_four, routing_number, swift_code, iban, account_type, currency, status, is_primary, is_active, accepts_deposits, verified_at, verified_by, verification_notes, notes, meta_data, tenant_id, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: contact_activities; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contact_activities (id, contact_id, activity_type, subject, description, activity_date, duration_minutes, status, outcome, performed_by, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: contact_field_definitions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contact_field_definitions (id, tenant_id, name, field_key, description, field_type, is_required, is_unique, is_searchable, default_value, validation_rules, options, display_order, placeholder, help_text, field_group, is_visible, is_editable, required_permission, is_system, is_encrypted, metadata, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: contact_label_definitions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contact_label_definitions (id, tenant_id, name, slug, description, color, icon, category, display_order, is_visible, is_system, is_default, metadata, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: contact_methods; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contact_methods (id, contact_id, type, value, label, address_line1, address_line2, city, state_province, postal_code, country, is_primary, is_verified, is_public, verified_at, verified_by, verification_token, display_order, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: contact_to_labels; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contact_to_labels (contact_id, label_definition_id, assigned_at, assigned_by) FROM stdin;
\.


--
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.contacts (id, tenant_id, customer_id, first_name, middle_name, last_name, display_name, prefix, suffix, company, job_title, department, status, stage, owner_id, notes, tags, custom_fields, metadata, birthday, anniversary, is_primary, is_decision_maker, is_billing_contact, is_technical_contact, is_verified, preferred_contact_method, preferred_language, timezone, created_at, updated_at, last_contacted_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: credit_applications; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.credit_applications (application_id, credit_note_id, applied_to_type, applied_to_id, applied_amount, application_date, applied_by, notes, extra_data, tenant_id) FROM stdin;
\.


--
-- Data for Name: credit_note_line_items; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.credit_note_line_items (line_item_id, credit_note_id, description, quantity, unit_price, total_price, original_invoice_line_item_id, product_id, tax_rate, tax_amount, extra_data) FROM stdin;
\.


--
-- Data for Name: credit_notes; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.credit_notes (credit_note_id, credit_note_number, idempotency_key, customer_id, invoice_id, issue_date, currency, subtotal, tax_amount, total_amount, credit_type, reason, reason_description, status, auto_apply_to_invoice, remaining_credit_amount, notes, internal_notes, extra_data, voided_at, tenant_id, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: customer_activities; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customer_activities (id, customer_id, activity_type, title, description, metadata, performed_by, ip_address, user_agent, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: customer_credits; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customer_credits (customer_id, tenant_id, total_credit_amount, currency, credit_notes, auto_apply_to_new_invoices, extra_data, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: customer_notes; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customer_notes (id, customer_id, subject, content, is_internal, created_by_id, created_at, updated_at, tenant_id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: customer_segments; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customer_segments (id, name, description, criteria, is_dynamic, priority, member_count, last_calculated, created_at, updated_at, tenant_id, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: customer_tags_association; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customer_tags_association (id, customer_id, tag_name, tag_category, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.customers (id, customer_number, first_name, last_name, middle_name, display_name, company_name, status, customer_type, tier, email, email_verified, phone, phone_verified, mobile, address_line1, address_line2, city, state_province, postal_code, country, tax_id, vat_number, industry, employee_count, annual_revenue, preferred_channel, preferred_language, timezone, opt_in_marketing, opt_in_updates, user_id, assigned_to, segment_id, lifetime_value, total_purchases, last_purchase_date, first_purchase_date, average_order_value, credit_score, risk_score, satisfaction_score, net_promoter_score, acquisition_date, last_contact_date, birthday, metadata, custom_fields, tags, external_id, source_system, created_at, updated_at, tenant_id, deleted_at, is_active, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: invoice_line_items; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.invoice_line_items (line_item_id, invoice_id, description, quantity, unit_price, total_price, product_id, subscription_id, tax_rate, tax_amount, discount_percentage, discount_amount, extra_data) FROM stdin;
\.


--
-- Data for Name: invoices; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.invoices (invoice_id, invoice_number, idempotency_key, customer_id, billing_email, billing_address, issue_date, due_date, currency, subtotal, tax_amount, discount_amount, total_amount, total_credits_applied, remaining_balance, credit_applications, status, payment_status, subscription_id, proforma_invoice_id, notes, internal_notes, extra_data, paid_at, voided_at, tenant_id, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: manual_payments; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.manual_payments (id, payment_reference, external_reference, customer_id, invoice_id, bank_account_id, payment_method, amount, currency, payment_date, received_date, cleared_date, cash_register_id, cashier_name, check_number, check_bank_name, sender_name, sender_bank, sender_account_last_four, mobile_number, mobile_provider, status, reconciled, reconciled_at, reconciled_by, notes, receipt_url, attachments, recorded_by, approved_by, approved_at, meta_data, tenant_id, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: payment_invoices; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.payment_invoices (payment_id, invoice_id, amount_applied, applied_at) FROM stdin;
\.


--
-- Data for Name: payment_methods; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.payment_methods (payment_method_id, customer_id, type, status, provider, provider_payment_method_id, display_name, last_four, brand, expiry_month, expiry_year, bank_name, account_type, routing_number_last_four, is_default, auto_pay_enabled, verified_at, extra_data, tenant_id, created_at, updated_at, deleted_at, is_active) FROM stdin;
\.


--
-- Data for Name: payment_reconciliations; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.payment_reconciliations (id, reconciliation_date, period_start, period_end, bank_account_id, opening_balance, closing_balance, statement_balance, total_deposits, total_withdrawals, unreconciled_count, discrepancy_amount, status, completed_by, completed_at, approved_by, approved_at, notes, statement_file_url, reconciled_items, meta_data, tenant_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.payments (payment_id, idempotency_key, amount, currency, customer_id, status, payment_method_type, payment_method_details, provider, provider_payment_id, provider_fee, failure_reason, retry_count, next_retry_at, processed_at, extra_data, tenant_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: permission_grants; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.permission_grants (id, user_id, role_id, permission_id, action, granted_by, reason, created_at, expires_at, metadata) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.permissions (id, name, display_name, description, category, parent_id, is_active, is_system, metadata, created_at, updated_at) FROM stdin;
ca35c51a-f938-48c2-a70d-94632e15bd70	admin.access	Admin Access	Access admin features	admin	\N	t	t	\N	2025-09-28 19:55:55.239823+00	2025-09-28 19:55:55.239823+00
fbb6185c-50ec-46a5-8a16-d72addf2ad63	user.profile.read	Read Profile	Read own profile	customer	\N	t	t	\N	2025-09-28 19:55:55.239823+00	2025-09-28 19:55:55.239823+00
7d5d2436-b2c6-4d2c-98e9-61d4e599077e	user.profile.write	Update Profile	Update own profile	customer	\N	t	t	\N	2025-09-28 19:55:55.239823+00	2025-09-28 19:55:55.239823+00
\.


--
-- Data for Name: role_hierarchy; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.role_hierarchy (id, parent_role_id, child_role_id, created_at) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.role_permissions (role_id, permission_id, granted_at) FROM stdin;
8a4704f7-adeb-4559-98eb-790b9cd2cee9	ca35c51a-f938-48c2-a70d-94632e15bd70	2025-09-28 19:55:55.761303+00
19e884bb-bdda-45a4-a8c2-390b85e6e3ed	7d5d2436-b2c6-4d2c-98e9-61d4e599077e	2025-09-28 19:55:55.761303+00
19e884bb-bdda-45a4-a8c2-390b85e6e3ed	fbb6185c-50ec-46a5-8a16-d72addf2ad63	2025-09-28 19:55:55.761303+00
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.roles (id, name, display_name, description, parent_id, priority, is_active, is_system, is_default, max_users, metadata, created_at, updated_at) FROM stdin;
8a4704f7-adeb-4559-98eb-790b9cd2cee9	admin	Administrator	Full system access	\N	100	t	t	f	\N	\N	2025-09-28 19:55:55.239823+00	2025-09-28 19:55:55.239823+00
19e884bb-bdda-45a4-a8c2-390b85e6e3ed	user	User	Standard user access	\N	10	t	t	t	\N	\N	2025-09-28 19:55:55.239823+00	2025-09-28 19:55:55.239823+00
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.transactions (transaction_id, amount, currency, transaction_type, description, customer_id, invoice_id, payment_id, credit_note_id, transaction_date, extra_data, tenant_id) FROM stdin;
\.


--
-- Data for Name: user_permissions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.user_permissions (user_id, permission_id, granted, granted_at, granted_by, expires_at, reason) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.user_roles (user_id, role_id, granted_at, granted_by, expires_at, metadata) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.users (id, username, email, password_hash, full_name, phone_number, is_active, is_verified, is_superuser, roles, permissions, mfa_enabled, mfa_secret, last_login, last_login_ip, failed_login_attempts, locked_until, metadata, created_at, updated_at, tenant_id) FROM stdin;
ede5c137-8d6d-431f-bef1-91047dcd220c	test	test@example.com	$2b$12$OkvBcDn7bXeBaHd/lHB.8eSHivQy15ojxsDEc/A74jbogk38qdfMa	\N	\N	t	t	f	["user"]	["user.profile.read", "user.profile.write"]	f	\N	2025-09-28 19:56:11.429609	127.0.0.1	0	\N	{}	2025-09-28 19:55:55.75697+00	2025-09-28 21:33:05.925045+00	\N
5051d72d-acc8-49bf-addd-1fed118a4a56	admin	admin@example.com	$2b$12$VIVAsyDQZVfIk2JI.W4A9.mItBoFODkQlqEgfCrQv3ZcVE4TK3U3S	\N	\N	t	t	t	["admin", "user"]	["admin.access", "user.profile.read", "user.profile.write"]	f	\N	2025-09-29 11:32:57.468888	::1	0	\N	{}	2025-09-28 19:55:55.756964+00	2025-09-29 11:32:57.471566+00	\N
\.


--
-- Data for Name: webhook_deliveries; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.webhook_deliveries (id, subscription_id, event_type, event_id, event_data, status, response_code, response_body, error_message, attempt_number, next_retry_at, duration_ms, tenant_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: webhook_subscriptions; Type: TABLE DATA; Schema: public; Owner: dotmac_user
--

COPY public.webhook_subscriptions (id, url, description, events, secret, headers, is_active, retry_enabled, max_retries, timeout_seconds, success_count, failure_count, last_triggered_at, last_success_at, last_failure_at, custom_metadata, tenant_id, created_at, updated_at) FROM stdin;
\.


--
-- Name: cash_registers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dotmac_user
--

SELECT pg_catalog.setval('public.cash_registers_id_seq', 1, false);


--
-- Name: company_bank_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dotmac_user
--

SELECT pg_catalog.setval('public.company_bank_accounts_id_seq', 1, false);


--
-- Name: manual_payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dotmac_user
--

SELECT pg_catalog.setval('public.manual_payments_id_seq', 1, false);


--
-- Name: payment_reconciliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dotmac_user
--

SELECT pg_catalog.setval('public.payment_reconciliations_id_seq', 1, false);


--
-- Name: audit_activities audit_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.audit_activities
    ADD CONSTRAINT audit_activities_pkey PRIMARY KEY (id);


--
-- Name: billing_pricing_rules billing_pricing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_pricing_rules
    ADD CONSTRAINT billing_pricing_rules_pkey PRIMARY KEY (rule_id, id);


--
-- Name: billing_product_categories billing_product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_product_categories
    ADD CONSTRAINT billing_product_categories_pkey PRIMARY KEY (category_id, id);


--
-- Name: billing_products billing_products_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_products
    ADD CONSTRAINT billing_products_pkey PRIMARY KEY (product_id, id);


--
-- Name: billing_rule_usage billing_rule_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_rule_usage
    ADD CONSTRAINT billing_rule_usage_pkey PRIMARY KEY (usage_id, id);


--
-- Name: billing_subscription_events billing_subscription_events_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_subscription_events
    ADD CONSTRAINT billing_subscription_events_pkey PRIMARY KEY (event_id, id);


--
-- Name: billing_subscription_plans billing_subscription_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_subscription_plans
    ADD CONSTRAINT billing_subscription_plans_pkey PRIMARY KEY (plan_id, id);


--
-- Name: billing_subscriptions billing_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.billing_subscriptions
    ADD CONSTRAINT billing_subscriptions_pkey PRIMARY KEY (subscription_id, id);


--
-- Name: cash_reconciliations cash_reconciliations_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_reconciliations
    ADD CONSTRAINT cash_reconciliations_pkey PRIMARY KEY (id);


--
-- Name: cash_registers cash_registers_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_registers
    ADD CONSTRAINT cash_registers_pkey PRIMARY KEY (id);


--
-- Name: cash_registers cash_registers_register_id_key; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_registers
    ADD CONSTRAINT cash_registers_register_id_key UNIQUE (register_id);


--
-- Name: cash_transactions cash_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_transactions
    ADD CONSTRAINT cash_transactions_pkey PRIMARY KEY (id);


--
-- Name: communication_logs communication_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.communication_logs
    ADD CONSTRAINT communication_logs_pkey PRIMARY KEY (id);


--
-- Name: communication_stats communication_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.communication_stats
    ADD CONSTRAINT communication_stats_pkey PRIMARY KEY (id);


--
-- Name: communication_templates communication_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.communication_templates
    ADD CONSTRAINT communication_templates_pkey PRIMARY KEY (id);


--
-- Name: company_bank_accounts company_bank_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.company_bank_accounts
    ADD CONSTRAINT company_bank_accounts_pkey PRIMARY KEY (id);


--
-- Name: contact_activities contact_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_activities
    ADD CONSTRAINT contact_activities_pkey PRIMARY KEY (id);


--
-- Name: contact_field_definitions contact_field_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_field_definitions
    ADD CONSTRAINT contact_field_definitions_pkey PRIMARY KEY (id);


--
-- Name: contact_label_definitions contact_label_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_label_definitions
    ADD CONSTRAINT contact_label_definitions_pkey PRIMARY KEY (id);


--
-- Name: contact_methods contact_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_methods
    ADD CONSTRAINT contact_methods_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: credit_applications credit_applications_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_applications
    ADD CONSTRAINT credit_applications_pkey PRIMARY KEY (application_id);


--
-- Name: credit_note_line_items credit_note_line_items_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_note_line_items
    ADD CONSTRAINT credit_note_line_items_pkey PRIMARY KEY (line_item_id);


--
-- Name: credit_notes credit_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_notes
    ADD CONSTRAINT credit_notes_pkey PRIMARY KEY (credit_note_id);


--
-- Name: customer_activities customer_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_activities
    ADD CONSTRAINT customer_activities_pkey PRIMARY KEY (id);


--
-- Name: customer_credits customer_credits_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_credits
    ADD CONSTRAINT customer_credits_pkey PRIMARY KEY (customer_id, tenant_id);


--
-- Name: customer_notes customer_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_notes
    ADD CONSTRAINT customer_notes_pkey PRIMARY KEY (id);


--
-- Name: customer_segments customer_segments_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_segments
    ADD CONSTRAINT customer_segments_pkey PRIMARY KEY (id);


--
-- Name: customer_tags_association customer_tags_association_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_tags_association
    ADD CONSTRAINT customer_tags_association_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: invoice_line_items invoice_line_items_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.invoice_line_items
    ADD CONSTRAINT invoice_line_items_pkey PRIMARY KEY (line_item_id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (invoice_id);


--
-- Name: manual_payments manual_payments_payment_reference_key; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.manual_payments
    ADD CONSTRAINT manual_payments_payment_reference_key UNIQUE (payment_reference);


--
-- Name: manual_payments manual_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.manual_payments
    ADD CONSTRAINT manual_payments_pkey PRIMARY KEY (id);


--
-- Name: payment_invoices payment_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_invoices
    ADD CONSTRAINT payment_invoices_pkey PRIMARY KEY (payment_id, invoice_id);


--
-- Name: payment_methods payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_pkey PRIMARY KEY (payment_method_id);


--
-- Name: payment_reconciliations payment_reconciliations_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_reconciliations
    ADD CONSTRAINT payment_reconciliations_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (payment_id);


--
-- Name: permission_grants permission_grants_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permission_grants
    ADD CONSTRAINT permission_grants_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: role_hierarchy role_hierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_hierarchy
    ADD CONSTRAINT role_hierarchy_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: contact_to_labels uq_contact_label; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_to_labels
    ADD CONSTRAINT uq_contact_label PRIMARY KEY (contact_id, label_definition_id);


--
-- Name: contact_methods uq_contact_method; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_methods
    ADD CONSTRAINT uq_contact_method UNIQUE (contact_id, type, value);


--
-- Name: credit_notes uq_credit_note_idempotency; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_notes
    ADD CONSTRAINT uq_credit_note_idempotency UNIQUE (tenant_id, idempotency_key);


--
-- Name: customer_tags_association uq_customer_tag; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_tags_association
    ADD CONSTRAINT uq_customer_tag UNIQUE (customer_id, tag_name);


--
-- Name: invoices uq_invoice_idempotency; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT uq_invoice_idempotency UNIQUE (tenant_id, idempotency_key);


--
-- Name: payments uq_payment_idempotency; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT uq_payment_idempotency UNIQUE (tenant_id, idempotency_key);


--
-- Name: role_hierarchy uq_role_hierarchy; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_hierarchy
    ADD CONSTRAINT uq_role_hierarchy UNIQUE (parent_role_id, child_role_id);


--
-- Name: role_permissions uq_role_permission; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uq_role_permission PRIMARY KEY (role_id, permission_id);


--
-- Name: customers uq_tenant_customer_number; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT uq_tenant_customer_number UNIQUE (tenant_id, customer_number);


--
-- Name: customers uq_tenant_email; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT uq_tenant_email UNIQUE (tenant_id, email);


--
-- Name: contact_field_definitions uq_tenant_field_key; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_field_definitions
    ADD CONSTRAINT uq_tenant_field_key UNIQUE (tenant_id, field_key);


--
-- Name: contact_label_definitions uq_tenant_label_slug; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_label_definitions
    ADD CONSTRAINT uq_tenant_label_slug UNIQUE (tenant_id, slug);


--
-- Name: customer_segments uq_tenant_segment_name; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_segments
    ADD CONSTRAINT uq_tenant_segment_name UNIQUE (tenant_id, name);


--
-- Name: user_permissions uq_user_permission; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT uq_user_permission PRIMARY KEY (user_id, permission_id);


--
-- Name: user_roles uq_user_role; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT uq_user_role PRIMARY KEY (user_id, role_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: webhook_deliveries webhook_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT webhook_deliveries_pkey PRIMARY KEY (id);


--
-- Name: webhook_subscriptions webhook_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.webhook_subscriptions
    ADD CONSTRAINT webhook_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: idx_company_bank_primary; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_company_bank_primary ON public.company_bank_accounts USING btree (tenant_id, is_primary);


--
-- Name: idx_company_bank_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_company_bank_status ON public.company_bank_accounts USING btree (status);


--
-- Name: idx_company_bank_tenant; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_company_bank_tenant ON public.company_bank_accounts USING btree (tenant_id);


--
-- Name: idx_credit_application_tenant_target; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_credit_application_tenant_target ON public.credit_applications USING btree (tenant_id, applied_to_id);


--
-- Name: idx_credit_note_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_credit_note_tenant_customer ON public.credit_notes USING btree (tenant_id, customer_id);


--
-- Name: idx_credit_note_tenant_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_credit_note_tenant_status ON public.credit_notes USING btree (tenant_id, status);


--
-- Name: idx_customer_credit_tenant; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_customer_credit_tenant ON public.customer_credits USING btree (tenant_id, customer_id);


--
-- Name: idx_invoice_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_invoice_tenant_customer ON public.invoices USING btree (tenant_id, customer_id);


--
-- Name: idx_invoice_tenant_due_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_invoice_tenant_due_date ON public.invoices USING btree (tenant_id, due_date);


--
-- Name: idx_invoice_tenant_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_invoice_tenant_status ON public.invoices USING btree (tenant_id, status);


--
-- Name: idx_manual_payment_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_customer ON public.manual_payments USING btree (customer_id);


--
-- Name: idx_manual_payment_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_date ON public.manual_payments USING btree (payment_date);


--
-- Name: idx_manual_payment_invoice; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_invoice ON public.manual_payments USING btree (invoice_id);


--
-- Name: idx_manual_payment_method; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_method ON public.manual_payments USING btree (payment_method);


--
-- Name: idx_manual_payment_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_status ON public.manual_payments USING btree (status);


--
-- Name: idx_manual_payment_tenant; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_manual_payment_tenant ON public.manual_payments USING btree (tenant_id);


--
-- Name: idx_payment_method_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_payment_method_tenant_customer ON public.payment_methods USING btree (tenant_id, customer_id);


--
-- Name: idx_payment_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_payment_tenant_customer ON public.payments USING btree (tenant_id, customer_id);


--
-- Name: idx_payment_tenant_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_payment_tenant_status ON public.payments USING btree (tenant_id, status);


--
-- Name: idx_reconciliation_bank; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_reconciliation_bank ON public.payment_reconciliations USING btree (bank_account_id);


--
-- Name: idx_reconciliation_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_reconciliation_date ON public.payment_reconciliations USING btree (reconciliation_date);


--
-- Name: idx_reconciliation_tenant; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_reconciliation_tenant ON public.payment_reconciliations USING btree (tenant_id);


--
-- Name: idx_transaction_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_transaction_tenant_customer ON public.transactions USING btree (tenant_id, customer_id);


--
-- Name: idx_transaction_tenant_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX idx_transaction_tenant_date ON public.transactions USING btree (tenant_id, transaction_date);


--
-- Name: ix_activity_customer_time; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_activity_customer_time ON public.customer_activities USING btree (customer_id, created_at);


--
-- Name: ix_audit_activities_activity_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_activity_type ON public.audit_activities USING btree (activity_type);


--
-- Name: ix_audit_activities_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_id ON public.audit_activities USING btree (id);


--
-- Name: ix_audit_activities_severity; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_severity ON public.audit_activities USING btree (severity);


--
-- Name: ix_audit_activities_severity_timestamp; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_severity_timestamp ON public.audit_activities USING btree (severity, "timestamp");


--
-- Name: ix_audit_activities_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_tenant_id ON public.audit_activities USING btree (tenant_id);


--
-- Name: ix_audit_activities_tenant_timestamp; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_tenant_timestamp ON public.audit_activities USING btree (tenant_id, "timestamp");


--
-- Name: ix_audit_activities_timestamp; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_timestamp ON public.audit_activities USING btree ("timestamp");


--
-- Name: ix_audit_activities_type_timestamp; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_type_timestamp ON public.audit_activities USING btree (activity_type, "timestamp");


--
-- Name: ix_audit_activities_user_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_user_id ON public.audit_activities USING btree (user_id);


--
-- Name: ix_audit_activities_user_timestamp; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_audit_activities_user_timestamp ON public.audit_activities USING btree (user_id, "timestamp");


--
-- Name: ix_billing_categories_sort; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_categories_sort ON public.billing_product_categories USING btree (tenant_id, sort_order);


--
-- Name: ix_billing_categories_tenant_name; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_billing_categories_tenant_name ON public.billing_product_categories USING btree (tenant_id, name);


--
-- Name: ix_billing_events_created; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_events_created ON public.billing_subscription_events USING btree (created_at);


--
-- Name: ix_billing_events_tenant_subscription; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_events_tenant_subscription ON public.billing_subscription_events USING btree (tenant_id, subscription_id);


--
-- Name: ix_billing_events_tenant_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_events_tenant_type ON public.billing_subscription_events USING btree (tenant_id, event_type);


--
-- Name: ix_billing_plans_tenant_active; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_plans_tenant_active ON public.billing_subscription_plans USING btree (tenant_id, is_active);


--
-- Name: ix_billing_plans_tenant_product; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_plans_tenant_product ON public.billing_subscription_plans USING btree (tenant_id, product_id);


--
-- Name: ix_billing_pricing_rules_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_pricing_rules_tenant_id ON public.billing_pricing_rules USING btree (tenant_id);


--
-- Name: ix_billing_product_categories_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_product_categories_tenant_id ON public.billing_product_categories USING btree (tenant_id);


--
-- Name: ix_billing_products_tenant_active; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_products_tenant_active ON public.billing_products USING btree (tenant_id, is_active);


--
-- Name: ix_billing_products_tenant_category; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_products_tenant_category ON public.billing_products USING btree (tenant_id, category);


--
-- Name: ix_billing_products_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_products_tenant_id ON public.billing_products USING btree (tenant_id);


--
-- Name: ix_billing_products_tenant_sku; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_billing_products_tenant_sku ON public.billing_products USING btree (tenant_id, sku);


--
-- Name: ix_billing_products_tenant_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_products_tenant_type ON public.billing_products USING btree (tenant_id, product_type);


--
-- Name: ix_billing_rule_usage_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rule_usage_tenant_customer ON public.billing_rule_usage USING btree (tenant_id, customer_id);


--
-- Name: ix_billing_rule_usage_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rule_usage_tenant_id ON public.billing_rule_usage USING btree (tenant_id);


--
-- Name: ix_billing_rule_usage_tenant_rule; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rule_usage_tenant_rule ON public.billing_rule_usage USING btree (tenant_id, rule_id);


--
-- Name: ix_billing_rule_usage_used_at; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rule_usage_used_at ON public.billing_rule_usage USING btree (used_at);


--
-- Name: ix_billing_rules_starts_ends; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rules_starts_ends ON public.billing_pricing_rules USING btree (starts_at, ends_at);


--
-- Name: ix_billing_rules_tenant_active; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_rules_tenant_active ON public.billing_pricing_rules USING btree (tenant_id, is_active);


--
-- Name: ix_billing_subscription_events_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscription_events_tenant_id ON public.billing_subscription_events USING btree (tenant_id);


--
-- Name: ix_billing_subscription_plans_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscription_plans_tenant_id ON public.billing_subscription_plans USING btree (tenant_id);


--
-- Name: ix_billing_subscriptions_period_end; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscriptions_period_end ON public.billing_subscriptions USING btree (current_period_end);


--
-- Name: ix_billing_subscriptions_tenant_customer; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscriptions_tenant_customer ON public.billing_subscriptions USING btree (tenant_id, customer_id);


--
-- Name: ix_billing_subscriptions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscriptions_tenant_id ON public.billing_subscriptions USING btree (tenant_id);


--
-- Name: ix_billing_subscriptions_tenant_plan; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscriptions_tenant_plan ON public.billing_subscriptions USING btree (tenant_id, plan_id);


--
-- Name: ix_billing_subscriptions_tenant_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_billing_subscriptions_tenant_status ON public.billing_subscriptions USING btree (tenant_id, status);


--
-- Name: ix_cash_reconciliations_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_cash_reconciliations_tenant_id ON public.cash_reconciliations USING btree (tenant_id);


--
-- Name: ix_cash_registers_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_cash_registers_tenant_id ON public.cash_registers USING btree (tenant_id);


--
-- Name: ix_cash_transactions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_cash_transactions_tenant_id ON public.cash_transactions USING btree (tenant_id);


--
-- Name: ix_communication_logs_job_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_job_id ON public.communication_logs USING btree (job_id);


--
-- Name: ix_communication_logs_recipient; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_recipient ON public.communication_logs USING btree (recipient);


--
-- Name: ix_communication_logs_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_status ON public.communication_logs USING btree (status);


--
-- Name: ix_communication_logs_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_tenant_id ON public.communication_logs USING btree (tenant_id);


--
-- Name: ix_communication_logs_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_type ON public.communication_logs USING btree (type);


--
-- Name: ix_communication_logs_user_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_logs_user_id ON public.communication_logs USING btree (user_id);


--
-- Name: ix_communication_stats_stats_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_stats_stats_date ON public.communication_stats USING btree (stats_date);


--
-- Name: ix_communication_stats_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_stats_tenant_id ON public.communication_stats USING btree (tenant_id);


--
-- Name: ix_communication_stats_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_stats_type ON public.communication_stats USING btree (type);


--
-- Name: ix_communication_templates_name; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_communication_templates_name ON public.communication_templates USING btree (name);


--
-- Name: ix_communication_templates_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_communication_templates_tenant_id ON public.communication_templates USING btree (tenant_id);


--
-- Name: ix_company_bank_accounts_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_company_bank_accounts_tenant_id ON public.company_bank_accounts USING btree (tenant_id);


--
-- Name: ix_contact_activities_activity_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_activities_activity_date ON public.contact_activities USING btree (activity_date);


--
-- Name: ix_contact_activities_activity_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_activities_activity_type ON public.contact_activities USING btree (activity_type);


--
-- Name: ix_contact_activities_contact_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_activities_contact_id ON public.contact_activities USING btree (contact_id);


--
-- Name: ix_contact_activities_performed_by; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_activities_performed_by ON public.contact_activities USING btree (performed_by);


--
-- Name: ix_contact_field_definitions_field_group; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_field_definitions_field_group ON public.contact_field_definitions USING btree (field_group);


--
-- Name: ix_contact_field_definitions_field_key; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_field_definitions_field_key ON public.contact_field_definitions USING btree (field_key);


--
-- Name: ix_contact_field_definitions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_field_definitions_tenant_id ON public.contact_field_definitions USING btree (tenant_id);


--
-- Name: ix_contact_label_definitions_category; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_label_definitions_category ON public.contact_label_definitions USING btree (category);


--
-- Name: ix_contact_label_definitions_slug; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_label_definitions_slug ON public.contact_label_definitions USING btree (slug);


--
-- Name: ix_contact_label_definitions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_label_definitions_tenant_id ON public.contact_label_definitions USING btree (tenant_id);


--
-- Name: ix_contact_labels_contact_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_labels_contact_id ON public.contact_to_labels USING btree (contact_id);


--
-- Name: ix_contact_labels_label_definition_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_labels_label_definition_id ON public.contact_to_labels USING btree (label_definition_id);


--
-- Name: ix_contact_methods_contact_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_methods_contact_id ON public.contact_methods USING btree (contact_id);


--
-- Name: ix_contact_methods_is_primary; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_methods_is_primary ON public.contact_methods USING btree (is_primary);


--
-- Name: ix_contact_methods_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_methods_type ON public.contact_methods USING btree (type);


--
-- Name: ix_contact_methods_value; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contact_methods_value ON public.contact_methods USING btree (value);


--
-- Name: ix_contacts_company; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_company ON public.contacts USING btree (company);


--
-- Name: ix_contacts_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_customer_id ON public.contacts USING btree (customer_id);


--
-- Name: ix_contacts_deleted_at; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_deleted_at ON public.contacts USING btree (deleted_at);


--
-- Name: ix_contacts_display_name; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_display_name ON public.contacts USING btree (display_name);


--
-- Name: ix_contacts_owner_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_owner_id ON public.contacts USING btree (owner_id);


--
-- Name: ix_contacts_stage; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_stage ON public.contacts USING btree (stage);


--
-- Name: ix_contacts_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_status ON public.contacts USING btree (status);


--
-- Name: ix_contacts_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_contacts_tenant_id ON public.contacts USING btree (tenant_id);


--
-- Name: ix_credit_applications_applied_to_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_applications_applied_to_id ON public.credit_applications USING btree (applied_to_id);


--
-- Name: ix_credit_applications_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_applications_tenant_id ON public.credit_applications USING btree (tenant_id);


--
-- Name: ix_credit_notes_credit_note_number; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_credit_notes_credit_note_number ON public.credit_notes USING btree (credit_note_number);


--
-- Name: ix_credit_notes_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_notes_customer_id ON public.credit_notes USING btree (customer_id);


--
-- Name: ix_credit_notes_idempotency_key; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_notes_idempotency_key ON public.credit_notes USING btree (idempotency_key);


--
-- Name: ix_credit_notes_invoice_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_notes_invoice_id ON public.credit_notes USING btree (invoice_id);


--
-- Name: ix_credit_notes_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_notes_status ON public.credit_notes USING btree (status);


--
-- Name: ix_credit_notes_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_credit_notes_tenant_id ON public.credit_notes USING btree (tenant_id);


--
-- Name: ix_customer_activities_activity_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_activities_activity_type ON public.customer_activities USING btree (activity_type);


--
-- Name: ix_customer_activities_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_activities_tenant_id ON public.customer_activities USING btree (tenant_id);


--
-- Name: ix_customer_location; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_location ON public.customers USING btree (country, state_province, city);


--
-- Name: ix_customer_notes_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_notes_tenant_id ON public.customer_notes USING btree (tenant_id);


--
-- Name: ix_customer_search; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_search ON public.customers USING btree (first_name, last_name, company_name);


--
-- Name: ix_customer_segments_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_segments_tenant_id ON public.customer_segments USING btree (tenant_id);


--
-- Name: ix_customer_status_tier; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_status_tier ON public.customers USING btree (status, tier);


--
-- Name: ix_customer_tags_association_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customer_tags_association_tenant_id ON public.customer_tags_association USING btree (tenant_id);


--
-- Name: ix_customers_customer_number; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_customers_customer_number ON public.customers USING btree (customer_number);


--
-- Name: ix_customers_customer_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_customer_type ON public.customers USING btree (customer_type);


--
-- Name: ix_customers_email; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_email ON public.customers USING btree (email);


--
-- Name: ix_customers_external_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_external_id ON public.customers USING btree (external_id);


--
-- Name: ix_customers_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_status ON public.customers USING btree (status);


--
-- Name: ix_customers_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_tenant_id ON public.customers USING btree (tenant_id);


--
-- Name: ix_customers_tier; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_customers_tier ON public.customers USING btree (tier);


--
-- Name: ix_invoices_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_customer_id ON public.invoices USING btree (customer_id);


--
-- Name: ix_invoices_due_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_due_date ON public.invoices USING btree (due_date);


--
-- Name: ix_invoices_idempotency_key; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_idempotency_key ON public.invoices USING btree (idempotency_key);


--
-- Name: ix_invoices_invoice_number; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_invoices_invoice_number ON public.invoices USING btree (invoice_number);


--
-- Name: ix_invoices_payment_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_payment_status ON public.invoices USING btree (payment_status);


--
-- Name: ix_invoices_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_status ON public.invoices USING btree (status);


--
-- Name: ix_invoices_subscription_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_subscription_id ON public.invoices USING btree (subscription_id);


--
-- Name: ix_invoices_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_invoices_tenant_id ON public.invoices USING btree (tenant_id);


--
-- Name: ix_manual_payments_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_manual_payments_tenant_id ON public.manual_payments USING btree (tenant_id);


--
-- Name: ix_note_customer_created; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_note_customer_created ON public.customer_notes USING btree (customer_id, created_at);


--
-- Name: ix_payment_methods_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payment_methods_customer_id ON public.payment_methods USING btree (customer_id);


--
-- Name: ix_payment_methods_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payment_methods_tenant_id ON public.payment_methods USING btree (tenant_id);


--
-- Name: ix_payment_reconciliations_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payment_reconciliations_tenant_id ON public.payment_reconciliations USING btree (tenant_id);


--
-- Name: ix_payments_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payments_customer_id ON public.payments USING btree (customer_id);


--
-- Name: ix_payments_idempotency_key; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payments_idempotency_key ON public.payments USING btree (idempotency_key);


--
-- Name: ix_payments_provider_payment_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payments_provider_payment_id ON public.payments USING btree (provider_payment_id);


--
-- Name: ix_payments_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payments_status ON public.payments USING btree (status);


--
-- Name: ix_payments_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_payments_tenant_id ON public.payments USING btree (tenant_id);


--
-- Name: ix_permission_grants_created_at; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_permission_grants_created_at ON public.permission_grants USING btree (created_at);


--
-- Name: ix_permission_grants_granted_by; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_permission_grants_granted_by ON public.permission_grants USING btree (granted_by);


--
-- Name: ix_permission_grants_user_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_permission_grants_user_id ON public.permission_grants USING btree (user_id);


--
-- Name: ix_permissions_name; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);


--
-- Name: ix_role_hierarchy_child; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_role_hierarchy_child ON public.role_hierarchy USING btree (child_role_id);


--
-- Name: ix_role_hierarchy_parent; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_role_hierarchy_parent ON public.role_hierarchy USING btree (parent_role_id);


--
-- Name: ix_role_permissions_role_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_role_permissions_role_id ON public.role_permissions USING btree (role_id);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_tag_name_category; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_tag_name_category ON public.customer_tags_association USING btree (tag_name, tag_category);


--
-- Name: ix_transactions_credit_note_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_credit_note_id ON public.transactions USING btree (credit_note_id);


--
-- Name: ix_transactions_customer_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_customer_id ON public.transactions USING btree (customer_id);


--
-- Name: ix_transactions_invoice_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_invoice_id ON public.transactions USING btree (invoice_id);


--
-- Name: ix_transactions_payment_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_payment_id ON public.transactions USING btree (payment_id);


--
-- Name: ix_transactions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_tenant_id ON public.transactions USING btree (tenant_id);


--
-- Name: ix_transactions_transaction_date; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_transaction_date ON public.transactions USING btree (transaction_date);


--
-- Name: ix_transactions_transaction_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_transactions_transaction_type ON public.transactions USING btree (transaction_type);


--
-- Name: ix_user_permissions_user_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_user_permissions_user_id ON public.user_permissions USING btree (user_id);


--
-- Name: ix_user_roles_expires_at; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_user_roles_expires_at ON public.user_roles USING btree (expires_at);


--
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_user_roles_user_id ON public.user_roles USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_users_tenant_id ON public.users USING btree (tenant_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_webhook_deliveries_event_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_deliveries_event_id ON public.webhook_deliveries USING btree (event_id);


--
-- Name: ix_webhook_deliveries_event_type; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_deliveries_event_type ON public.webhook_deliveries USING btree (event_type);


--
-- Name: ix_webhook_deliveries_status; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_deliveries_status ON public.webhook_deliveries USING btree (status);


--
-- Name: ix_webhook_deliveries_subscription_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_deliveries_subscription_id ON public.webhook_deliveries USING btree (subscription_id);


--
-- Name: ix_webhook_deliveries_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_deliveries_tenant_id ON public.webhook_deliveries USING btree (tenant_id);


--
-- Name: ix_webhook_subscriptions_tenant_id; Type: INDEX; Schema: public; Owner: dotmac_user
--

CREATE INDEX ix_webhook_subscriptions_tenant_id ON public.webhook_subscriptions USING btree (tenant_id);


--
-- Name: cash_reconciliations cash_reconciliations_register_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_reconciliations
    ADD CONSTRAINT cash_reconciliations_register_id_fkey FOREIGN KEY (register_id) REFERENCES public.cash_registers(register_id);


--
-- Name: cash_transactions cash_transactions_register_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.cash_transactions
    ADD CONSTRAINT cash_transactions_register_id_fkey FOREIGN KEY (register_id) REFERENCES public.cash_registers(register_id);


--
-- Name: contact_activities contact_activities_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_activities
    ADD CONSTRAINT contact_activities_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id) ON DELETE CASCADE;


--
-- Name: contact_activities contact_activities_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_activities
    ADD CONSTRAINT contact_activities_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(id);


--
-- Name: contact_field_definitions contact_field_definitions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_field_definitions
    ADD CONSTRAINT contact_field_definitions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: contact_label_definitions contact_label_definitions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_label_definitions
    ADD CONSTRAINT contact_label_definitions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: contact_methods contact_methods_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_methods
    ADD CONSTRAINT contact_methods_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id) ON DELETE CASCADE;


--
-- Name: contact_methods contact_methods_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_methods
    ADD CONSTRAINT contact_methods_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id);


--
-- Name: contact_to_labels contact_to_labels_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_to_labels
    ADD CONSTRAINT contact_to_labels_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: contact_to_labels contact_to_labels_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_to_labels
    ADD CONSTRAINT contact_to_labels_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id) ON DELETE CASCADE;


--
-- Name: contact_to_labels contact_to_labels_label_definition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contact_to_labels
    ADD CONSTRAINT contact_to_labels_label_definition_id_fkey FOREIGN KEY (label_definition_id) REFERENCES public.contact_label_definitions(id) ON DELETE CASCADE;


--
-- Name: contacts contacts_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id);


--
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: credit_applications credit_applications_credit_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_applications
    ADD CONSTRAINT credit_applications_credit_note_id_fkey FOREIGN KEY (credit_note_id) REFERENCES public.credit_notes(credit_note_id);


--
-- Name: credit_note_line_items credit_note_line_items_credit_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.credit_note_line_items
    ADD CONSTRAINT credit_note_line_items_credit_note_id_fkey FOREIGN KEY (credit_note_id) REFERENCES public.credit_notes(credit_note_id);


--
-- Name: customer_activities customer_activities_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_activities
    ADD CONSTRAINT customer_activities_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: customer_activities customer_activities_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_activities
    ADD CONSTRAINT customer_activities_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: customer_notes customer_notes_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_notes
    ADD CONSTRAINT customer_notes_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: customer_notes customer_notes_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_notes
    ADD CONSTRAINT customer_notes_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: customer_tags_association customer_tags_association_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customer_tags_association
    ADD CONSTRAINT customer_tags_association_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: customers customers_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: customers customers_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_segment_id_fkey FOREIGN KEY (segment_id) REFERENCES public.customer_segments(id) ON DELETE SET NULL;


--
-- Name: customers customers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: invoice_line_items invoice_line_items_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.invoice_line_items
    ADD CONSTRAINT invoice_line_items_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(invoice_id);


--
-- Name: payment_invoices payment_invoices_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_invoices
    ADD CONSTRAINT payment_invoices_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(invoice_id);


--
-- Name: payment_invoices payment_invoices_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_invoices
    ADD CONSTRAINT payment_invoices_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES public.payments(payment_id);


--
-- Name: payment_reconciliations payment_reconciliations_bank_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.payment_reconciliations
    ADD CONSTRAINT payment_reconciliations_bank_account_id_fkey FOREIGN KEY (bank_account_id) REFERENCES public.company_bank_accounts(id);


--
-- Name: permission_grants permission_grants_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permission_grants
    ADD CONSTRAINT permission_grants_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: permission_grants permission_grants_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permission_grants
    ADD CONSTRAINT permission_grants_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);


--
-- Name: permission_grants permission_grants_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permission_grants
    ADD CONSTRAINT permission_grants_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: permission_grants permission_grants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permission_grants
    ADD CONSTRAINT permission_grants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: permissions permissions_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.permissions(id);


--
-- Name: role_hierarchy role_hierarchy_child_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_hierarchy
    ADD CONSTRAINT role_hierarchy_child_role_id_fkey FOREIGN KEY (child_role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: role_hierarchy role_hierarchy_parent_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_hierarchy
    ADD CONSTRAINT role_hierarchy_parent_role_id_fkey FOREIGN KEY (parent_role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: roles roles_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.roles(id);


--
-- Name: user_permissions user_permissions_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: user_permissions user_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: user_permissions user_permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: webhook_deliveries webhook_deliveries_subscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dotmac_user
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT webhook_deliveries_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES public.webhook_subscriptions(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict qJI1MF59KkTSdEJJpnStYPZIsaDuj6fc965rBIzmZNazORaMMAOwYawqpxDlEna

