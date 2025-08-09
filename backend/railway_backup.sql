--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auto_cleanup_email_locks(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.auto_cleanup_email_locks() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- Clean up expired locks before inserting new ones
            PERFORM cleanup_expired_email_locks();
            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.auto_cleanup_email_locks() OWNER TO postgres;

--
-- Name: check_single_lock(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_single_lock() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- If this is an INSERT, check if table is empty
            IF TG_OP = 'INSERT' THEN
                IF EXISTS (SELECT 1 FROM email_processing_locks) THEN
                    RAISE EXCEPTION 'Another email processing lock already exists';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.check_single_lock() OWNER TO postgres;

--
-- Name: cleanup_expired_email_editing_locks(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cleanup_expired_email_editing_locks() RETURNS void
    LANGUAGE plpgsql
    AS $$
            BEGIN
                DELETE FROM email_editing_locks 
                WHERE expires_at < NOW();
            END;
            $$;


ALTER FUNCTION public.cleanup_expired_email_editing_locks() OWNER TO postgres;

--
-- Name: cleanup_expired_email_locks(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cleanup_expired_email_locks() RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- Delete locks that have expired
            DELETE FROM email_processing_locks 
            WHERE expires_at <= NOW();
            
            -- Delete stale locks (older than 5 minutes)
            DELETE FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '5 minutes';
        END;
        $$;


ALTER FUNCTION public.cleanup_expired_email_locks() OWNER TO postgres;

--
-- Name: cleanup_stale_user_activity(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cleanup_stale_user_activity() RETURNS void
    LANGUAGE plpgsql
    AS $$
            BEGIN
                DELETE FROM user_activity 
                WHERE last_activity < NOW() - INTERVAL '30 minutes';
            END;
            $$;


ALTER FUNCTION public.cleanup_stale_user_activity() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_drafts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ai_drafts (
    id integer NOT NULL,
    email_id integer,
    draft_content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sent_at timestamp without time zone,
    sent_by character varying(255),
    draft_type character varying(50) DEFAULT 'ai_generated'::character varying
);


ALTER TABLE public.ai_drafts OWNER TO postgres;

--
-- Name: TABLE ai_drafts; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.ai_drafts IS 'Stores AI-generated and user-edited draft responses';


--
-- Name: ai_drafts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ai_drafts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_drafts_id_seq OWNER TO postgres;

--
-- Name: ai_drafts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ai_drafts_id_seq OWNED BY public.ai_drafts.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    operation character varying(255) NOT NULL,
    details text,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address character varying(45)
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: TABLE audit_logs; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.audit_logs IS 'System activity tracking for security and performance monitoring';


--
-- Name: COLUMN audit_logs.user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.audit_logs.user_id IS 'Reference to users table (can be NULL for system operations)';


--
-- Name: COLUMN audit_logs.operation; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.audit_logs.operation IS 'Type of operation performed (login, logout, data_access, etc.)';


--
-- Name: COLUMN audit_logs.details; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.audit_logs.details IS 'Additional details about the operation';


--
-- Name: COLUMN audit_logs."timestamp"; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.audit_logs."timestamp" IS 'When the operation occurred';


--
-- Name: COLUMN audit_logs.ip_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.audit_logs.ip_address IS 'IP address of the user performing the operation';


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: bank_unmatched_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bank_unmatched_records (
    id integer NOT NULL,
    bl_number character varying(255),
    amount numeric,
    date date,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reason text
);


ALTER TABLE public.bank_unmatched_records OWNER TO postgres;

--
-- Name: bank_unmatched_records_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bank_unmatched_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bank_unmatched_records_id_seq OWNER TO postgres;

--
-- Name: bank_unmatched_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bank_unmatched_records_id_seq OWNED BY public.bank_unmatched_records.id;


--
-- Name: bill_of_lading; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bill_of_lading (
    id integer NOT NULL,
    customer_name text,
    customer_email text,
    customer_phone text,
    pdf_filename text,
    ocr_text text,
    shipper text,
    consignee text,
    port_of_loading text,
    port_of_discharge text,
    bl_number text,
    container_numbers text,
    service_fee numeric,
    receipt_filename text,
    status character varying(50),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    invoice_filename text,
    unique_number text,
    customer_username text,
    ctn_fee numeric,
    payment_link text,
    receipt_uploaded_at timestamp with time zone,
    completed_at timestamp with time zone,
    customer_invoice character varying(255),
    customer_packing_list character varying(255),
    flight_or_vessel text,
    product_description text,
    payment_method text DEFAULT 'not_selected_yet'::text,
    payment_status text DEFAULT 'pending'::text,
    reserve_amount numeric DEFAULT 0,
    reserve_status text DEFAULT 'not_applicable'::text,
    allinpay_85_received_at timestamp without time zone,
    payment_reference text,
    shipment_type character varying(20) DEFAULT 'ocean'::character varying,
    container_type character varying(20),
    container_count integer DEFAULT 1,
    total_weight_kg numeric(10,2),
    weight_unit character varying(10) DEFAULT 'kg'::character varying,
    pricing_method character varying(20) DEFAULT 'container'::character varying,
    base_ctn_fee numeric(10,2),
    base_service_fee numeric(10,2),
    calculated_ctn_fee numeric(10,2),
    calculated_service_fee numeric(10,2),
    ocr_confidence_score numeric(3,2),
    manual_override boolean DEFAULT false,
    override_reason text,
    override_by character varying(100),
    override_at timestamp with time zone,
    pricing_calculation_log jsonb,
    last_pricing_update timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    notify_party text,
    container_count_20ft integer DEFAULT 0,
    container_count_40ft integer DEFAULT 0,
    container_count_40ft_hc integer DEFAULT 0,
    payment_processed_by character varying(50),
    payment_processed_at timestamp with time zone,
    payment_source character varying(50),
    balance_applied numeric(10,2) DEFAULT 0
);


ALTER TABLE public.bill_of_lading OWNER TO postgres;

--
-- Name: COLUMN bill_of_lading.shipment_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.shipment_type IS 'Type of shipment: ocean, air, or loose_cargo';


--
-- Name: COLUMN bill_of_lading.container_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.container_type IS 'Container type: 20ft, 40ft, 40ft_hc, or loose_cargo';


--
-- Name: COLUMN bill_of_lading.pricing_method; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.pricing_method IS 'Method used for fee calculation: container, weight, or mixed';


--
-- Name: COLUMN bill_of_lading.manual_override; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.manual_override IS 'Flag indicating if fees were manually overridden';


--
-- Name: COLUMN bill_of_lading.pricing_calculation_log; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.pricing_calculation_log IS 'JSON log of how fees were calculated for audit purposes';


--
-- Name: COLUMN bill_of_lading.notify_party; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.notify_party IS 'Notify party information from BOL/AWB documents';


--
-- Name: COLUMN bill_of_lading.container_count_20ft; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.container_count_20ft IS 'Number of 20ft containers';


--
-- Name: COLUMN bill_of_lading.container_count_40ft; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.container_count_40ft IS 'Number of 40ft containers';


--
-- Name: COLUMN bill_of_lading.container_count_40ft_hc; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.bill_of_lading.container_count_40ft_hc IS 'Number of 40ft high cube containers';


--
-- Name: bill_of_lading_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bill_of_lading_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bill_of_lading_id_seq OWNER TO postgres;

--
-- Name: bill_of_lading_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bill_of_lading_id_seq OWNED BY public.bill_of_lading.id;


--
-- Name: customer_balance_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_balance_transactions (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    transaction_type character varying(20) NOT NULL,
    amount numeric(10,2) NOT NULL,
    reference_type character varying(50),
    reference_id integer,
    payment_source character varying(50),
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100),
    CONSTRAINT customer_balance_transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['credit'::character varying, 'debit'::character varying, 'adjustment'::character varying, 'application'::character varying])::text[])))
);


ALTER TABLE public.customer_balance_transactions OWNER TO postgres;

--
-- Name: customer_balance_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.customer_balance_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customer_balance_transactions_id_seq OWNER TO postgres;

--
-- Name: customer_balance_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.customer_balance_transactions_id_seq OWNED BY public.customer_balance_transactions.id;


--
-- Name: customer_balances; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_balances (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    balance_amount numeric(10,2) DEFAULT 0,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    notes text,
    is_active boolean DEFAULT true
);


ALTER TABLE public.customer_balances OWNER TO postgres;

--
-- Name: customer_balances_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.customer_balances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customer_balances_id_seq OWNER TO postgres;

--
-- Name: customer_balances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.customer_balances_id_seq OWNED BY public.customer_balances.id;


--
-- Name: customer_email_replies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_email_replies (
    id integer NOT NULL,
    customer_email_id integer,
    sender text NOT NULL,
    body text,
    created_at timestamp without time zone DEFAULT now(),
    is_draft boolean DEFAULT false,
    sent_at timestamp without time zone,
    sent_via character varying(50),
    confidence_score double precision,
    confidence_reasoning jsonb,
    auto_send_recommended boolean DEFAULT false,
    auto_sent boolean DEFAULT false,
    auto_sent_at timestamp without time zone
);


ALTER TABLE public.customer_email_replies OWNER TO postgres;

--
-- Name: customer_email_replies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.customer_email_replies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customer_email_replies_id_seq OWNER TO postgres;

--
-- Name: customer_email_replies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.customer_email_replies_id_seq OWNED BY public.customer_email_replies.id;


--
-- Name: customer_emails; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_emails (
    id integer NOT NULL,
    sender text NOT NULL,
    subject text,
    body text,
    attachments jsonb,
    bl_numbers text[],
    created_at timestamp without time zone DEFAULT now(),
    processed_at timestamp without time zone,
    classification character varying(50),
    openai_processed boolean DEFAULT false,
    processed_for_payments boolean DEFAULT false,
    message_id character varying(255),
    from_addr character varying(255),
    outlook_message_id character varying(255),
    processed_by_outlook boolean DEFAULT false,
    outlook_user_id character varying(255),
    status character varying(50) DEFAULT 'New'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cc text[],
    bcc text[],
    reply_to text[],
    "to" text[]
);


ALTER TABLE public.customer_emails OWNER TO postgres;

--
-- Name: COLUMN customer_emails.outlook_message_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.outlook_message_id IS 'Outlook message ID for tracking';


--
-- Name: COLUMN customer_emails.processed_by_outlook; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.processed_by_outlook IS 'Whether email was processed via Outlook add-in';


--
-- Name: COLUMN customer_emails.outlook_user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.outlook_user_id IS 'ID of Outlook user who processed the email';


--
-- Name: COLUMN customer_emails.cc; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.cc IS 'Array of CC email addresses from original email';


--
-- Name: COLUMN customer_emails.bcc; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.bcc IS 'Array of BCC email addresses from original email';


--
-- Name: COLUMN customer_emails.reply_to; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails.reply_to IS 'Array of Reply-To email addresses from original email';


--
-- Name: COLUMN customer_emails."to"; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customer_emails."to" IS 'Array of "To" email addresses from original email';


--
-- Name: customer_emails_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.customer_emails_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customer_emails_id_seq OWNER TO postgres;

--
-- Name: customer_emails_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.customer_emails_id_seq OWNED BY public.customer_emails.id;


--
-- Name: email_editing_locks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_editing_locks (
    id integer NOT NULL,
    email_id integer NOT NULL,
    user_id character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.email_editing_locks OWNER TO postgres;

--
-- Name: TABLE email_editing_locks; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.email_editing_locks IS 'Prevents multiple users from editing the same email simultaneously';


--
-- Name: email_editing_locks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_editing_locks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_editing_locks_id_seq OWNER TO postgres;

--
-- Name: email_editing_locks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_editing_locks_id_seq OWNED BY public.email_editing_locks.id;


--
-- Name: email_ingest_errors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_ingest_errors (
    id integer NOT NULL,
    filename text,
    reason text,
    raw_text text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.email_ingest_errors OWNER TO postgres;

--
-- Name: email_ingest_errors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_ingest_errors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_ingest_errors_id_seq OWNER TO postgres;

--
-- Name: email_ingest_errors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_ingest_errors_id_seq OWNED BY public.email_ingest_errors.id;


--
-- Name: email_processing_locks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_processing_locks (
    id integer NOT NULL,
    user_id character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.email_processing_locks OWNER TO postgres;

--
-- Name: TABLE email_processing_locks; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.email_processing_locks IS 'Prevents multiple users from processing emails simultaneously';


--
-- Name: email_processing_locks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_processing_locks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_processing_locks_id_seq OWNER TO postgres;

--
-- Name: email_processing_locks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_processing_locks_id_seq OWNED BY public.email_processing_locks.id;


--
-- Name: email_prompt_locks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_prompt_locks (
    sender_id character varying(64) NOT NULL,
    locked_until timestamp without time zone
);


ALTER TABLE public.email_prompt_locks OWNER TO postgres;

--
-- Name: email_status_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.email_status_view AS
 SELECT ce.id,
    ce.sender,
    ce.subject,
    ce.classification,
    ce.created_at,
    count(cer.id) AS reply_count,
    max(
        CASE
            WHEN (cer.is_draft = false) THEN cer.sent_at
            ELSE NULL::timestamp without time zone
        END) AS last_sent_at,
    max(cer.confidence_score) AS max_confidence,
    bool_or(cer.auto_sent) AS has_auto_sent,
    bool_or(cer.auto_send_recommended) AS has_auto_send_recommended
   FROM (public.customer_emails ce
     LEFT JOIN public.customer_email_replies cer ON ((ce.id = cer.customer_email_id)))
  GROUP BY ce.id, ce.sender, ce.subject, ce.classification, ce.created_at;


ALTER VIEW public.email_status_view OWNER TO postgres;

--
-- Name: fcm_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fcm_notifications (
    id integer NOT NULL,
    email_id integer NOT NULL,
    notification_type character varying(50) NOT NULL,
    sent_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.fcm_notifications OWNER TO postgres;

--
-- Name: TABLE fcm_notifications; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fcm_notifications IS 'Tracks FCM notifications sent to prevent duplicates';


--
-- Name: COLUMN fcm_notifications.email_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_notifications.email_id IS 'ID of the email that triggered the notification';


--
-- Name: COLUMN fcm_notifications.notification_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_notifications.notification_type IS 'Type of notification (new_email, payment_receipt, etc.)';


--
-- Name: COLUMN fcm_notifications.sent_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_notifications.sent_at IS 'When the notification was sent';


--
-- Name: fcm_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fcm_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fcm_notifications_id_seq OWNER TO postgres;

--
-- Name: fcm_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fcm_notifications_id_seq OWNED BY public.fcm_notifications.id;


--
-- Name: fcm_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fcm_tokens (
    id integer NOT NULL,
    user_id integer,
    token text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);


ALTER TABLE public.fcm_tokens OWNER TO postgres;

--
-- Name: TABLE fcm_tokens; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.fcm_tokens IS 'Stores FCM tokens for push notifications';


--
-- Name: COLUMN fcm_tokens.user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_tokens.user_id IS 'User ID for authenticated tokens, NULL for public tokens';


--
-- Name: COLUMN fcm_tokens.token; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_tokens.token IS 'Firebase Cloud Messaging token';


--
-- Name: COLUMN fcm_tokens.is_active; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fcm_tokens.is_active IS 'Whether the token is still valid';


--
-- Name: fcm_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fcm_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fcm_tokens_id_seq OWNER TO postgres;

--
-- Name: fcm_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fcm_tokens_id_seq OWNED BY public.fcm_tokens.id;


--
-- Name: outlook_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.outlook_sessions (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    session_token character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);


ALTER TABLE public.outlook_sessions OWNER TO postgres;

--
-- Name: TABLE outlook_sessions; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.outlook_sessions IS 'Tracks active Outlook user sessions';


--
-- Name: outlook_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.outlook_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.outlook_sessions_id_seq OWNER TO postgres;

--
-- Name: outlook_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.outlook_sessions_id_seq OWNED BY public.outlook_sessions.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer,
    token character varying(128) NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


ALTER TABLE public.password_reset_tokens OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: pricing_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pricing_config (
    id integer NOT NULL,
    shipment_type character varying(20) NOT NULL,
    container_type character varying(20),
    pricing_method character varying(20) NOT NULL,
    ctn_fee_per_unit numeric(10,2) NOT NULL,
    service_fee_per_unit numeric(10,2) NOT NULL,
    unit_type character varying(20) NOT NULL,
    minimum_charge numeric(10,2) DEFAULT 0,
    maximum_charge numeric(10,2),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100),
    notes text
);


ALTER TABLE public.pricing_config OWNER TO postgres;

--
-- Name: TABLE pricing_config; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.pricing_config IS 'Configuration table for different pricing methods and rates';


--
-- Name: pricing_config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pricing_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pricing_config_id_seq OWNER TO postgres;

--
-- Name: pricing_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pricing_config_id_seq OWNED BY public.pricing_config.id;


--
-- Name: pricing_overrides; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pricing_overrides (
    id integer NOT NULL,
    bill_of_lading_id integer,
    original_ctn_fee numeric(10,2),
    original_service_fee numeric(10,2),
    new_ctn_fee numeric(10,2),
    new_service_fee numeric(10,2),
    reason text NOT NULL,
    overridden_by character varying(100) NOT NULL,
    overridden_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    notes text
);


ALTER TABLE public.pricing_overrides OWNER TO postgres;

--
-- Name: pricing_overrides_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pricing_overrides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pricing_overrides_id_seq OWNER TO postgres;

--
-- Name: pricing_overrides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pricing_overrides_id_seq OWNED BY public.pricing_overrides.id;


--
-- Name: test123; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test123 (
    id integer NOT NULL
);


ALTER TABLE public.test123 OWNER TO postgres;

--
-- Name: test123_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test123_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test123_id_seq OWNER TO postgres;

--
-- Name: test123_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test123_id_seq OWNED BY public.test123.id;


--
-- Name: unmatched_receipts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unmatched_receipts (
    id integer NOT NULL,
    date date,
    description text,
    amount numeric(10,2),
    reason text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    raw_text text
);


ALTER TABLE public.unmatched_receipts OWNER TO postgres;

--
-- Name: TABLE unmatched_receipts; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.unmatched_receipts IS 'Stores details of payment receipts that could not be automatically matched to a Bill of Lading.';


--
-- Name: COLUMN unmatched_receipts.reason; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.unmatched_receipts.reason IS 'The reason why the receipt could not be matched, e.g., Invalid BL number, amount mismatch.';


--
-- Name: COLUMN unmatched_receipts.raw_text; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.unmatched_receipts.raw_text IS 'The full text of the email body for manual review.';


--
-- Name: unmatched_receipts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unmatched_receipts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unmatched_receipts_id_seq OWNER TO postgres;

--
-- Name: unmatched_receipts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unmatched_receipts_id_seq OWNED BY public.unmatched_receipts.id;


--
-- Name: user_activity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_activity (
    id integer NOT NULL,
    user_id character varying(100) NOT NULL,
    current_email_id integer,
    current_action character varying(50),
    last_activity timestamp without time zone DEFAULT now()
);


ALTER TABLE public.user_activity OWNER TO postgres;

--
-- Name: TABLE user_activity; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.user_activity IS 'Tracks user activity for real-time collaboration features';


--
-- Name: user_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_activity_id_seq OWNER TO postgres;

--
-- Name: user_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_activity_id_seq OWNED BY public.user_activity.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(512) NOT NULL,
    role character varying(10) NOT NULL,
    approved boolean DEFAULT false,
    customer_name text,
    customer_email text,
    customer_phone text,
    failed_attempts integer DEFAULT 0 NOT NULL,
    lockout_until timestamp with time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_drafts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_drafts ALTER COLUMN id SET DEFAULT nextval('public.ai_drafts_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: bank_unmatched_records id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_unmatched_records ALTER COLUMN id SET DEFAULT nextval('public.bank_unmatched_records_id_seq'::regclass);


--
-- Name: bill_of_lading id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_of_lading ALTER COLUMN id SET DEFAULT nextval('public.bill_of_lading_id_seq'::regclass);


--
-- Name: customer_balance_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balance_transactions ALTER COLUMN id SET DEFAULT nextval('public.customer_balance_transactions_id_seq'::regclass);


--
-- Name: customer_balances id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balances ALTER COLUMN id SET DEFAULT nextval('public.customer_balances_id_seq'::regclass);


--
-- Name: customer_email_replies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_email_replies ALTER COLUMN id SET DEFAULT nextval('public.customer_email_replies_id_seq'::regclass);


--
-- Name: customer_emails id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_emails ALTER COLUMN id SET DEFAULT nextval('public.customer_emails_id_seq'::regclass);


--
-- Name: email_editing_locks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_editing_locks ALTER COLUMN id SET DEFAULT nextval('public.email_editing_locks_id_seq'::regclass);


--
-- Name: email_ingest_errors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_ingest_errors ALTER COLUMN id SET DEFAULT nextval('public.email_ingest_errors_id_seq'::regclass);


--
-- Name: email_processing_locks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_processing_locks ALTER COLUMN id SET DEFAULT nextval('public.email_processing_locks_id_seq'::regclass);


--
-- Name: fcm_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_notifications ALTER COLUMN id SET DEFAULT nextval('public.fcm_notifications_id_seq'::regclass);


--
-- Name: fcm_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_tokens ALTER COLUMN id SET DEFAULT nextval('public.fcm_tokens_id_seq'::regclass);


--
-- Name: outlook_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlook_sessions ALTER COLUMN id SET DEFAULT nextval('public.outlook_sessions_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: pricing_config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_config ALTER COLUMN id SET DEFAULT nextval('public.pricing_config_id_seq'::regclass);


--
-- Name: pricing_overrides id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_overrides ALTER COLUMN id SET DEFAULT nextval('public.pricing_overrides_id_seq'::regclass);


--
-- Name: test123 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test123 ALTER COLUMN id SET DEFAULT nextval('public.test123_id_seq'::regclass);


--
-- Name: unmatched_receipts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unmatched_receipts ALTER COLUMN id SET DEFAULT nextval('public.unmatched_receipts_id_seq'::regclass);


--
-- Name: user_activity id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_activity ALTER COLUMN id SET DEFAULT nextval('public.user_activity_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ai_drafts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ai_drafts (id, email_id, draft_content, created_at, sent_at, sent_by, draft_type) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_logs (id, user_id, operation, details, "timestamp", ip_address) FROM stdin;
1	\N	table_creation	audit_logs table created for performance monitoring	2025-07-29 02:16:40.962018+00	system
2	84	login	User logged in successfully	2025-07-29 02:27:45.866388+00	\N
3	84	login	User logged in successfully	2025-07-29 02:38:50.487623+00	\N
4	84	login	User logged in successfully	2025-07-29 06:18:53.841755+00	\N
5	84	login	User logged in successfully	2025-07-29 07:00:46.647887+00	\N
6	84	login	User logged in successfully	2025-07-29 07:06:51.34113+00	\N
7	84	login	User logged in successfully	2025-07-29 07:10:52.843284+00	\N
8	84	login	User logged in successfully	2025-07-29 10:12:38.780595+00	\N
9	84	login	User logged in successfully	2025-07-29 10:14:47.49968+00	\N
10	84	login	User logged in successfully	2025-07-30 01:15:59.804864+00	\N
11	107	login	User logged in successfully	2025-07-30 02:13:59.553735+00	\N
12	107	login	User logged in successfully	2025-07-30 02:15:53.625027+00	\N
13	\N	login_failed	Username ray80 not found	2025-07-30 02:16:22.799418+00	\N
14	97	login	User logged in successfully	2025-07-30 02:16:45.438295+00	\N
15	97	login	User logged in successfully	2025-07-30 02:31:52.263048+00	\N
16	84	login	User logged in successfully	2025-07-30 03:45:37.218544+00	\N
17	84	login	User logged in successfully	2025-07-30 04:04:49.194554+00	\N
18	\N	register	New user registered: ray401	2025-07-30 04:33:35.349135+00	\N
19	84	login	User logged in successfully	2025-07-30 04:34:42.060794+00	\N
20	84	login	User logged in successfully	2025-07-30 05:45:43.898429+00	\N
21	84	login	User logged in successfully	2025-07-30 07:03:06.868215+00	\N
22	110	login	User logged in successfully	2025-07-30 07:05:52.811953+00	\N
23	84	login	User logged in successfully	2025-07-30 07:07:15.995033+00	\N
24	84	login	User logged in successfully	2025-07-30 07:54:45.418178+00	\N
25	84	login	User logged in successfully	2025-07-30 08:08:26.099626+00	\N
26	84	login	User logged in successfully	2025-07-30 08:09:36.960056+00	\N
27	84	login	User logged in successfully	2025-07-30 08:12:00.337368+00	\N
28	84	login	User logged in successfully	2025-07-30 08:14:52.100548+00	\N
29	84	login	User logged in successfully	2025-07-30 08:24:10.984913+00	\N
30	84	login	User logged in successfully	2025-07-30 08:45:30.120608+00	\N
31	84	login	User logged in successfully	2025-07-30 09:48:58.056132+00	\N
32	84	login	User logged in successfully	2025-07-30 10:32:18.522639+00	\N
33	84	login	User logged in successfully	2025-07-30 10:36:34.520261+00	\N
34	84	login	User logged in successfully	2025-07-31 04:00:31.947937+00	\N
35	84	login	User logged in successfully	2025-07-31 04:12:50.763164+00	\N
36	84	login	User logged in successfully	2025-07-31 05:27:23.358858+00	\N
37	84	login	User logged in successfully	2025-07-31 07:33:32.991395+00	\N
38	84	login	User logged in successfully	2025-07-31 11:55:07.173855+00	\N
39	84	login	User logged in successfully	2025-07-31 12:14:28.447585+00	\N
40	84	login	User logged in successfully	2025-07-31 12:20:35.322776+00	\N
41	84	login	User logged in successfully	2025-07-31 12:33:37.383521+00	\N
42	84	login	User logged in successfully	2025-07-31 12:36:35.745508+00	\N
43	84	login	User logged in successfully	2025-07-31 12:41:02.498155+00	\N
44	84	login	User logged in successfully	2025-07-31 12:49:06.85231+00	\N
45	84	login	User logged in successfully	2025-07-31 21:58:18.014146+00	\N
46	84	login	User logged in successfully	2025-08-01 00:13:04.429054+00	\N
47	84	login	User logged in successfully	2025-08-01 01:22:47.915645+00	\N
48	84	login	User logged in successfully	2025-08-01 01:38:18.462243+00	\N
49	84	login	User logged in successfully	2025-08-01 02:30:52.464617+00	\N
50	84	login	User logged in successfully	2025-08-01 02:53:05.463982+00	\N
51	84	login	User logged in successfully	2025-08-01 03:39:20.064954+00	\N
52	84	login	User logged in successfully	2025-08-01 06:06:27.526488+00	\N
53	84	login	User logged in successfully	2025-08-01 07:02:40.891206+00	\N
54	84	login	User logged in successfully	2025-08-01 07:27:13.065536+00	\N
55	84	login	User logged in successfully	2025-08-01 08:57:44.206459+00	\N
56	84	login	User logged in successfully	2025-08-01 09:58:50.225602+00	\N
57	84	login	User logged in successfully	2025-08-01 10:31:30.112335+00	\N
58	84	login	User logged in successfully	2025-08-01 11:29:29.846934+00	\N
59	84	login	User logged in successfully	2025-08-01 11:32:49.017277+00	\N
60	84	login	User logged in successfully	2025-08-01 11:33:52.092996+00	\N
61	84	login	User logged in successfully	2025-08-01 11:39:16.236063+00	\N
62	84	login	User logged in successfully	2025-08-02 01:20:54.960472+00	\N
63	84	login	User logged in successfully	2025-08-02 06:51:18.456375+00	\N
64	84	login	User logged in successfully	2025-08-02 06:51:49.897134+00	\N
65	84	login	User logged in successfully	2025-08-02 06:59:39.177014+00	\N
66	84	login	User logged in successfully	2025-08-02 07:47:54.690162+00	\N
67	84	login	User logged in successfully	2025-08-02 08:01:23.507313+00	\N
68	84	login	User logged in successfully	2025-08-02 08:01:57.506633+00	\N
69	84	login	User logged in successfully	2025-08-02 08:02:04.697617+00	\N
70	84	login	User logged in successfully	2025-08-02 08:02:42.802969+00	\N
71	84	login	User logged in successfully	2025-08-02 08:02:54.835619+00	\N
72	107	login	User logged in successfully	2025-08-02 08:03:04.107228+00	\N
73	84	login	User logged in successfully	2025-08-02 08:26:37.253137+00	\N
74	84	login	User logged in successfully	2025-08-02 08:26:52.551201+00	\N
75	84	login	User logged in successfully	2025-08-02 08:32:41.292707+00	\N
76	84	login	User logged in successfully	2025-08-02 08:40:54.040438+00	\N
77	84	login	User logged in successfully	2025-08-02 08:48:31.482523+00	\N
78	84	login	User logged in successfully	2025-08-02 08:56:44.786468+00	\N
79	84	login	User logged in successfully	2025-08-02 09:02:30.962612+00	\N
80	84	login	User logged in successfully	2025-08-02 09:14:42.389042+00	\N
81	84	login	User logged in successfully	2025-08-02 09:37:24.660192+00	\N
82	84	login	User logged in successfully	2025-08-02 09:45:00.456738+00	\N
83	84	login	User logged in successfully	2025-08-02 09:45:16.250778+00	\N
84	84	login	User logged in successfully	2025-08-02 09:45:24.873577+00	\N
85	84	login	User logged in successfully	2025-08-02 09:51:03.404011+00	\N
86	84	login	User logged in successfully	2025-08-02 10:09:23.453952+00	\N
87	84	login	User logged in successfully	2025-08-02 10:18:33.465757+00	\N
88	84	login	User logged in successfully	2025-08-02 10:39:33.921169+00	\N
89	84	login	User logged in successfully	2025-08-02 10:42:56.454321+00	\N
90	84	login	User logged in successfully	2025-08-02 11:22:32.471026+00	\N
91	84	login	User logged in successfully	2025-08-02 11:30:43.06049+00	\N
92	84	login	User logged in successfully	2025-08-02 11:50:09.729457+00	\N
93	84	login	User logged in successfully	2025-08-02 12:06:49.934438+00	\N
94	84	login	User logged in successfully	2025-08-02 12:24:31.620645+00	\N
95	84	login	User logged in successfully	2025-08-02 12:30:24.95128+00	\N
96	84	login	User logged in successfully	2025-08-02 12:44:40.519098+00	\N
97	84	login	User logged in successfully	2025-08-02 12:55:13.942262+00	\N
98	84	login	User logged in successfully	2025-08-02 12:58:32.632347+00	\N
99	84	login	User logged in successfully	2025-08-02 13:07:48.628079+00	\N
100	107	login	User logged in successfully	2025-08-02 13:11:03.081968+00	\N
101	107	login	User logged in successfully	2025-08-02 13:12:57.507252+00	\N
102	107	login	User logged in successfully	2025-08-02 13:13:58.481708+00	\N
103	107	login	User logged in successfully	2025-08-02 14:04:31.290329+00	\N
104	107	login	User logged in successfully	2025-08-02 14:04:58.108015+00	\N
105	84	login	User logged in successfully	2025-08-02 14:06:15.39398+00	\N
106	84	login	User logged in successfully	2025-08-03 01:52:04.624279+00	\N
107	107	login	User logged in successfully	2025-08-03 01:55:43.629667+00	\N
108	84	login	User logged in successfully	2025-08-03 02:15:14.080021+00	\N
109	84	login	User logged in successfully	2025-08-03 02:16:23.781671+00	\N
110	84	login	User logged in successfully	2025-08-03 02:28:40.192901+00	\N
111	84	login	User logged in successfully	2025-08-03 02:38:41.714786+00	\N
112	107	login	User logged in successfully	2025-08-03 02:39:37.661858+00	\N
113	107	login	User logged in successfully	2025-08-03 02:41:34.708946+00	\N
114	107	login	User logged in successfully	2025-08-03 02:42:38.017231+00	\N
115	107	login	User logged in successfully	2025-08-03 03:01:24.760219+00	\N
116	84	login	User logged in successfully	2025-08-03 03:03:24.560274+00	\N
117	107	login	User logged in successfully	2025-08-03 03:04:25.467913+00	\N
118	107	login	User logged in successfully	2025-08-03 03:07:08.86881+00	\N
119	107	login	User logged in successfully	2025-08-03 03:07:50.663156+00	\N
120	107	login	User logged in successfully	2025-08-03 03:23:18.069474+00	\N
121	107	login	User logged in successfully	2025-08-03 03:23:44.809962+00	\N
122	107	login	User logged in successfully	2025-08-03 03:24:17.692503+00	\N
123	107	login	User logged in successfully	2025-08-03 06:03:31.373024+00	\N
124	107	login	User logged in successfully	2025-08-03 06:37:30.247404+00	\N
125	84	login	User logged in successfully	2025-08-03 06:56:41.334326+00	\N
126	107	login	User logged in successfully	2025-08-03 07:02:54.622714+00	\N
127	107	login	User logged in successfully	2025-08-03 07:04:53.238424+00	\N
128	84	login	User logged in successfully	2025-08-03 10:00:37.623453+00	\N
129	84	login	User logged in successfully	2025-08-03 12:43:33.18303+00	\N
130	84	login	User logged in successfully	2025-08-03 13:31:45.538025+00	\N
131	84	login	User logged in successfully	2025-08-03 13:32:51.243806+00	\N
132	84	login	User logged in successfully	2025-08-03 13:50:11.44293+00	\N
133	107	login	User logged in successfully	2025-08-03 13:50:51.239434+00	\N
134	84	login	User logged in successfully	2025-08-04 07:49:42.524834+00	\N
135	84	login	User logged in successfully	2025-08-04 09:14:40.308248+00	\N
136	84	login	User logged in successfully	2025-08-04 09:17:12.490519+00	\N
137	84	login	User logged in successfully	2025-08-04 09:17:52.603266+00	\N
138	84	login	User logged in successfully	2025-08-04 09:20:42.837825+00	\N
139	84	login	User logged in successfully	2025-08-04 09:45:46.689789+00	\N
140	84	login	User logged in successfully	2025-08-04 10:54:20.356807+00	\N
141	84	login	User logged in successfully	2025-08-04 10:55:42.6973+00	\N
142	84	login	User logged in successfully	2025-08-04 10:57:26.007064+00	\N
143	84	login	User logged in successfully	2025-08-04 11:12:18.120946+00	\N
144	84	login	User logged in successfully	2025-08-04 11:18:05.993848+00	\N
145	84	login	User logged in successfully	2025-08-04 12:40:30.201142+00	\N
146	84	login	User logged in successfully	2025-08-04 22:36:18.167418+00	\N
147	84	login	User logged in successfully	2025-08-05 06:12:47.100632+00	\N
148	84	login	User logged in successfully	2025-08-05 06:46:26.728861+00	\N
149	84	login	User logged in successfully	2025-08-05 07:22:44.28274+00	\N
150	84	login	User logged in successfully	2025-08-05 08:05:08.256387+00	\N
151	84	login	User logged in successfully	2025-08-05 08:06:01.652516+00	\N
152	84	login	User logged in successfully	2025-08-05 08:17:35.684234+00	\N
153	84	login	User logged in successfully	2025-08-05 10:09:31.788814+00	\N
154	84	login	User logged in successfully	2025-08-05 10:32:10.35252+00	\N
155	84	login	User logged in successfully	2025-08-05 11:27:42.045807+00	\N
156	84	login	User logged in successfully	2025-08-06 02:02:18.613053+00	\N
157	84	login	User logged in successfully	2025-08-06 02:30:44.279557+00	\N
158	84	login	User logged in successfully	2025-08-06 03:21:18.5716+00	\N
159	84	login	User logged in successfully	2025-08-06 03:46:49.766105+00	\N
160	84	login	User logged in successfully	2025-08-06 04:06:43.983618+00	\N
161	84	login	User logged in successfully	2025-08-06 04:16:14.713463+00	\N
162	84	login	User logged in successfully	2025-08-06 06:08:42.807768+00	\N
163	84	login	User logged in successfully	2025-08-06 07:04:47.588815+00	\N
164	84	login	User logged in successfully	2025-08-06 08:23:41.371292+00	\N
165	84	login	User logged in successfully	2025-08-06 09:24:28.837909+00	\N
166	84	login	User logged in successfully	2025-08-06 10:17:17.413438+00	\N
167	84	login	User logged in successfully	2025-08-06 10:58:53.582986+00	\N
168	107	login	User logged in successfully	2025-08-07 01:53:51.149805+00	\N
169	\N	login_failed	Username Ray40 not found	2025-08-07 01:56:00.694567+00	\N
170	84	login	User logged in successfully	2025-08-07 01:56:39.038535+00	\N
171	107	login	User logged in successfully	2025-08-07 01:56:53.176808+00	\N
172	84	login	User logged in successfully	2025-08-08 00:26:00.623193+00	\N
173	84	login	User logged in successfully	2025-08-09 05:38:23.865511+00	\N
174	84	login	User logged in successfully	2025-08-09 07:55:21.758033+00	\N
175	84	login	User logged in successfully	2025-08-09 08:10:16.557458+00	\N
\.


--
-- Data for Name: bank_unmatched_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bank_unmatched_records (id, bl_number, amount, date, description, created_at, reason) FROM stdin;
2	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-14 11:16:50.173951	No unpaid record for BL NYC22062891
3	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-14 11:16:50.341134	No unpaid record for BL BL123456
5	\N	300.0	2025-07-02	cash depoist	2025-07-14 11:18:54.362713	No BL number detected
6	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-14 11:18:54.362713	No unpaid record for BL NYC22062891
7	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-14 11:18:54.536121	No unpaid record for BL BL123456
9	\N	300.0	2025-07-02	cash depoist	2025-07-14 11:25:38.605495	No BL number detected
10	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-14 11:25:38.605495	No unpaid record for BL NYC22062891
11	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-14 11:25:38.765949	No unpaid record for BL BL123456
13	\N	300.0	2025-07-02	cash depoist	2025-07-15 03:52:29.619676	No BL number detected
14	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 03:52:29.619676	No unpaid record for BL NYC22062891
15	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 03:52:29.777625	No unpaid record for BL BL123456
17	\N	300.0	2025-07-02	cash depoist	2025-07-15 04:08:53.375581	No BL number detected
18	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 04:08:53.375581	No unpaid record for BL NYC22062891
19	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 04:08:53.537773	No unpaid record for BL BL123456
21	\N	300.0	2025-07-02	cash depoist	2025-07-15 07:54:00.275258	No BL number detected
22	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 07:54:00.275258	No unpaid record for BL NYC22062891
23	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 07:54:00.45437	No unpaid record for BL BL123456
25	\N	300.0	2025-07-02	cash depoist	2025-07-15 10:57:13.563068	No BL number detected
26	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 10:57:13.563068	No unpaid record for BL NYC22062891
27	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 10:57:13.738838	No unpaid record for BL BL123456
29	\N	300.0	2025-07-02	cash depoist	2025-07-15 11:46:48.861623	No BL number detected
30	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 11:46:48.861623	No unpaid record for BL NYC22062891
31	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 11:46:49.019056	No unpaid record for BL BL123456
33	\N	300.0	2025-07-02	cash depoist	2025-07-15 12:04:29.644792	No BL number detected
34	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-15 12:04:29.644792	No unpaid record for BL NYC22062891
35	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-15 12:04:29.799453	No unpaid record for BL BL123456
37	\N	300.0	2025-07-02	cash depoist	2025-07-16 08:45:57.4145	No BL number detected
38	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-16 08:45:57.4145	No unpaid record for BL NYC22062891
39	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-16 08:45:57.571109	No unpaid record for BL BL123456
41	\N	300.0	2025-07-02	cash depoist	2025-07-16 09:30:28.596713	No BL number detected
42	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-16 09:30:28.596713	No unpaid record for BL NYC22062891
43	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-16 09:30:28.751572	No unpaid record for BL BL123456
44	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-16 09:30:28.878551	No BL number detected
45	\N	300.0	2025-07-02	cash depoist	2025-07-16 09:31:55.73801	No BL number detected
46	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-16 09:31:55.73801	No unpaid record for BL NYC22062891
47	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-16 09:31:55.90191	No unpaid record for BL BL123456
48	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-16 09:31:56.057531	No BL number detected
49	\N	300.0	2025-07-02	cash depoist	2025-07-16 10:44:42.768148	No BL number detected
50	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-16 10:44:42.768148	No unpaid record for BL NYC22062891
51	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-16 10:44:42.927294	No unpaid record for BL BL123456
52	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-16 10:44:43.056369	No BL number detected
53	\N	300.0	2025-07-02	cash depoist	2025-07-17 11:00:06.602956	No BL number detected
54	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-17 11:00:06.602956	No unpaid record for BL NYC22062891
55	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-17 11:00:06.75684	No unpaid record for BL BL123456
56	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-17 11:00:06.881363	No BL number detected
57	\N	300.0	2025-07-02	cash depoist	2025-07-17 11:08:34.084478	No BL number detected
58	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-17 11:08:34.084478	No unpaid record for BL NYC22062891
59	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-17 11:08:34.251791	No unpaid record for BL BL123456
61	\N	300.0	2025-07-02	cash depoist	2025-07-17 11:16:20.745861	No BL number detected
62	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-17 11:16:20.745861	No unpaid record for BL NYC22062891
63	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-17 11:16:20.904306	No unpaid record for BL BL123456
65	\N	300.0	2025-07-02	cash depoist	2025-07-17 11:26:44.940306	No BL number detected
66	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-17 11:26:44.940306	No unpaid record for BL NYC22062891
67	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-17 11:26:45.109221	No unpaid record for BL BL123456
68	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-17 11:26:45.244087	No BL number detected
77	\N	300.0	2025-07-02	cash depoist	2025-07-17 13:32:40.981351	No BL number detected
78	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-17 13:32:40.981351	No unpaid record for BL NYC22062891
79	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-17 13:32:41.145381	No unpaid record for BL BL123456
85	\N	300.0	2025-07-02	cash depoist	2025-07-20 10:41:35.078288	No BL number detected
86	\N	200.0	2025-07-03	Payment for B/L NYC22062891	2025-07-20 10:41:35.078288	No unpaid record for BL NYC22062891
87	\N	200.0	2025-07-04	Payment for B/L BL123456	2025-07-20 10:41:36.638318	No unpaid record for BL BL123456
88	\N	250.0	2025-07-05	Unknown Transfer REF 9999	2025-07-20 10:41:38.078311	No BL number detected
\.


--
-- Data for Name: bill_of_lading; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bill_of_lading (id, customer_name, customer_email, customer_phone, pdf_filename, ocr_text, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, service_fee, receipt_filename, status, created_at, updated_at, invoice_filename, unique_number, customer_username, ctn_fee, payment_link, receipt_uploaded_at, completed_at, customer_invoice, customer_packing_list, flight_or_vessel, product_description, payment_method, payment_status, reserve_amount, reserve_status, allinpay_85_received_at, payment_reference, shipment_type, container_type, container_count, total_weight_kg, weight_unit, pricing_method, base_ctn_fee, base_service_fee, calculated_ctn_fee, calculated_service_fee, ocr_confidence_score, manual_override, override_reason, override_by, override_at, pricing_calculation_log, last_pricing_update, notify_party, container_count_20ft, container_count_40ft, container_count_40ft_hc, payment_processed_by, payment_processed_at, payment_source, balance_applied) FROM stdin;
28	Ray	ykrw12@gmail.com	4567890	https://res.cloudinary.com/dtm46mski/raw/upload/v1753842932/bill/zp6vnh0ek9btjo7n0drp.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC2212345	OOCU7645765, TGBU8072666	\N	\N	Pending	2025-07-30 02:35:39.15587+00	2025-07-30 02:35:41.386786+00	\N	\N	ray81	\N	\N	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-30 02:35:41.386786+00		0	1	1	\N	\N	\N	0.00
39	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753964459/bill/zebx8fymvtk5uxschtz6.pdf	{"document_type": "BOL", "bl_number": "NYC2201666", "shipper": "SOLEX LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHENZHEN", "port_of_discharge": "NEW YORK, NY", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSOLEX LTD\\nNYC2201666\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nZHONGSHAN\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHENZHEN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nFRANCE\\nNEW YORK, NY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	SOLEX LTD	HAYWARD INDUSTRIES, INC.	SHENZHEN	NEW YORK, NY	NYC2201666	SLVU4877415, VOLU4543799	225.0	\N	Pending	2025-07-31 12:21:07.15426+00	2025-07-31 12:21:08.446828+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753964473/invoices/vkohaetyr60espkcxdmz.pdf	LZW027325	ray40	450.0	https://pay.example.com/39?ctn=450.0&svc=225.0&uniquenum=LZW027325	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-31 12:21:08.446828+00		0	1	1	\N	\N	\N	0.00
49	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754135430/bill/kqs8lvotegurbpbdip6e.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, G1-013025A-3T Rev K, qty:2436each, CONTR # OOCU7645789, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, 2436 CTNS in 42 x PLTS, G1-013032A-3T Rev D, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN		NYC2206288	OOCU7645789, TGBU8072614	\N	\N	Pending	2025-08-02 11:50:40.629866+00	2025-08-02 11:50:40.94139+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, G1-013025A-3T Rev K, qty:2436each, CONTR # OOCU7645789, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, 2436 CTNS in 42 x PLTS, G1-013032A-3T Rev D, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 11:50:40.94139+00		0	1	1	\N	\N	\N	0.00
64	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754190280/bill/xcyab0jrhcrk8kdli9ql.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC235	OOCU7645765, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754453713/receipts/cbqajud1pkj8efjsmvmh.pdf	Awaiting Bank In	2025-08-03 03:04:45.406046+00	2025-08-03 03:04:45.667843+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754453498/invoices/skw7fnldr7kivb17rmnw.pdf	LVS753972	ray40	450	https://pay.example.com/64?ctn=450.0&svc=225.0&uniquenum=LVS753972	2025-08-06 04:15:13.355364+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 03:04:45.667843+00		0	1	1	\N	\N	\N	0.00
54	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754139374/bill/vtyvr3j6ai051eu9cwkq.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "CONTR # OOCU7645789, PO#38920A, SEAL  # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL  # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN	largos	NYC245	OOCU7645789, TGBU8072614	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464996/receipts/xqxhfapjvxglgjf03xwf.pdf	Awaiting Bank In	2025-08-02 12:56:17.929237+00	2025-08-02 12:56:18.170429+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464665/invoices/uoo37gvd0fubjuq4hofk.pdf		ray40	450		2025-08-06 15:23:16.792078+00	\N	\N	\N	OOCL BERLIN v.041E	CONTR # OOCU7645789, PO#38920A, SEAL  # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL  # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 12:56:18.170429+00		0	1	1	\N	\N	\N	0.00
29	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753847177/bill/hpfohl1jia1dtfmg4z2e.pdf	{"document_type": "BOL", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 03:46:25.891532+00	2025-07-30 03:46:27.223599+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 03:46:27.223599+00		0	0	0	\N	\N	\N	0.00
40	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753965237/bill/pu5siccovwqqejcgkux1.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI		NYC2201777	SLVU4877415, VOLU4543799, BBBB4543799	\N	\N	Pending	2025-07-31 12:34:04.922668+00	2025-07-31 12:34:06.400203+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	3	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-07-31 12:34:06.400203+00		0	1	1	\N	\N	\N	0.00
50	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754136422/bill/gmkbvgyguybk0u7tshes.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI		NYC2201777	SLVU4877415, VOLU4543799, BBBB4543799	\N	\N	Pending	2025-08-02 12:07:10.309626+00	2025-08-02 12:07:10.585404+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	3	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 12:07:10.585404+00		0	1	1	\N	\N	\N	0.00
74	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754347018/bill/phdfb14flz9l91hzuux5.PDF	{"document_type": "SEA WAYBILL", "bl_number": "254148256214", "shipper": "WANG TAI CO.", "consignee": "BORMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "HONGKONG", "port_of_discharge": "HAMBURG", "container_numbers": "KEIS2374724/20", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "BAG FOR CHARGING CABLE 1800PCS", "paid_amount": "", "raw_text": "[OpenAI Vision fallback used]", "container_count": 1, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.69, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.7, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.69}, "extraction_method": "vision_api"}	WANG TAI CO.	BORMANN LOGISTICS GMBH & CO. OHG	HONGKONG	HAMBURG	NYC225	KEIS2374724/20	100	\N	Invoice Sent	2025-08-04 22:37:09.984544+00	2025-08-04 22:37:10.236987+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754390000/invoices/pi2esxbkb7t3v4swpt47.pdf	UTY010214	ray40	100	https://pay.example.com/74?ctn=100.0&svc=100.0&uniquenum=UTY010214	\N	\N	\N	\N	MEGA WAVE RIDER	BAG FOR CHARGING CABLE 1800PCS			0		\N	\N	ocean	\N	1	\N	kg	default	\N	\N	100.00	100.00	0.69	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-08-04 22:37:10.236987+00		0	0	0	email_ingestor	2025-08-05 11:37:23.078822+00	email	0.00
30	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753848321/bill/g8lskkxz6fpftnpejy44.pdf	{"document_type": "BILL OF LADING FOR OCEAN TRANSPORT OR MULTIMODAL TRANSPORT", "bl_number": "602436760", "shipper": "GUARDIAN INDUSTRIES CORP LTD.", "consignee": "WESSEX PICTURES", "port_of_loading": "Laem Chabang, Thailand", "port_of_discharge": "Felixstowe", "container_numbers": "", "flight_or_vessel": "SCT VIETNAM v.1292", "product_description": "FLOAT CLEAR 2.00 MM 915 X 1220 MM", "paid_amount": "", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	GUARDIAN INDUSTRIES CORP LTD.	WESSEX PICTURES	Laem Chabang, Thailand	Felixstowe	602436760		\N	\N	Pending	2025-07-30 04:05:30.857858+00	2025-07-30 04:05:32.713501+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	SCT VIETNAM v.1292	FLOAT CLEAR 2.00 MM 915 X 1220 MM	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 04:05:32.713501+00		0	0	0	\N	\N	\N	0.00
41	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753965412/bill/gqdq8wsmvas7htidjzei.pdf	{"document_type": "BOL", "bl_number": "NYC2201666", "shipper": "SOLEX LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHENZHEN", "port_of_discharge": "NEW YORK, NY", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSOLEX LTD\\nNYC2201666\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nZHONGSHAN\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHENZHEN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nFRANCE\\nNEW YORK, NY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	SOLEX LTD	HAYWARD INDUSTRIES, INC.	SHENZHEN	NEW YORK, NY	NYC223	SLVU4877415, VOLU4543799	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754030752/receipts/ycjzayxfx4yq9oeqxoee.pdf	Awaiting Bank In	2025-07-31 12:36:58.989477+00	2025-07-31 12:37:00.367951+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754028781/invoices/gc5goi1st2gu9wyna4wi.pdf	VVG116890	ray40	450	https://pay.example.com/41?ctn=450.0&svc=225.0&uniquenum=VVG116890	2025-08-01 06:45:53.861161+00	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-31 12:37:00.367951+00		0	1	1	\N	\N	\N	0.00
42	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753965683/bill/pl9xxtucfmwzsogz7lyv.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC221	OOCU7645765, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754224904/receipts/nwvhoxzkzdkov9ngacew.pdf	Awaiting Bank In	2025-07-31 12:41:30.012699+00	2025-07-31 12:41:32.639831+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754028750/invoices/ljsjlp4jed7zq04oal7b.pdf	GRY272129	ray40	450	https://pay.example.com/42?ctn=450.0&svc=225.0&uniquenum=GRY272129	2025-08-03 20:41:45.128447+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-31 12:41:32.639831+00		0	1	1	\N	\N	\N	0.00
51	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754137484/bill/cwawgsslmwfwwhtllxun.pdf	{"document_type": "BOL", "bl_number": "NYC2207777", "shipper": "RAY TOP", "consignee": "SMART FAMOUS", "port_of_loading": "HONG KONG", "port_of_discharge": "", "container_numbers": "OOCU7645898, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY TOP\\nNYC2207777\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nHONG KONG\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nNIGERIA\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645898\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	RAY TOP	SMART FAMOUS	HONG KONG	hong	NYC248	OOCU7645898, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754465145/receipts/yojl13ei5etzkitod8yj.pdf	Awaiting Bank In	2025-08-02 12:24:51.076888+00	2025-08-02 12:24:51.350784+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754465097/invoices/dzrepgb2vg5teo6bk7vl.pdf		ray40	450		2025-08-06 15:25:45.928603+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 12:24:51.350784+00		0	1	1	\N	\N	\N	0.00
70	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754204708/bill/tbdcdopt38cp9vkg7mn0.PDF	{"document_type": "BOL", "shipper": "A Joint Service Agreement", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "", "port_of_discharge": "HAMBURG", "bl_number": "254148256214", "container_numbers": "KEIS2374724", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "KEIS2374724/20' /EGDGS5468/54 PACKAGES", "raw_text": "BLUELINERS CORP.\\n(2) Shipper/Exporter\\nA Joint Service Agreement\\nWANG TAI CO. LTD\\nV, Enterprise Square\\n38 Wang Chiu Rd\\nKowloon Bay, Hongkong\\nSEA WAYBILL\\nNON-NEGOTIABLE\\n(5) Document No.\\n(6) Export References\\n(3) Consignee(complete name and address)\\nBOHRMANN LOGISTICS GMBH & CO. OHG\\nPARKSTRASSE 1\\n38440 WOLFSBURG GERMANY\\n(7) Forwarding Agent-References\\n(4) Notify Party (complete name and address)\\nWHEELS AG BIELEFELD\\nHERFORDER STRASSE 306\\n33609 BIELEFELD GERMANY\\n(8) Point and Country of Origin (for the Merchant's reference only)\\n(9) Also Notify Party (complete name and address)\\nNOTIABLE\\nHONGKONG\\n(17) Place of Delivery\\nHAMBURG\\n(12) Pre-carriage by\\n(14) Ocean Vessel/Voy. No.\\nMEGA WAVE RIDER\\n245W\\n(16) Port of Discharge\\nHAMBURG\\nThis Sea Waybill is issued at the request and for the convenience of the Merchant, but is nevertheless\\nsubject to the terms and conditions of the Carrier's standard long form Bill of Lading for this trade\\nwhich may be viewed online at [http://www.evergreen-line.com] or a copy obtained from the Carrier\\nor its agents.\\n(10) Onward Inland Routing/Export Instructions (which are contracted separately by\\nMerchants entirely for their own account and risk)\\n(18) Container No. And Seal No.\\nMarks & Nos.\\nCONTAINER NO./SEAL NO.\\n(19) Quantity And\\nKind of Packages\\nParticulars furnished by the Merchant\\n(20) Description of Goods\\nKEIS2374724/20' /EGDGS5468/54 PACKAGES\\nINV NO. 10550578\\nDN NO. 10550578\\nWHEELS 12E (G15F)\\nHAMBURG\\nNO. 1-2\\nWHEELS 5WOG (G15F)\\nHAMBURG\\nNO. 1-2\\nINV NO. 10550578\\nDN NO.\\n10550578\\n(22) TOTAL NUMBER OF\\nCONTAINERS OR PACKAGES\\n(IN WORDS)\\n1 x 20'\\n4 PACKAGE(S)\\nOTIABLE\\nDUNS NUMBER: 455889824\\nPART NAME+QUANTITY\\nBAG FOR CHARGING CABLE\\n1800PCS\\nPART NUMBER 15E 554 812\\nHS CODE 42029200.00\\nPART NAME+QUANTITY\\nWARNING VEST 1200PCS\\nPART NUMBER 7K3 512 568\\n*THE BALANCE OF BILL OF LADING SEE ATTACHED LIST *\\nTOTAL NUMBER OF ATTACHED 1 PAGE\\n\\"OCEAN FREIGHT COLLECT\\"\\nSHIPPER'S LOAD & COUNT\\n25 PACKAGES\\nONE (1) CONTAINER ONLY\\n(24) FREIGHT & CHARGES\\nRevenue Tons\\n(21) Measurement (M\\u00b3)\\nGross Weight (KGS)\\n20.4700 CBM\\n4,616.100 KGS\\nRate\\nPer Prepaid\\nAS\\nARRANGED\\n(23)\\nDeclared Value S\\nMerchant enters actual value of Goods\\nand pays, the applicable ad valorem\\nTariff rate, Carrier's package limitation.\\nshall not apply.\\nCollect\\nNON-NEG ABLE\\n(25) Waybill No.\\n254148256214\\n(26) Service Type/Mode\\nFCL/FCL 0/0\\n(27) Number of Original Waybills\\nNIL (0)\\n(28) Place and Date of Issue\\nKOWLOON BAY, HONGKONG AUG. 22, 2024\\n(33) Laden on Board\\nAUG. 22,2024\\nMEGA WAVE RIDER\\n245W\\nKOWLOON BAY, HONGKONG\\n(29) Prepaid at\\n(31) Exchange Rate\\n(30) Collect at\\nDESTINATION\\n(32) Exchange Rate\\nAs agent for the Carrier and Vessel Provider Blueline Corp.\\ndoing business as \\"Blueline\\"\\nFORM NO. DOC-1-006-02\\n"}	A Joint Service Agreement	BOHRMANN LOGISTICS GMBH & CO. OHG	hong kong	HAMBURG	NYC229	KEIS2374724	200	\N	Invoice Sent	2025-08-03 07:05:10.659334+00	2025-08-03 07:05:10.89329+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754449212/invoices/hfohzzkq04lq86ix7o1b.pdf	ray272727	ray100	150	https://pay.dummy.com/link/70?amount=350.00&currency=USD&email=ray633008%40gmail.com&ctn=None&description=Reserve+payment+for+CTN+ray272727&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250806110010	\N	\N	\N	\N	MEGA WAVE RIDER	KEIS2374724/20' /EGDGS5468/54 PACKAGES			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-03 07:05:10.89329+00		0	0	0	email_ingestor	2025-08-06 03:03:30.653143+00	email	0.00
31	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753848336/bill/pgrhmgjpyu1uuze145sv.pdf	{"document_type": "Air Waybill", "bl_number": "001-12345678", "shipper": "CABLE AND STEEL COMPANY", "consignee": "CABLE BIG STORE", "port_of_loading": "NEW YORK", "port_of_discharge": "HEATHROW", "container_numbers": "", "flight_or_vessel": "AA1234/12", "product_description": "SOME ITEMS", "paid_amount": "1234.00", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	CABLE AND STEEL COMPANY	CABLE BIG STORE	NEW YORK	HEATHROW	001-12345678		\N	\N	Pending	2025-07-30 04:05:42.804103+00	2025-07-30 04:05:45.415886+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	AA1234/12	SOME ITEMS	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 04:05:45.415886+00		0	0	0	\N	\N	\N	0.00
73	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754300887/bill/lnmyaxvfivxjln55ltwl.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI	HUNGARY	NYC226	SLVU4877415, VOLU4543799, BBBB4543799	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754393994/receipts/xrteouwgwatgrx4vxi31.pdf	Paid and CTN Valid	2025-08-04 09:48:16.174417+00	2025-08-04 09:48:16.423815+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf	Ray010101	ray40	450	https://pay.dummy.com/link/73?amount=665.00&currency=USD&email=ykrw11%40myyahoo.com&ctn=None&description=Reserve+payment+for+CTN+Ray010101+%28Balance+applied%3A+%2410.00%29&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250805192925	2025-08-05 11:39:54.454295+00	2025-08-06 09:37:07.440553+00	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	3	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-08-04 09:48:16.423815+00		0	1	1	email_ingestor	2025-08-05 11:39:55.942358+00	email	10.00
13	VIP Logistics	vip@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024013	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.914681+00	2025-07-29 02:57:56.914681+00	\N	\N	\N	100.00	\N	\N	2025-08-03 01:59:32.651351+00	\N	\N	\N	\N	Allinpay	Paid 100%	30.0000	Reserve Settled	2025-07-19 14:00:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.914681+00	\N	0	0	0	\N	\N	\N	0.00
18	Processing Inc	processing@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024018	\N	100.00	\N	Invoice Sent	2025-07-29 02:57:57.261642+00	2025-07-29 02:57:57.261642+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:57.261642+00	\N	0	0	0	\N	\N	\N	0.00
14	Royal Freight	royal@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024014	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.914681+00	2025-07-29 02:57:56.914681+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	Paid 85%	30.0000	Unsettled	2025-07-21 09:30:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.914681+00	\N	0	0	0	\N	\N	\N	0.00
9	Speed Freight	speed@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024009	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.574746+00	2025-07-29 02:57:56.574746+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	Paid 85%	30.0000	Unsettled	2025-07-22 10:00:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.574746+00	\N	0	0	0	\N	\N	\N	0.00
53	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754138699/bill/uspjnhr34f5qoj6n3gud.pdf	{"document_type": "BOL", "bl_number": "NYC2201003", "shipper": "STAR RAPID LIMITED", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "NEW YORK, NY", "port_of_discharge": "NANSHA, CHINA", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "BILL OF LADING\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSTAR RAPID LIMITED\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nHAYWARD INDUSTRIES, INC. \\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nNEW YORK, NY\\nNEW YORK, NY\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B deta      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                  (18)\\n(19)\\n(20)\\n(21)\\n(22)\\n2x40'HQ SHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED ON BOARD :\\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN.,2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID COLLECT\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the abov\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limit\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\nFreight Brokers Global Services, Inc.\\nTIMON v.2201E\\nNANSHA, CHINA\\nNYC2201003\\nZHONGSHAN\\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	STAR RAPID LIMITED	HAYWARD INDUSTRIES, INC.	NEW YORK, NY	NANSHA, CHINA	NYC246	SLVU4877415, VOLU4543799	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464996/receipts/xqxhfapjvxglgjf03xwf.pdf	Awaiting Bank In	2025-08-02 12:45:06.920406+00	2025-08-02 12:45:07.17506+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464687/invoices/byn2grzhudvwwnxub768.pdf	III532225	ray40	450	https://pay.example.com/53?ctn=450.0&svc=225.0&uniquenum=III532225	2025-08-06 15:23:17.111979+00	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 12:45:07.17506+00		0	1	1	\N	\N	\N	0.00
4	Ocean Express	ocean@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024004	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.225898+00	2025-07-29 02:57:56.225898+00	\N	\N	\N	100.00	\N	\N	2025-07-25 11:20:00+00	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.225898+00	\N	0	0	0	\N	\N	\N	0.00
5	Maritime Co	maritime@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024005	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.225898+00	2025-07-29 02:57:56.225898+00	\N	\N	\N	100.00	\N	\N	2025-07-28 13:55:00+00	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.225898+00	\N	0	0	0	\N	\N	\N	0.00
11	Premium Cargo	premium@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024011	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.914681+00	2025-07-29 02:57:56.914681+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	Paid 85%	30.0000	Unsettled	2025-07-14 16:15:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.914681+00	\N	0	0	0	\N	\N	\N	0.00
12	Elite Shipping	elite@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024012	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.914681+00	2025-07-29 02:57:56.914681+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	Paid 85%	30.0000	Unsettled	2025-07-17 11:45:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.914681+00	\N	0	0	0	\N	\N	\N	0.00
6	Fast Track Ltd	fast@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024006	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.574746+00	2025-07-29 02:57:56.574746+00	\N	\N	\N	100.00	\N	\N	2025-07-16 10:30:00+00	\N	\N	\N	\N	Allinpay	Paid 100%	0	Reserve Settled	2025-07-13 10:00:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.574746+00	\N	0	0	0	\N	\N	\N	0.00
7	Quick Ship	quick@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024007	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.574746+00	2025-07-29 02:57:56.574746+00	\N	\N	\N	100.00	\N	\N	2025-07-19 15:45:00+00	\N	\N	\N	\N	Allinpay	Paid 100%	0	Reserve Settled	2025-07-16 14:30:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.574746+00	\N	0	0	0	\N	\N	\N	0.00
8	Express Cargo	express@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024008	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.574746+00	2025-07-29 02:57:56.574746+00	\N	\N	\N	100.00	\N	\N	2025-07-23 08:20:00+00	\N	\N	\N	\N	Allinpay	Paid 100%	0	Reserve Settled	2025-07-20 08:45:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.574746+00	\N	0	0	0	\N	\N	\N	0.00
16	Pending Co	pending@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024016	\N	100.00	\N	Awaiting Bank In	2025-07-29 02:57:57.261642+00	2025-07-29 02:57:57.261642+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:57.261642+00	\N	0	0	0	\N	\N	\N	0.00
17	Waiting Ltd	waiting@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024017	\N	100.00	\N	Awaiting Bank In	2025-07-29 02:57:57.261642+00	2025-07-29 02:57:57.261642+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:57.261642+00	\N	0	0	0	\N	\N	\N	0.00
19	Invoice Co	invoice@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024019	\N	100.00	\N	Invoice Sent	2025-07-29 02:57:57.593704+00	2025-07-29 02:57:57.593704+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:57.593704+00	\N	0	0	0	\N	\N	\N	0.00
20	Billing Ltd	billing@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024020	\N	100.00	\N	Invoice Sent	2025-07-29 02:57:57.593704+00	2025-07-29 02:57:57.593704+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:57.593704+00	\N	0	0	0	\N	\N	\N	0.00
32	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753848347/bill/jinjyhzgbzlxnkumncud.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN	LARGOS	NYC2206288	OOCU7645789, TGBU8072614	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1753848472/receipts/d83d4e7585834c769fcc.pdf	Awaiting Bank In	2025-07-30 04:05:51.933004+00	2025-07-30 04:05:54.08487+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753848416/invoices/ilfil4zytyqiledsdpop.pdf	RAY121222	ray40	450	https://pay.dummy.com/link/32?amount=101.25&currency=USD&email=ykrw11%40myyahoo.com&ctn=None&description=Reserve+payment+for+CTN+RAY121222&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250730120647	2025-07-30 04:07:53.937003+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-30 04:05:54.08487+00		0	1	1	\N	\N	\N	0.00
3	Global Freight	global@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024003	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.225898+00	2025-07-29 02:57:56.225898+00	\N	\N	\N	100.00	\N	\N	2025-07-22 16:45:00+00	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.225898+00	\N	0	0	0	\N	\N	\N	0.00
10	Rapid Logistics	rapid@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024010	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.574746+00	2025-07-29 02:57:56.574746+00	\N	\N	\N	100.00	\N	\N	\N	\N	\N	\N	\N	Allinpay	Paid 85%	30.0000	Unsettled	2025-07-22 10:00:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.574746+00	\N	0	0	0	\N	\N	\N	0.00
15	Luxury Cargo	luxury@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024015	\N	100.00	\N	Paid and CTN Valid	2025-07-29 02:57:56.914681+00	2025-07-29 02:57:56.914681+00	\N	\N	\N	100.00	\N	\N	2025-07-29 10:44:58.120491+00	\N	\N	\N	\N	Allinpay	Paid 100%	30.0000	Reserve Settled	2025-07-24 16:15:00	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.914681+00	\N	0	0	0	\N	\N	\N	0.00
1	ABC Logistics	abc@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024001	\N	100.00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753786876/receipts/x61e0y9cgrtbatirld6e.pdf	Awaiting Bank In	2025-07-29 02:57:56.225898+00	2025-07-29 02:57:56.225898+00	\N	\N	\N	100.00	\N	2025-07-29 11:01:14.204881+00	2025-07-15 14:30:00+00	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.225898+00	\N	0	0	0	\N	\N	\N	0.00
2	XYZ Shipping	xyz@example.com	\N	\N	\N	\N	\N	\N	\N	BL2024002	\N	100.00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753786900/receipts/ecfeovkm1flqgiimmtd4.pdf	Awaiting Bank In	2025-07-29 02:57:56.225898+00	2025-07-29 02:57:56.225898+00	\N	\N	\N	100.00	\N	2025-07-29 11:01:41.333109+00	2025-07-18 09:15:00+00	\N	\N	\N	\N	Bank Transfer	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	2025-07-29 02:57:56.225898+00	\N	0	0	0	\N	\N	\N	0.00
43	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754013286/bill/r0vklchigzbxjr7bjsn5.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI	HUNGARY	NYC220	SLVU4877415, VOLU4543799, BBBB4543799	400	https://res.cloudinary.com/dtm46mski/raw/upload/v1754224904/receipts/nwvhoxzkzdkov9ngacew.pdf	Awaiting Bank In	2025-08-01 01:54:54.230314+00	2025-08-01 01:54:54.55871+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf	RAY001122	ray40	300	https://pay.dummy.com/link/43?amount=105.00&currency=USD&email=ykrw11%40myyahoo.com&ctn=None&description=Reserve+payment+for+CTN+RAY001122&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250801104540	2025-08-03 20:41:45.428484+00	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	300.00	400.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-08-01 01:54:54.55871+00		0	1	1	\N	\N	\N	0.00
21	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838210/bill/zrm9pjmdqwm7j4pau2sj.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 01:16:52.629323+00	2025-07-30 01:16:53.52086+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838208/invoice/bibq5svhqv2wtmtw8nkr.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838209/packing/yv4ywudnpmbxvsguy0k1.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:16:53.52086+00		0	0	0	\N	\N	\N	0.00
33	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753849401/bill/tah1lm49vgql7jj0a8vw.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC2212345	OOCU7645765, TGBU8072666	225.0	\N	Pending	2025-07-30 04:23:30.269638+00	2025-07-30 04:23:31.614963+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753849417/invoices/na0ffdf5acvgmbnios2b.pdf	XXH927464	ray40	450.0	https://pay.example.com/33?ctn=450.0&svc=225.0&uniquenum=XXH927464	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-30 04:23:31.614963+00		0	1	1	\N	\N	\N	0.00
52	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754137849/bill/smzvs7n01txxe36hfmaq.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC247	OOCU7645765, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754465145/receipts/yojl13ei5etzkitod8yj.pdf	Awaiting Bank In	2025-08-02 12:30:56.25201+00	2025-08-02 12:30:56.566483+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754465078/invoices/t0loagqp0padbfvdex5n.pdf	XNM078346	ray40	450	https://pay.example.com/52?ctn=450.0&svc=225.0&uniquenum=XNM078346	2025-08-06 15:25:46.232487+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 12:30:56.566483+00		0	1	1	\N	\N	\N	0.00
22	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838216/bill/hrmsvqghogjaz1fzvw5m.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 01:16:59.088318+00	2025-07-30 01:17:00.293707+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838208/invoice/bibq5svhqv2wtmtw8nkr.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838209/packing/yv4ywudnpmbxvsguy0k1.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:17:00.293707+00		0	0	0	\N	\N	\N	0.00
63	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754190218/bill/fw0zw6commydrlnzwwmx.PDF	{"document_type": "SEA WAYBILL", "bl_number": "254148256214", "shipper": "WANG TAI CO.", "consignee": "BORMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "HONGKONG", "port_of_discharge": "HAMBURG", "container_numbers": "KEIS2374724/20", "flight_or_vessel": "MEGA WAVE RIDER 245W", "product_description": "BAG FOR CHARGING CABLE 1800PCS", "paid_amount": "", "raw_text": "[OpenAI Vision fallback used]", "container_count": 1, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.69, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.7, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.69}, "extraction_method": "vision_api"}	WANG TAI CO.	BORMANN LOGISTICS GMBH & CO. OHG	HONGKONG	HAMBURG	NYC236	KEIS2374724/20	200	https://res.cloudinary.com/dtm46mski/raw/upload/v1754454181/receipts/vvbocfcyxd0hf2fzlu88.pdf	Awaiting Bank In	2025-08-03 03:03:47.267443+00	2025-08-03 03:03:47.505471+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf	DDZ549122	ray40	150	https://pay.example.com/63?ctn=100.0&svc=100.0&uniquenum=DDZ549122	2025-08-06 04:23:01.650985+00	\N	\N	\N	MEGA WAVE RIDER 245W	BAG FOR CHARGING CABLE 1800PCS			0		\N	\N	ocean	\N	1	\N	kg	default	\N	\N	150.00	200.00	0.69	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-08-03 03:03:47.505471+00		0	0	0	\N	\N	\N	0.00
56	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754140612/bill/oew0zxsiyopdjjd3i3c2.PDF	{"document_type": "BOL", "shipper": "A Joint Service Agreement", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "", "port_of_discharge": "HAMBURG", "bl_number": "254148256214", "container_numbers": "KEIS2374724", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "KEIS2374724/20' /EGDGS5468/54 PACKAGES", "raw_text": "BLUELINERS CORP.\\n(2) Shipper/Exporter\\nA Joint Service Agreement\\nWANG TAI CO. LTD\\nV, Enterprise Square\\n38 Wang Chiu Rd\\nKowloon Bay, Hongkong\\nSEA WAYBILL\\nNON-NEGOTIABLE\\n(5) Document No.\\n(6) Export References\\n(3) Consignee(complete name and address)\\nBOHRMANN LOGISTICS GMBH & CO. OHG\\nPARKSTRASSE 1\\n38440 WOLFSBURG GERMANY\\n(7) Forwarding Agent-References\\n(4) Notify Party (complete name and address)\\nWHEELS AG BIELEFELD\\nHERFORDER STRASSE 306\\n33609 BIELEFELD GERMANY\\n(8) Point and Country of Origin (for the Merchant's reference only)\\n(9) Also Notify Party (complete name and address)\\nNOTIABLE\\nHONGKONG\\n(17) Place of Delivery\\nHAMBURG\\n(12) Pre-carriage by\\n(14) Ocean Vessel/Voy. No.\\nMEGA WAVE RIDER\\n245W\\n(16) Port of Discharge\\nHAMBURG\\nThis Sea Waybill is issued at the request and for the convenience of the Merchant, but is nevertheless\\nsubject to the terms and conditions of the Carrier's standard long form Bill of Lading for this trade\\nwhich may be viewed online at [http://www.evergreen-line.com] or a copy obtained from the Carrier\\nor its agents.\\n(10) Onward Inland Routing/Export Instructions (which are contracted separately by\\nMerchants entirely for their own account and risk)\\n(18) Container No. And Seal No.\\nMarks & Nos.\\nCONTAINER NO./SEAL NO.\\n(19) Quantity And\\nKind of Packages\\nParticulars furnished by the Merchant\\n(20) Description of Goods\\nKEIS2374724/20' /EGDGS5468/54 PACKAGES\\nINV NO. 10550578\\nDN NO. 10550578\\nWHEELS 12E (G15F)\\nHAMBURG\\nNO. 1-2\\nWHEELS 5WOG (G15F)\\nHAMBURG\\nNO. 1-2\\nINV NO. 10550578\\nDN NO.\\n10550578\\n(22) TOTAL NUMBER OF\\nCONTAINERS OR PACKAGES\\n(IN WORDS)\\n1 x 20'\\n4 PACKAGE(S)\\nOTIABLE\\nDUNS NUMBER: 455889824\\nPART NAME+QUANTITY\\nBAG FOR CHARGING CABLE\\n1800PCS\\nPART NUMBER 15E 554 812\\nHS CODE 42029200.00\\nPART NAME+QUANTITY\\nWARNING VEST 1200PCS\\nPART NUMBER 7K3 512 568\\n*THE BALANCE OF BILL OF LADING SEE ATTACHED LIST *\\nTOTAL NUMBER OF ATTACHED 1 PAGE\\n\\"OCEAN FREIGHT COLLECT\\"\\nSHIPPER'S LOAD & COUNT\\n25 PACKAGES\\nONE (1) CONTAINER ONLY\\n(24) FREIGHT & CHARGES\\nRevenue Tons\\n(21) Measurement (M\\u00b3)\\nGross Weight (KGS)\\n20.4700 CBM\\n4,616.100 KGS\\nRate\\nPer Prepaid\\nAS\\nARRANGED\\n(23)\\nDeclared Value S\\nMerchant enters actual value of Goods\\nand pays, the applicable ad valorem\\nTariff rate, Carrier's package limitation.\\nshall not apply.\\nCollect\\nNON-NEG ABLE\\n(25) Waybill No.\\n254148256214\\n(26) Service Type/Mode\\nFCL/FCL 0/0\\n(27) Number of Original Waybills\\nNIL (0)\\n(28) Place and Date of Issue\\nKOWLOON BAY, HONGKONG AUG. 22, 2024\\n(33) Laden on Board\\nAUG. 22,2024\\nMEGA WAVE RIDER\\n245W\\nKOWLOON BAY, HONGKONG\\n(29) Prepaid at\\n(31) Exchange Rate\\n(30) Collect at\\nDESTINATION\\n(32) Exchange Rate\\nAs agent for the Carrier and Vessel Provider Blueline Corp.\\ndoing business as \\"Blueline\\"\\nFORM NO. DOC-1-006-02\\n"}	A Joint Service Agreement	BOHRMANN LOGISTICS GMBH & CO. OHG	hong	HAMBURG	NYC243	KEIS2374724	200	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464435/receipts/jxxjx1ykysg8igdz8t4e.pdf	Awaiting Bank In	2025-08-02 13:16:54.294995+00	2025-08-02 13:16:54.620758+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464363/invoices/cujtv9jxj30f0bozp3im.pdf		ray100	150		2025-08-06 15:13:57.951467+00	\N	\N	\N	MEGA WAVE RIDER	KEIS2374724/20' /EGDGS5468/54 PACKAGES			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-02 13:16:54.620758+00		0	0	0	\N	\N	\N	0.00
69	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754204236/bill/enp1ij0z2ypumkkjnstt.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC230	OOCU7645765, TGBU8072666	225	\N	Invoice Sent	2025-08-03 06:57:21.295067+00	2025-08-03 06:57:21.541175+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754449240/invoices/czk1i0b6dxgvnvqrswef.pdf	HPF908350	ray40	450	https://pay.example.com/69?ctn=450.0&svc=225.0&uniquenum=HPF908350	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 06:57:21.541175+00		0	1	1	email_ingestor	2025-08-06 03:04:22.781312+00	email	0.00
65	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754191672/bill/nkteurzde5ygh00b06zf.pdf	{"document_type": "Air Waybill", "bl_number": "001-12345678", "shipper": "CABLE AND STEEL COMPANY", "consignee": "CABLE BIG STORE", "port_of_loading": "NEW YORK", "port_of_discharge": "HEATHROW", "container_numbers": "", "flight_or_vessel": "AA1234/12", "product_description": "SOME ITEMS", "paid_amount": "1234.00", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	CABLE AND STEEL COMPANY	CABLE BIG STORE	NEW YORK	HEATHROW	NYC234		200	\N	Invoice Sent	2025-08-03 03:28:02.587479+00	2025-08-03 03:28:02.830432+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf	ray787944	ray40	150		\N	\N	\N	\N	AA1234/12	SOME ITEMS			0		\N	\N	ocean	\N	1	\N	kg	default	\N	\N	150.00	200.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-08-03 03:28:02.830432+00		0	0	0	\N	\N	\N	0.00
23	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838222/bill/esrcjpftozjitp6lktmb.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 01:17:04.369706+00	2025-07-30 01:17:05.380005+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838208/invoice/bibq5svhqv2wtmtw8nkr.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838209/packing/yv4ywudnpmbxvsguy0k1.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:17:05.380005+00		0	0	0	\N	\N	\N	0.00
34	ray40	gAAAAABoiaEvtBGGefrBuMAhyOCZd7Af-a398ahmVxGsFBp9dpvL9XJkJa8cO-_oCQQs8qzYg2tUkxwH1liP1HZ6WjZUFnWs4ljapOb-upNPPVApaD-8amw=	gAAAAABoiaEvKrat_mxn7ArCXrQ6TPp8y7DDvOIWbQmEmTUCGTgY0_SniSYEOronH27JdLCvRbGzK1bz04rQPtCoYztfil-jIA==	https://res.cloudinary.com/dtm46mski/raw/upload/v1753849421/bill/xcsamtzlqbanewpwizjh.PDF	{"document_type": "SEA WAYBILL", "bl_number": "254148256214", "shipper": "WANG TAI CO.", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "HONGKONG", "port_of_discharge": "HAMBURG", "container_numbers": "KEIS2374724/20", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "4 PACKAGE(S) DUNS NUMBER: 455889824 PART NAME+QUANTITY BAG FOR CHARGING CABLE 1800PCS", "paid_amount": "", "raw_text": "[OpenAI Vision fallback used]", "container_count": 1, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.69, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.7, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.69}, "extraction_method": "vision_api"}	WANG TAI CO	BOHRMANN LOGISTICS GMBH & CO. OH	HONGKONG2	HAMBUR	25414825621	KEIS2374724/	100	\N	Pending	2025-07-30 04:23:50.754612+00	2025-07-30 04:23:53.332757+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753850163/invoices/zhwerjsrlb9twuwpvgwo.pdf	NQL791193	ray40	100	https://pay.example.com/34?ctn=100.0&svc=100.0&uniquenum=NQL791193	\N	\N	\N	\N	MEGA WAVE RIDE	4 PACKAGE(S) DUNS NUMBER: 455889824 PART NAME+QUANTITY BAG FOR CHARGING CABLE 1800PCS	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	default	\N	\N	100.00	100.00	0.69	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 04:23:53.332757+00		0	0	0	\N	\N	\N	0.00
62	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754189028/bill/tqmmrhbayie1bdpz2q57.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC237	OOCU7645765, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754454181/receipts/vvbocfcyxd0hf2fzlu88.pdf	Awaiting Bank In	2025-08-03 02:43:51.450967+00	2025-08-03 02:43:51.693251+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754454028/invoices/afdczp1jnzu8tljbdl0p.pdf	NCU094011	ray40	450	https://pay.example.com/62?ctn=450.0&svc=225.0&uniquenum=NCU094011	2025-08-06 04:23:01.650985+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645765, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 02:43:51.693251+00		0	1	1	\N	\N	\N	0.00
57	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754186291/bill/utxyfslbohbjffm7uupr.PDF	{"document_type": "BOL", "shipper": "A Joint Service Agreement", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "", "port_of_discharge": "HAMBURG", "bl_number": "254148256214", "container_numbers": "KEIS2374724", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "KEIS2374724/20' /EGDGS5468/54 PACKAGES", "raw_text": "BLUELINERS CORP.\\n(2) Shipper/Exporter\\nA Joint Service Agreement\\nWANG TAI CO. LTD\\nV, Enterprise Square\\n38 Wang Chiu Rd\\nKowloon Bay, Hongkong\\nSEA WAYBILL\\nNON-NEGOTIABLE\\n(5) Document No.\\n(6) Export References\\n(3) Consignee(complete name and address)\\nBOHRMANN LOGISTICS GMBH & CO. OHG\\nPARKSTRASSE 1\\n38440 WOLFSBURG GERMANY\\n(7) Forwarding Agent-References\\n(4) Notify Party (complete name and address)\\nWHEELS AG BIELEFELD\\nHERFORDER STRASSE 306\\n33609 BIELEFELD GERMANY\\n(8) Point and Country of Origin (for the Merchant's reference only)\\n(9) Also Notify Party (complete name and address)\\nNOTIABLE\\nHONGKONG\\n(17) Place of Delivery\\nHAMBURG\\n(12) Pre-carriage by\\n(14) Ocean Vessel/Voy. No.\\nMEGA WAVE RIDER\\n245W\\n(16) Port of Discharge\\nHAMBURG\\nThis Sea Waybill is issued at the request and for the convenience of the Merchant, but is nevertheless\\nsubject to the terms and conditions of the Carrier's standard long form Bill of Lading for this trade\\nwhich may be viewed online at [http://www.evergreen-line.com] or a copy obtained from the Carrier\\nor its agents.\\n(10) Onward Inland Routing/Export Instructions (which are contracted separately by\\nMerchants entirely for their own account and risk)\\n(18) Container No. And Seal No.\\nMarks & Nos.\\nCONTAINER NO./SEAL NO.\\n(19) Quantity And\\nKind of Packages\\nParticulars furnished by the Merchant\\n(20) Description of Goods\\nKEIS2374724/20' /EGDGS5468/54 PACKAGES\\nINV NO. 10550578\\nDN NO. 10550578\\nWHEELS 12E (G15F)\\nHAMBURG\\nNO. 1-2\\nWHEELS 5WOG (G15F)\\nHAMBURG\\nNO. 1-2\\nINV NO. 10550578\\nDN NO.\\n10550578\\n(22) TOTAL NUMBER OF\\nCONTAINERS OR PACKAGES\\n(IN WORDS)\\n1 x 20'\\n4 PACKAGE(S)\\nOTIABLE\\nDUNS NUMBER: 455889824\\nPART NAME+QUANTITY\\nBAG FOR CHARGING CABLE\\n1800PCS\\nPART NUMBER 15E 554 812\\nHS CODE 42029200.00\\nPART NAME+QUANTITY\\nWARNING VEST 1200PCS\\nPART NUMBER 7K3 512 568\\n*THE BALANCE OF BILL OF LADING SEE ATTACHED LIST *\\nTOTAL NUMBER OF ATTACHED 1 PAGE\\n\\"OCEAN FREIGHT COLLECT\\"\\nSHIPPER'S LOAD & COUNT\\n25 PACKAGES\\nONE (1) CONTAINER ONLY\\n(24) FREIGHT & CHARGES\\nRevenue Tons\\n(21) Measurement (M\\u00b3)\\nGross Weight (KGS)\\n20.4700 CBM\\n4,616.100 KGS\\nRate\\nPer Prepaid\\nAS\\nARRANGED\\n(23)\\nDeclared Value S\\nMerchant enters actual value of Goods\\nand pays, the applicable ad valorem\\nTariff rate, Carrier's package limitation.\\nshall not apply.\\nCollect\\nNON-NEG ABLE\\n(25) Waybill No.\\n254148256214\\n(26) Service Type/Mode\\nFCL/FCL 0/0\\n(27) Number of Original Waybills\\nNIL (0)\\n(28) Place and Date of Issue\\nKOWLOON BAY, HONGKONG AUG. 22, 2024\\n(33) Laden on Board\\nAUG. 22,2024\\nMEGA WAVE RIDER\\n245W\\nKOWLOON BAY, HONGKONG\\n(29) Prepaid at\\n(31) Exchange Rate\\n(30) Collect at\\nDESTINATION\\n(32) Exchange Rate\\nAs agent for the Carrier and Vessel Provider Blueline Corp.\\ndoing business as \\"Blueline\\"\\nFORM NO. DOC-1-006-02\\n"}	A Joint Service Agreement	BOHRMANN LOGISTICS GMBH & CO. OHG	hong	HAMBURG	NYC242	KEIS2374724	200	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464296/receipts/cdulyxdhyo7cpx65bmo0.pdf	Awaiting Bank In	2025-08-03 01:58:13.320889+00	2025-08-03 01:58:13.578589+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464258/invoices/ouy3hjiyqz5hekfdfyyq.pdf		ray100	150		2025-08-06 15:11:37.172347+00	\N	\N	\N	MEGA WAVE RIDER	KEIS2374724/20' /EGDGS5468/54 PACKAGES			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-03 01:58:13.578589+00		0	0	0	\N	\N	\N	0.00
72	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754299101/bill/tqccqywviexfyy1yrbsv.pdf	{"document_type": "Air Waybill", "bl_number": "001-12345678", "shipper": "CABLE AND STEEL COMPANY", "consignee": "CABLE BIG STORE", "port_of_loading": "NEW YORK", "port_of_discharge": "HEATHROW", "container_numbers": "", "flight_or_vessel": "AA1234/12", "product_description": "SOME ITEMS", "paid_amount": "1234.00", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	CABLE AND STEEL COMPANY	CABLE BIG STORE	NEW YORK	HEATHROW	NYC227	NA	100	https://res.cloudinary.com/dtm46mski/raw/upload/v1754448846/receipts/sqf7dtlr9zbtypktrvgt.pdf	Paid and CTN Valid	2025-08-04 09:18:27.358373+00	2025-08-04 09:18:27.672929+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754445798/invoices/asvvpk0dpu1f4z9qrelh.pdf	RAY090909	ray40	100	https://pay.dummy.com/link/72?amount=200.00&currency=USD&email=ykrw11%40myyahoo.com&ctn=None&description=Reserve+payment+for+CTN+RAY090909&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250806100315	2025-08-06 02:54:06.611123+00	2025-08-06 09:37:16.8242+00	\N	\N	AA1234/12	SOME ITEMS			0		\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-08-04 09:18:27.672929+00		0	0	0	email_ingestor	2025-08-06 02:54:09.12092+00	email	0.00
35	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859042/bill/byaazktck6lyj102b2f5.pdf	{"document_type": "BILL OF LADING FOR OCEAN TRANSPORT OR MULTIMODAL TRANSPORT", "bl_number": "602436760", "shipper": "GUARDIAN INDUSTRIES CORP LTD.", "consignee": "WESSEX PICTURES", "port_of_loading": "Laem Chabang, Thailand", "port_of_discharge": "Felixstowe", "container_numbers": "", "flight_or_vessel": "SCT VIETNAM v.1292", "product_description": "1 Container Said to Contain 11 Packages FLOAT CLEAR 2.00 MM 915 X 1220 MM TRANSHIP AT ANJUNG PELEPAS BY NORTHERN JUBILEE V.1302 HS. NO.7005.29 INVOICE NO.CVO07531", "paid_amount": "", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	GUARDIAN INDUSTRIES CORP LTD.	WESSEX PICTURES	Laem Chabang, Thailand	Felixstowe	602436760		\N	\N	Pending	2025-07-30 07:04:14.867427+00	2025-07-30 07:04:17.117234+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859041/invoice/sdt59fxyr9kuank73zyi.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859041/packing/ry4qxpsuxhp1mywtbsqn.pdf	SCT VIETNAM v.1292	1 Container Said to Contain 11 Packages FLOAT CLEAR 2.00 MM 915 X 1220 MM TRANSHIP AT ANJUNG PELEPAS BY NORTHERN JUBILEE V.1302 HS. NO.7005.29 INVOICE NO.CVO07531	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 07:04:17.117234+00		0	0	0	\N	\N	\N	0.00
24	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838227/bill/ex5w6xaedri6oqyk1mjr.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753839070/receipts/d82fd2b2e4894a998140.pdf	Awaiting Bank In	2025-07-30 01:17:09.376098+00	2025-07-30 01:17:10.644514+00	\N	\N	ray40	\N	\N	2025-07-30 01:31:12.191421+00	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838208/invoice/bibq5svhqv2wtmtw8nkr.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838209/packing/yv4ywudnpmbxvsguy0k1.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:17:10.644514+00		0	0	0	\N	\N	\N	0.00
59	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754188863/bill/mv9smkpjonbkktbbommm.pdf	{"document_type": "BOL", "bl_number": "NYC2212345", "shipper": "RAY WONG LTD", "consignee": "SMART FAMOUS LTD", "port_of_loading": "HONG KONG", "port_of_discharge": "NIGERIA", "container_numbers": "OOCU7645765, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY WONG LTD\\nNYC2212345\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nJAPAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nHONG KONG\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645765\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	RAY WONG LTD	SMART FAMOUS LTD	HONG KONG	NIGERIA	NYC240	OOCU7645765, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754463274/receipts/mlijdu57z2s2mq5hxx3a.pdf	Awaiting Bank In	2025-08-03 02:41:09.910952+00	2025-08-03 02:41:10.17666+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754460557/invoices/l6ciziuqle3ci7rt86co.pdf	NEQ718107	ray40	450	https://pay.example.com/59?ctn=450.0&svc=225.0&uniquenum=NEQ718107	2025-08-06 14:54:35.802061+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 02:41:10.17666+00		0	1	1	\N	\N	\N	0.00
71	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754298903/bill/hjng5zctlbu7ubkrrip9.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN	LARGOS	NYC228	OOCU7645789, TGBU8072614	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754448846/receipts/sqf7dtlr9zbtypktrvgt.pdf	Paid and CTN Valid	2025-08-04 09:15:10.792654+00	2025-08-04 09:15:11.035037+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754445844/invoices/pitab1ide6k59vywsa9c.pdf	RAY765432	ray40	450		2025-08-06 02:54:06.611123+00	2025-08-06 09:37:11.154516+00	\N	\N	OOCL BERLIN v.041E				0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-04 09:15:11.035037+00		0	1	1	email_ingestor	2025-08-06 02:54:07.98281+00	email	0.00
58	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754188826/bill/tefdy3dodhtrlrb1wiix.pdf	{"document_type": "BOL", "shipper": "MAERSK LINE", "consignee": "WESSEX PICTURES", "port_of_loading": "Laem Chabang", "port_of_discharge": "Felixstowe", "bl_number": "602436760", "container_numbers": "MRKU6569533", "flight_or_vessel": "SCT VIETNAM", "product_description": "1 Container Said to Contain 11 Packages", "raw_text": "Shipper\\nMAERSK LINE\\nGUARDIAN INDUSTRIES CORP LTD.\\n42 MOO 7 NONGPLAMOH SUB-DISTRICT,\\nNONGKHAE, SARABURI 18140 THAILAND\\nBILL OF LADING FOR OCEAN TRANSPORT\\nOR MULTIMODAL TRANSPORT\\nBooking No.\\n602436760\\nExport references\\nSCAC\\nMAEU\\nB/L No. 602436760\\nSvc Contract\\n485554\\nOnward inland routing (Not part of Carriage as defined in clause 1. For account and risk of Merchant)\\n.\\nConsignee (negotiable only if consigned \\"to order\\", \\"to order of\\" a named Person or \\"to order of bearer\\")\\nWESSEX PICTURES\\nUNIT 1142, AXIS CENTRE\\nCLEEVE ROAD LEATHERHEAD,\\nSURREY KT22 7RD UNITED KINGDOM\\nNotify Party (see clause 22)\\nAL YOUNGER LTD.WESSEX PICTURES,\\nUNIT 1142, AXIS CENTRE \\u00b7\\nCLEEVE ROAD LEATHERHEAD,\\nSURREY KT22 7RD UK**\\nVessel (see clause 1+19)\\nSCT VIETNAM\\nPort of Loading\\nLaem Chabang, Thailand\\nVoyage No.\\n1292\\nPort of Discharge\\nFelixstowe\\nPlace of Receipt. Applicable only when document used as Multimodal Transport B/L. (see clause 1)\\nBANGKOK, THAILAND\\nPlace of Delivery. Applicable only when document used as Multimodal Transport B/L. (see clause 1)\\nLeatherhead, United Kingdom\\nPARTICULARS FURNISHED BY SHIPPER\\nKind of Packages; Description of goods; Marks and Numbers; Container No./Seal No.\\n1 Container Said to Contain 11 Packages\\nFLOAT CLEAR 2.00 MM 915 X 1220 MM\\nTRANSHIP AT TANJUNG PELEPAS BY NORTHERN\\nJUBILEE V.1302\\nHS. NO.7005.29\\nINVOICE NO.CV007531\\n**PHONE 01372 377738 FAX:01372 386315\\nEMAIL: SALES@WESSEX-PICTURES.CO.UK\\nGIN\\nNO.1-11\\nWeight\\n22696.000 KGS\\nORIGINAL\\nMADE IN THAILAND\\nMRKU6569533 ML-TH2122861 20 DRY 8'6 11 Packages 22696.000 KGS 25.0000 CBM\\nSHIPPER'S LOAD, STOW, WEIGHT AND COUNT\\nFREIGHT PREPAID\\nCY/SD\\nMeasurement\\n25.0000 CBM\\n\\u0e2d\\u0e32\\u0e42\\u0e1b\\u0e2a\\u0e2d\\u0e19\\u0e21\\n\\u0e27\\u0e32\\u0e17\\u0e40\\u0e2a\\u0e15\\u0e47\\u0e21\\u0e1a\\nAbove particulars as declared by Shipper, but without responsibility of or representation by Carrier (see clause 14)\\nFreight & Charges\\nRate\\nUnit\\nCurrency\\nPrepaid\\n\\u0e1a\\u0e32\\u0e17\\n\\u0e1a\\u0e32\\u0e17\\nCollect\\nCarrier's Receipt (see clause 1 and 14). Total number\\nPlace of Issue of B/L\\nof containers or packages received by Carrier.\\n1 container\\nNumber & Sequence of Original B(S)/L\\n1/THREE\\nDeclared Value (see clause 7.3)\\nBangkok\\nDate of Issue of B/L\\n2013-01-02\\nShipped on Board Date (Local Time)\\n2012-12-30\\nSHIPPED, as far as ascertained by reasonable means of checking, In apparent good order and condition unless otherwise stated herein, the total\\nnumber or quantity of Containers or other packages or units Indicated in the box entitled \\"Carrier's Receipt for carriage from the Port of Loading (or\\nthe Place of Receipt, if mentioned above) to the Part of Discharge (or the Place of Delivery, if mentioned above), such carriage being always subject to\\nthe terms, rights, defences, provisions, conditions, exceptions, Amitations, and liberties hereof (INCLUDING ALL THOSE TERMS AND CONDITIONS ON\\nTHE REVERSE HEREOF NUMBERED 1-26 AND THOSE TERMS AND CONDITIONS CONTAINED IN THE CARRIER'S APPLICABLE TARIFF) and the\\nMerchant's attention is drawn in particular to the Carrier's liberties in respect of on deck stowage (see clause 18) and the carrying vessel (see cause\\n19). Where the bill of lading is non-negotiable the Carrier may give delivery of the Goods to the named consignee upon reasonable proof of Identity\\nand without requiring surrender of an original bill of lading. Where the bill of lading is negotiable, the Merchant is obliged to surrender one original,\\nduly endorsed, In exchange for the Goods. The Carrier accepts a duty reasonable care to check that any such document which the Merchant\\nsurrenders as a bill of lading is genuine and original. If the Carrier complies with this duty, it will be entitled to deliver the Goods against what it\\nreasonably believes to be a genuine and original bill of lading, such delivery discharging the Carrier's delivery obligations. In accepting this bill of\\nlading, any local customs or privileges to the contrary notwithstanding, the Merchant agrees to be bound by al Terms and Conditions stated herein\\nwhether written, printed, stamped or Incorporated on the face or reverse side hereof, as fully as if they were all signed by the Merchant.\\nIN WITNESS WHEREOF the number of original Bills of Lading stated on this side have been signed and wherever one original Bill of Lading has been\\nsurrendered any others shall be vold.\\nSigned for the Carrier A.P. M\\u00f8ller-M\\u00e6rsk A/S trading as Maersk Line\\nThi\\nMAERSK LINE (THAILAND) LTD.\\nAs Agent(s) for the Carrier\\n0015\\n\\u3092\\nACE USA\\nOpen Policy No.\\nIndemnity Insurance Co of North America\\nN02178977\\nSERVICE OFFICE:\\nSpecial Marine Policy\\nW000472086\\nNo.\\nCOPY\\n(ORIGINAL AND DUPLICATE ISSUED ONE\\nOF WHICH BEING ACCOMPLISHED, THE\\nOTHER TO BE NULL AND VOID)\\nof Chicago Branch Office\\n8,924.00 (GBP) (PLACE & DATE) LAEM CHABANG, THAILAND, December 30, 2012\\nThis Company, in consideration of a premium as agreed, and subject to the Terms and Conditions printed or stamped hereon\\nand/or attached hereto, does insure, lost or notdusardian Industries Corp Ltd.\\nFor account of whom it may concern; to be shipped by the vessel\\nTHERN JUBILEE V.1302\\nFrom LAEM CHABANG, THAILAND\\nTO LEATHERHEAD, UNITED KINGDOM\\nLawful Goods Consisting of FLOAT CLEAR\\nValued at Sum hereby insured\\nSCT VIETNAM V.1292/ NOR\\nand connecting conveyances.\\nMARKS AND NUMBERS\\nGIN\\nNO.1-11\\nNumber of Packages 11 PACKAGES\\nEight Thousand Nine Hundred Twenty Four POUND STERLING And Zero Cents\\n(GBP)\\nMADE IN THAILAND\\nSHIPPED ON 12/30/12\\nLoss, if any, payable to Assured\\nor order.\\nInv. # CV007531\\nB/L #\\nTERMS AND CONDITIONS - SEE ALSO BACK HEREOF\\nWAREHOUSE TO WAREHOUSE: This insurance attaches from the time the goods leave the Warehouse and/or Store at the place named in the Policy for the commencement of the transit and continues during\\nthe ordinary course of transit, including customary transhipment if any, until the goods are discharged overside from the overseas vessel at the final port. Thereafter the insurance continues whilst the goods are in\\ntransit and/or awaiting transit until delivered to final warehouse at the destination named in the Policy or until the expiry of 15 days (or 30 days if the destination to which the goods are insured is outside the limits\\nof the port) whichever shall first occur. The time limits referred to above to be reckoned from midnight of the day on which the discharge overside of the goods hereby insured from the overseas vessel is\\ncompleted. Held covered at a premium to be arranged in the event of transhipment, if any, other than as above and/or in the event of delay in excess of the above time limits arising from circumstances beyond the\\ncontrol of the Assured. NOTE -- IT IS NECESSARY FOR TIJE ASSURED TO GIVE PROMPT NOTICE TO THESE ASSURERS WIJEN TIIEY BECOME AWARE OF AN EVENT FOR WINICII THEY\\nARE \\"HIELD COVERED\\" UNDER THIS POLICY AND THE RIGHT TO SUCII COVER IS DEPENDENT ON COMPLIANCE WITII TIIIS OBLIGATION.\\nSHORE CLAUSE: Where this insurance by its terms covers while on docks, wharves or elsewhere on shore, and/or during land transportation, it shall include the risks of collision, derailment, overturning or\\nother accident to the conveyance, fire, lightning, sprinkler leakage, cyclones, hurricanes, earthquakes, floods (meaning the rising of navigable waters), and/or collapse or subsidence of docks or wharves, even\\nthough the insurance be otherwise F.P.A.\\nBOTH TO BLAME CLAUSE: Where goods are shipped under a Bill of Lading containing the so-called \\"Both to Blame Collision\\" Clause, these Assurers agree as to all losses covered by this insurance, to\\nindemnify the Assured for this Policy's proportion of any amount (not exceeding the amount insured) which the Assured may be legally bound to pay to the shipowners under such clause. In the event that such\\nliability is asserted the Assured agrees to notify these Assurers who shall have the right at their own cost and expense to defend the Assured against such claim.\\nMACHINERY CLAUSE: When the property insured under this Policy includes a machine consisting when complete for sale or use of several parts, then in case of loss or damage covered by this insurance to\\nany part of such machine, these Assurers shall be liable only for the proportion of the insured value of the part lost or damaged, or at the Assured's option, for the cost and expense, including labor and forwarding\\ncharges, of replacing and repairing the lost or damaged part; but in no event shall these Assurers be liable for more than the insured value of the complete machine.\\nLABELS CLAUSE: In case of damage affecting labels, capsules or wrappers, these Assurers, if liable therefor under the terms of this policy, shall not be liable for more than an amount sufficient to pay the cost\\nof new labels, capsules or wrappers, and the cost of reconditioning the goods, but in no event shall these Assurers be liable for more than the insured value of the damaged merchandise.\\nDELAY CLAUSE: Warranted free of claim for loss of market or for loss, damage or deterioration arising from delay, whether caused by a peril insured against or otherwise, unless expressly assumed in writing\\nhereon.\\nAMERICAN INSTITUTE CLAUSES: This insurance, in addition to the foregoing, is also subject to the following American Institute Cargo Clauses, current forms:\\n4. GENERAL AVERAGE 6. BILL OF LADING, ETC. 8. CONSTRUCTIVE TOTAL LOSS\\n5. EXPLOSION\\n7. INCHMAREE\\n9. CARRIER 10. EXTENDED R.A.C.E.\\nPERILS CLAUSE: Touching the adventures and perils which this Company is contented to bear, and takes upon itself, they are of the seas, assailing thieves, jettisons, barratry of the master and mariners, and all other\\nlike perils, losses and misfortunes (illicit or contraband trade excepted in all cases), that have or shall come to the hurt, detriment or damage of the said goods and merchandise, or any part thereof.\\n1. CRAFT, ETC. 3. WAREHOUSE & FORWARDING CHARGES,\\n2. DEVIATION PACKAGES TOTALLY LOST LOADING, ETC.\\n11. CHEMICAL, BIOLOGICAL, ELECTROMAGNETIC\\nEXCLUSION TO AMERICAN INSTITUTE CLAUSES.\\nAVERAGE TERMS: ON DECK AND SUBJECT TO AN \\"ON DECK\\" BILL OF LADING -- (which must be so declared by the Assured): Free of Particular Average unless caused by the vessel being\\nstranded, sunk, burnt, on fire or in collision, but including jettison and/or washing overboard irrespective of percentage. EXCEPT WIIILE SUBJECT TO AN \\"ON DECK\\" BILL OF LADING:\\nThis policy is extended to include the provisions of the following clauses as if the current form of each were endorsed hereon: American Institute Clauses - F. C. & S. Warranty, Marine Extension Clauses, S. R. &\\nC. C. Endorsement, War Risk Insurance, Nuclear Exclusion, Where appropriate: South America 60 Day Clause.\\n-INSTITUTE CARGO CLAUSES(A),INSTITUTE WAR CLAUSES(CARGO)\\n-INSTITUTE STRIKES CLAUSES(CARGO),INSTITUTE RADIOACTIVE CONTAMINation excluDING CLAUSE\\nOUR INT.\\nASSURED\\nTHIS SPACE RESERVED FOR COMPANY USE\\nREINS. CEDED\\nS.O.\\nAGENCY NO.\\nPOLICY NO.\\nCERT. OR DEC. NO.\\nVESSEL\\nB/L DATE\\nVOYAGE\\nCGU\\nN02178977\\nCLASS\\nAMOUNT\\nPREMIUM\\nRATE\\n%\\nMOD.\\nSCT VIETNAM V.1292/\\nNOR\\n12/30/12\\nFROM: LAEM CHABANG, THAILAN\\nTO: LEATHERHEAD,UNITED KI\\nCOMMODITY\\nFLOAT\\nCLEAR\\nPREMIUM\\nCOMM.\\nRATE %\\nCLASS\\nTAX\\nSTATE\\nLINE\\nTAX DIST.\\nOR REINS.\\nCO. CODE\\nS. S.\\nLINE\\nVOYAGE\\nCOM-\\nMODITY\\nMARINE\\nWAR\\nDUTY - MAR.\\nDUTY. WAR\\nTOTALS\\nMA-2098q (Issued via the Internet)\\nINSTRUCTIONS TO CLAIMANTS ON REVERSE SIDE\\nCOPY\\nREGISTRATION\\n1\\n1. Goods consigned from (exporter's business name, address,\\ncountry)\\nGUARDIAN INDUSTRIES CORP LTD. 42 MOO 7, NONGPLAMOH SUB-DISTRICT,\\nNONGKHAE, SARABURI 19140 THAILAND TEL: 036-373373 FAX: 036-373343-350 TAX ID:\\n3030888105\\n2. Goods consigned to (consignee's name, address, country)\\nWESSEX PICTURES\\nUNIT 1142, AXIS CENTRE CLEEVE ROAD LEATHERHEAD, SURREY KT22 7RD\\nUNITED KINGDOM\\nReference No\\nIA2012-0234811\\nGENERALIZED SYSTEM OF PREFERENCES\\nCERTIFICATE OF ORIGIN\\n(Combined declaration and certificate)\\nIssued in\\nFORM A\\nTHAILAND\\n(country)\\n3. Means of transport and route (as far as known)\\n4. For official use\\nBY SEA FREIGHT\\n5. Item\\nnum-\\nber\\n6. Marks and\\nnumbers of\\npackages\\n7. Number and kind of packages; description of goods\\nPage: 1 of 1\\n1\\nGIN\\nFLOAT CLEAR 2.00 MM 915X1220 MM ****\\nNO. 1-11\\nTOTAL: ELEVEN (11) PACKAGES****\\nMADE IN\\nTHAILAND\\nSee notes overleaf\\n8. Origin\\ncriterion\\n(see notes\\noverleaf)\\n9. Gross weight\\nor other\\nquantity\\n10. Number\\nand date of\\ninvoices\\n\\"W\\"7005\\n22,696.00 KGS\\nCV007531\\n25/12/2012\\n\\u0e02\\u0e49\\u0e32\\u0e1e\\u0e40\\u0e08\\u0e49\\u0e32\\u0e43\\u0e19\\u0e19\\u0e32\\u0e21\\u0e02\\u0e2d\\u0e07\\u0e1a\\u0e23\\u0e34\\u0e29\\u0e31\\u0e17..\\n\\u0e44\\u0e14\\u0e49\\u0e23\\u0e31\\u0e1a p \\u0e40\\u0e23\\u0e35\\u0e22\\u0e1a\\u0e23\\u0e49\\u0e2d\\u0e22\\u0e41\\u0e25\\u0e49\\u0e27\\n.\\u0e2a\\u0e07 \\u0e2d\\n11. Certification\\nIt is hereby certified, on the basis of control carried out, that\\nthe declaration by the exporter is correct.\\n\\u0e01\\u0e23\\u0e21\\u0e1f\\n\\u0e23\\u0e30\\u0e40\\u0e17\\u0e28\\n12. Declaration by the exporter\\nThe undersigned hereby declares that the above details and\\nstatements are correct; that all the goods were\\nproduced in\\nTHAILAND\\ncountry)\\nand that they comply witorigin requirements specified\\nfor those good in\\nsuster of preferences for\\ngoods exported ardian Industries Corp Ltd\\nUNITED KINGDOM\\n(importing country)\\nSARABURI 18140 27/12/2012\\n27. DEC. 2012\\nPlace and date, signature of authorized signatory\\nBANGKOK\\nDEPARTMENT\\nTHAILAND\\nOF\\nF FOREIGN TRADE GOVERNMEN\\nPlace and date, signature and stamp of cortifying authority\\nNo. 0004998\\n"}	MAERSK LINE	WESSEX PICTURES	Laem Chabang	Felixstowe	NYC241	MRKU6569533	200	https://res.cloudinary.com/dtm46mski/raw/upload/v1754463274/receipts/mlijdu57z2s2mq5hxx3a.pdf	Awaiting Bank In	2025-08-03 02:40:27.602537+00	2025-08-03 02:40:27.858574+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754460585/invoices/s3ngq3t3ovqotauohkz0.pdf		ray100	150		2025-08-06 14:54:35.511329+00	\N	\N	\N	SCT VIETNAM	1 Container Said to Contain 11 Packages			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-03 02:40:27.858574+00		0	0	0	\N	\N	\N	0.00
75	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754478006/bill/tuhy5igmpkqprw9rfljt.pdf	{"document_type": "BOL", "bl_number": "NYC2207777", "shipper": "RAY TOP", "consignee": "SMART FAMOUS", "port_of_loading": "HONG KONG", "port_of_discharge": "", "container_numbers": "OOCU7645898, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY TOP\\nNYC2207777\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nHONG KONG\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nNIGERIA\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645898\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	RAY TOP	SMART FAMOUS	HONG KONG		NYC2207777	OOCU7645898, TGBU8072666	\N	\N	Pending	2025-08-06 11:00:15.270691+00	2025-08-06 11:00:15.522622+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-06 11:00:15.522622+00		0	1	1	\N	\N	\N	0.00
25	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838232/bill/levys1ozn7m9y32vcso6.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 01:17:14.602562+00	2025-07-30 01:17:15.542571+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838208/invoice/bibq5svhqv2wtmtw8nkr.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753838209/packing/yv4ywudnpmbxvsguy0k1.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:17:15.542571+00		0	0	0	\N	\N	\N	0.00
36	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859060/bill/fczx5yfhlvvxjunakbp5.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN		NYC2206288	OOCU7645789, TGBU8072614	\N	\N	Pending	2025-07-30 07:04:26.056784+00	2025-07-30 07:04:28.498413+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859041/invoice/sdt59fxyr9kuank73zyi.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859041/packing/ry4qxpsuxhp1mywtbsqn.pdf	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 10255.60 KGS/64.57 CBM, 10231.20 KGS/64.57 CBM	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-30 07:04:28.498413+00		0	1	1	\N	\N	\N	0.00
46	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754131282/bill/vb8zepprtd46fjxw8omm.pdf	{"document_type": "BOL", "bl_number": "NYC2206288", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING INTERNATIONAL", "port_of_loading": "YANTIAN", "port_of_discharge": "", "container_numbers": "OOCU7645789, TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645789, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nPERFECT TOP TECHNOLOGIES LTD.\\nNYC2206288\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nJETHING INTERNATIONAL\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nYANTIAN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nLARGOS\\nLARGOS\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645789\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072614\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED \\n/JUN/20\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                   \\n                                          AGENT OF THE MASTER\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of re\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\n\\u0018\\n\\nMO.\\nDAY\\nYEAR\\n\\nF LADING\\n8\\n91\\nERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\nON BOARD:\\n022\\n port of \\nbove \\nt the above mentioned\\nions, limitations,\\nstated \\n   \\neceipt and \\nsignee \\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING INTERNATIONAL	YANTIAN	largos	NYC2206288	OOCU7645789, TGBU8072614	225	\N	Invoice Sent	2025-08-02 10:41:29.974334+00	2025-08-02 10:41:30.256156+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754131782/invoices/vddw428gpoyjulgooo9w.pdf	ray123999	ray40	450	https://pay.dummy.com/link/46?amount=101.25&currency=USD&email=ykrw11%40myyahoo.com&ctn=None&description=Reserve+payment+for+CTN+ray123999&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250802184939	\N	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645789, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072614, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 10:41:30.256156+00		0	1	1	\N	\N	\N	0.00
55	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754140018/bill/jugqqljumj9ag7gtux6r.pdf	{"document_type": "Air Waybill", "bl_number": "001-12345678", "shipper": "CABLE AND STEEL COMPANY", "consignee": "CABLE BIG STORE", "port_of_loading": "NEW YORK", "port_of_discharge": "HEATHROW", "container_numbers": "", "flight_or_vessel": "AA1234/12", "product_description": "SOME ITEMS", "paid_amount": "1234.00", "raw_text": "[OpenAI Vision fallback used]", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.5700000000000001, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 1.0, "overall": 0.5700000000000001}, "extraction_method": "vision_api"}	CABLE AND STEEL COMPANY	CABLE BIG STORE	NEW YORK	HEATHROW	NYC244	NA	100	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464435/receipts/jxxjx1ykysg8igdz8t4e.pdf	Awaiting Bank In	2025-08-02 13:07:08.581607+00	2025-08-02 13:07:08.832798+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754464379/invoices/qykrujou843mg2gcgsr5.pdf		ray40	100		2025-08-06 15:13:57.651737+00	\N	\N	\N	AA1234/12	SOME ITEMS			0		\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.57	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-08-02 13:07:08.832798+00		0	0	0	\N	\N	\N	0.00
26	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753839505/bill/jaibqhms11m29fb9i1rp.pdf	{"document_type": "", "bl_number": "", "shipper": "", "consignee": "", "port_of_loading": "", "port_of_discharge": "", "container_numbers": "", "flight_or_vessel": "", "product_description": "", "paid_amount": "", "raw_text": "", "container_count": 0, "container_types": [], "container_type": null, "container_count_20ft": 0, "container_count_40ft": 0, "container_count_40ft_hc": 0, "total_weight_kg": null, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "default", "calculated_ctn_fee": 100.0, "calculated_service_fee": 100.0, "calculated_total_fee": 200.0, "ocr_confidence_score": 0.27, "pricing_calculation_log": {"method": "default", "reason": "No specific pricing data available"}, "validation_result": {"missing_fields": ["shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number"], "has_critical_missing": true, "confidence_score": 0.0, "needs_revalidation": true, "revalidation_performed": true}, "confidence_breakdown": {"container_detection": 0.3, "weight_detection": 0.2, "shipment_classification": 0.7, "field_validation": 0.0, "overall": 0.27}, "extraction_method": "ai"}							\N	\N	Pending	2025-07-30 01:38:27.42806+00	2025-07-30 01:38:28.404325+00	\N	\N	ray40	\N	\N	\N	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753839503/invoice/g29dcrrthspeffmwzjlf.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753839504/packing/woa2x6yba3z24olatdgq.pdf			not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	0	\N	kg	default	\N	\N	100.00	100.00	0.27	f	\N	\N	\N	{"method": "default", "reason": "No specific pricing data available"}	2025-07-30 01:38:28.404325+00		0	0	0	\N	\N	\N	0.00
37	ray	ykrw13@gmail.com	5600	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859173/bill/mykleqjescxgwu6vgnt7.pdf	{"document_type": "BOL", "shipper": "MAERSK LINE", "consignee": "WESSEX PICTURES", "port_of_loading": "Laem Chabang", "port_of_discharge": "Felixstowe", "bl_number": "602436760", "container_numbers": "MRKU6569533", "flight_or_vessel": "SCT VIETNAM", "product_description": "1 Container Said to Contain 11 Packages", "raw_text": "Shipper\\nMAERSK LINE\\nGUARDIAN INDUSTRIES CORP LTD.\\n42 MOO 7 NONGPLAMOH SUB-DISTRICT,\\nNONGKHAE, SARABURI 18140 THAILAND\\nBILL OF LADING FOR OCEAN TRANSPORT\\nOR MULTIMODAL TRANSPORT\\nBooking No.\\n602436760\\nExport references\\nSCAC\\nMAEU\\nB/L No. 602436760\\nSvc Contract\\n485554\\nOnward inland routing (Not part of Carriage as defined in clause 1. For account and risk of Merchant)\\n.\\nConsignee (negotiable only if consigned \\"to order\\", \\"to order of\\" a named Person or \\"to order of bearer\\")\\nWESSEX PICTURES\\nUNIT 1142, AXIS CENTRE\\nCLEEVE ROAD LEATHERHEAD,\\nSURREY KT22 7RD UNITED KINGDOM\\nNotify Party (see clause 22)\\nAL YOUNGER LTD.WESSEX PICTURES,\\nUNIT 1142, AXIS CENTRE \\u00b7\\nCLEEVE ROAD LEATHERHEAD,\\nSURREY KT22 7RD UK**\\nVessel (see clause 1+19)\\nSCT VIETNAM\\nPort of Loading\\nLaem Chabang, Thailand\\nVoyage No.\\n1292\\nPort of Discharge\\nFelixstowe\\nPlace of Receipt. Applicable only when document used as Multimodal Transport B/L. (see clause 1)\\nBANGKOK, THAILAND\\nPlace of Delivery. Applicable only when document used as Multimodal Transport B/L. (see clause 1)\\nLeatherhead, United Kingdom\\nPARTICULARS FURNISHED BY SHIPPER\\nKind of Packages; Description of goods; Marks and Numbers; Container No./Seal No.\\n1 Container Said to Contain 11 Packages\\nFLOAT CLEAR 2.00 MM 915 X 1220 MM\\nTRANSHIP AT TANJUNG PELEPAS BY NORTHERN\\nJUBILEE V.1302\\nHS. NO.7005.29\\nINVOICE NO.CV007531\\n**PHONE 01372 377738 FAX:01372 386315\\nEMAIL: SALES@WESSEX-PICTURES.CO.UK\\nGIN\\nNO.1-11\\nWeight\\n22696.000 KGS\\nORIGINAL\\nMADE IN THAILAND\\nMRKU6569533 ML-TH2122861 20 DRY 8'6 11 Packages 22696.000 KGS 25.0000 CBM\\nSHIPPER'S LOAD, STOW, WEIGHT AND COUNT\\nFREIGHT PREPAID\\nCY/SD\\nMeasurement\\n25.0000 CBM\\n\\u0e2d\\u0e32\\u0e42\\u0e1b\\u0e2a\\u0e2d\\u0e19\\u0e21\\n\\u0e27\\u0e32\\u0e17\\u0e40\\u0e2a\\u0e15\\u0e47\\u0e21\\u0e1a\\nAbove particulars as declared by Shipper, but without responsibility of or representation by Carrier (see clause 14)\\nFreight & Charges\\nRate\\nUnit\\nCurrency\\nPrepaid\\n\\u0e1a\\u0e32\\u0e17\\n\\u0e1a\\u0e32\\u0e17\\nCollect\\nCarrier's Receipt (see clause 1 and 14). Total number\\nPlace of Issue of B/L\\nof containers or packages received by Carrier.\\n1 container\\nNumber & Sequence of Original B(S)/L\\n1/THREE\\nDeclared Value (see clause 7.3)\\nBangkok\\nDate of Issue of B/L\\n2013-01-02\\nShipped on Board Date (Local Time)\\n2012-12-30\\nSHIPPED, as far as ascertained by reasonable means of checking, In apparent good order and condition unless otherwise stated herein, the total\\nnumber or quantity of Containers or other packages or units Indicated in the box entitled \\"Carrier's Receipt for carriage from the Port of Loading (or\\nthe Place of Receipt, if mentioned above) to the Part of Discharge (or the Place of Delivery, if mentioned above), such carriage being always subject to\\nthe terms, rights, defences, provisions, conditions, exceptions, Amitations, and liberties hereof (INCLUDING ALL THOSE TERMS AND CONDITIONS ON\\nTHE REVERSE HEREOF NUMBERED 1-26 AND THOSE TERMS AND CONDITIONS CONTAINED IN THE CARRIER'S APPLICABLE TARIFF) and the\\nMerchant's attention is drawn in particular to the Carrier's liberties in respect of on deck stowage (see clause 18) and the carrying vessel (see cause\\n19). Where the bill of lading is non-negotiable the Carrier may give delivery of the Goods to the named consignee upon reasonable proof of Identity\\nand without requiring surrender of an original bill of lading. Where the bill of lading is negotiable, the Merchant is obliged to surrender one original,\\nduly endorsed, In exchange for the Goods. The Carrier accepts a duty reasonable care to check that any such document which the Merchant\\nsurrenders as a bill of lading is genuine and original. If the Carrier complies with this duty, it will be entitled to deliver the Goods against what it\\nreasonably believes to be a genuine and original bill of lading, such delivery discharging the Carrier's delivery obligations. In accepting this bill of\\nlading, any local customs or privileges to the contrary notwithstanding, the Merchant agrees to be bound by al Terms and Conditions stated herein\\nwhether written, printed, stamped or Incorporated on the face or reverse side hereof, as fully as if they were all signed by the Merchant.\\nIN WITNESS WHEREOF the number of original Bills of Lading stated on this side have been signed and wherever one original Bill of Lading has been\\nsurrendered any others shall be vold.\\nSigned for the Carrier A.P. M\\u00f8ller-M\\u00e6rsk A/S trading as Maersk Line\\nThi\\nMAERSK LINE (THAILAND) LTD.\\nAs Agent(s) for the Carrier\\n0015\\n\\u3092\\nACE USA\\nOpen Policy No.\\nIndemnity Insurance Co of North America\\nN02178977\\nSERVICE OFFICE:\\nSpecial Marine Policy\\nW000472086\\nNo.\\nCOPY\\n(ORIGINAL AND DUPLICATE ISSUED ONE\\nOF WHICH BEING ACCOMPLISHED, THE\\nOTHER TO BE NULL AND VOID)\\nof Chicago Branch Office\\n8,924.00 (GBP) (PLACE & DATE) LAEM CHABANG, THAILAND, December 30, 2012\\nThis Company, in consideration of a premium as agreed, and subject to the Terms and Conditions printed or stamped hereon\\nand/or attached hereto, does insure, lost or notdusardian Industries Corp Ltd.\\nFor account of whom it may concern; to be shipped by the vessel\\nTHERN JUBILEE V.1302\\nFrom LAEM CHABANG, THAILAND\\nTO LEATHERHEAD, UNITED KINGDOM\\nLawful Goods Consisting of FLOAT CLEAR\\nValued at Sum hereby insured\\nSCT VIETNAM V.1292/ NOR\\nand connecting conveyances.\\nMARKS AND NUMBERS\\nGIN\\nNO.1-11\\nNumber of Packages 11 PACKAGES\\nEight Thousand Nine Hundred Twenty Four POUND STERLING And Zero Cents\\n(GBP)\\nMADE IN THAILAND\\nSHIPPED ON 12/30/12\\nLoss, if any, payable to Assured\\nor order.\\nInv. # CV007531\\nB/L #\\nTERMS AND CONDITIONS - SEE ALSO BACK HEREOF\\nWAREHOUSE TO WAREHOUSE: This insurance attaches from the time the goods leave the Warehouse and/or Store at the place named in the Policy for the commencement of the transit and continues during\\nthe ordinary course of transit, including customary transhipment if any, until the goods are discharged overside from the overseas vessel at the final port. Thereafter the insurance continues whilst the goods are in\\ntransit and/or awaiting transit until delivered to final warehouse at the destination named in the Policy or until the expiry of 15 days (or 30 days if the destination to which the goods are insured is outside the limits\\nof the port) whichever shall first occur. The time limits referred to above to be reckoned from midnight of the day on which the discharge overside of the goods hereby insured from the overseas vessel is\\ncompleted. Held covered at a premium to be arranged in the event of transhipment, if any, other than as above and/or in the event of delay in excess of the above time limits arising from circumstances beyond the\\ncontrol of the Assured. NOTE -- IT IS NECESSARY FOR TIJE ASSURED TO GIVE PROMPT NOTICE TO THESE ASSURERS WIJEN TIIEY BECOME AWARE OF AN EVENT FOR WINICII THEY\\nARE \\"HIELD COVERED\\" UNDER THIS POLICY AND THE RIGHT TO SUCII COVER IS DEPENDENT ON COMPLIANCE WITII TIIIS OBLIGATION.\\nSHORE CLAUSE: Where this insurance by its terms covers while on docks, wharves or elsewhere on shore, and/or during land transportation, it shall include the risks of collision, derailment, overturning or\\nother accident to the conveyance, fire, lightning, sprinkler leakage, cyclones, hurricanes, earthquakes, floods (meaning the rising of navigable waters), and/or collapse or subsidence of docks or wharves, even\\nthough the insurance be otherwise F.P.A.\\nBOTH TO BLAME CLAUSE: Where goods are shipped under a Bill of Lading containing the so-called \\"Both to Blame Collision\\" Clause, these Assurers agree as to all losses covered by this insurance, to\\nindemnify the Assured for this Policy's proportion of any amount (not exceeding the amount insured) which the Assured may be legally bound to pay to the shipowners under such clause. In the event that such\\nliability is asserted the Assured agrees to notify these Assurers who shall have the right at their own cost and expense to defend the Assured against such claim.\\nMACHINERY CLAUSE: When the property insured under this Policy includes a machine consisting when complete for sale or use of several parts, then in case of loss or damage covered by this insurance to\\nany part of such machine, these Assurers shall be liable only for the proportion of the insured value of the part lost or damaged, or at the Assured's option, for the cost and expense, including labor and forwarding\\ncharges, of replacing and repairing the lost or damaged part; but in no event shall these Assurers be liable for more than the insured value of the complete machine.\\nLABELS CLAUSE: In case of damage affecting labels, capsules or wrappers, these Assurers, if liable therefor under the terms of this policy, shall not be liable for more than an amount sufficient to pay the cost\\nof new labels, capsules or wrappers, and the cost of reconditioning the goods, but in no event shall these Assurers be liable for more than the insured value of the damaged merchandise.\\nDELAY CLAUSE: Warranted free of claim for loss of market or for loss, damage or deterioration arising from delay, whether caused by a peril insured against or otherwise, unless expressly assumed in writing\\nhereon.\\nAMERICAN INSTITUTE CLAUSES: This insurance, in addition to the foregoing, is also subject to the following American Institute Cargo Clauses, current forms:\\n4. GENERAL AVERAGE 6. BILL OF LADING, ETC. 8. CONSTRUCTIVE TOTAL LOSS\\n5. EXPLOSION\\n7. INCHMAREE\\n9. CARRIER 10. EXTENDED R.A.C.E.\\nPERILS CLAUSE: Touching the adventures and perils which this Company is contented to bear, and takes upon itself, they are of the seas, assailing thieves, jettisons, barratry of the master and mariners, and all other\\nlike perils, losses and misfortunes (illicit or contraband trade excepted in all cases), that have or shall come to the hurt, detriment or damage of the said goods and merchandise, or any part thereof.\\n1. CRAFT, ETC. 3. WAREHOUSE & FORWARDING CHARGES,\\n2. DEVIATION PACKAGES TOTALLY LOST LOADING, ETC.\\n11. CHEMICAL, BIOLOGICAL, ELECTROMAGNETIC\\nEXCLUSION TO AMERICAN INSTITUTE CLAUSES.\\nAVERAGE TERMS: ON DECK AND SUBJECT TO AN \\"ON DECK\\" BILL OF LADING -- (which must be so declared by the Assured): Free of Particular Average unless caused by the vessel being\\nstranded, sunk, burnt, on fire or in collision, but including jettison and/or washing overboard irrespective of percentage. EXCEPT WIIILE SUBJECT TO AN \\"ON DECK\\" BILL OF LADING:\\nThis policy is extended to include the provisions of the following clauses as if the current form of each were endorsed hereon: American Institute Clauses - F. C. & S. Warranty, Marine Extension Clauses, S. R. &\\nC. C. Endorsement, War Risk Insurance, Nuclear Exclusion, Where appropriate: South America 60 Day Clause.\\n-INSTITUTE CARGO CLAUSES(A),INSTITUTE WAR CLAUSES(CARGO)\\n-INSTITUTE STRIKES CLAUSES(CARGO),INSTITUTE RADIOACTIVE CONTAMINation excluDING CLAUSE\\nOUR INT.\\nASSURED\\nTHIS SPACE RESERVED FOR COMPANY USE\\nREINS. CEDED\\nS.O.\\nAGENCY NO.\\nPOLICY NO.\\nCERT. OR DEC. NO.\\nVESSEL\\nB/L DATE\\nVOYAGE\\nCGU\\nN02178977\\nCLASS\\nAMOUNT\\nPREMIUM\\nRATE\\n%\\nMOD.\\nSCT VIETNAM V.1292/\\nNOR\\n12/30/12\\nFROM: LAEM CHABANG, THAILAN\\nTO: LEATHERHEAD,UNITED KI\\nCOMMODITY\\nFLOAT\\nCLEAR\\nPREMIUM\\nCOMM.\\nRATE %\\nCLASS\\nTAX\\nSTATE\\nLINE\\nTAX DIST.\\nOR REINS.\\nCO. CODE\\nS. S.\\nLINE\\nVOYAGE\\nCOM-\\nMODITY\\nMARINE\\nWAR\\nDUTY - MAR.\\nDUTY. WAR\\nTOTALS\\nMA-2098q (Issued via the Internet)\\nINSTRUCTIONS TO CLAIMANTS ON REVERSE SIDE\\nCOPY\\nREGISTRATION\\n1\\n1. Goods consigned from (exporter's business name, address,\\ncountry)\\nGUARDIAN INDUSTRIES CORP LTD. 42 MOO 7, NONGPLAMOH SUB-DISTRICT,\\nNONGKHAE, SARABURI 19140 THAILAND TEL: 036-373373 FAX: 036-373343-350 TAX ID:\\n3030888105\\n2. Goods consigned to (consignee's name, address, country)\\nWESSEX PICTURES\\nUNIT 1142, AXIS CENTRE CLEEVE ROAD LEATHERHEAD, SURREY KT22 7RD\\nUNITED KINGDOM\\nReference No\\nIA2012-0234811\\nGENERALIZED SYSTEM OF PREFERENCES\\nCERTIFICATE OF ORIGIN\\n(Combined declaration and certificate)\\nIssued in\\nFORM A\\nTHAILAND\\n(country)\\n3. Means of transport and route (as far as known)\\n4. For official use\\nBY SEA FREIGHT\\n5. Item\\nnum-\\nber\\n6. Marks and\\nnumbers of\\npackages\\n7. Number and kind of packages; description of goods\\nPage: 1 of 1\\n1\\nGIN\\nFLOAT CLEAR 2.00 MM 915X1220 MM ****\\nNO. 1-11\\nTOTAL: ELEVEN (11) PACKAGES****\\nMADE IN\\nTHAILAND\\nSee notes overleaf\\n8. Origin\\ncriterion\\n(see notes\\noverleaf)\\n9. Gross weight\\nor other\\nquantity\\n10. Number\\nand date of\\ninvoices\\n\\"W\\"7005\\n22,696.00 KGS\\nCV007531\\n25/12/2012\\n\\u0e02\\u0e49\\u0e32\\u0e1e\\u0e40\\u0e08\\u0e49\\u0e32\\u0e43\\u0e19\\u0e19\\u0e32\\u0e21\\u0e02\\u0e2d\\u0e07\\u0e1a\\u0e23\\u0e34\\u0e29\\u0e31\\u0e17..\\n\\u0e44\\u0e14\\u0e49\\u0e23\\u0e31\\u0e1a p \\u0e40\\u0e23\\u0e35\\u0e22\\u0e1a\\u0e23\\u0e49\\u0e2d\\u0e22\\u0e41\\u0e25\\u0e49\\u0e27\\n.\\u0e2a\\u0e07 \\u0e2d\\n11. Certification\\nIt is hereby certified, on the basis of control carried out, that\\nthe declaration by the exporter is correct.\\n\\u0e01\\u0e23\\u0e21\\u0e1f\\n\\u0e23\\u0e30\\u0e40\\u0e17\\u0e28\\n12. Declaration by the exporter\\nThe undersigned hereby declares that the above details and\\nstatements are correct; that all the goods were\\nproduced in\\nTHAILAND\\ncountry)\\nand that they comply witorigin requirements specified\\nfor those good in\\nsuster of preferences for\\ngoods exported ardian Industries Corp Ltd\\nUNITED KINGDOM\\n(importing country)\\nSARABURI 18140 27/12/2012\\n27. DEC. 2012\\nPlace and date, signature of authorized signatory\\nBANGKOK\\nDEPARTMENT\\nTHAILAND\\nOF\\nF FOREIGN TRADE GOVERNMEN\\nPlace and date, signature and stamp of cortifying authority\\nNo. 0004998\\n"}	MAERSK LINE	WESSEX PICTURES	Laem Chabang	Felixstowe	602436760	MRKU6569533	\N	\N	Pending	2025-07-30 07:06:17.512931+00	2025-07-30 07:06:19.835978+00	\N	\N	ray401	\N	\N	\N	\N	\N	\N	SCT VIETNAM	1 Container Said to Contain 11 Packages	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	{}	2025-07-30 07:06:19.835978+00		0	0	0	\N	\N	\N	0.00
47	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754133791/bill/eeqrjq2tch6vo390cvpr.pdf	{"document_type": "BOL", "bl_number": "NYC2201666", "shipper": "SOLEX LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHENZHEN", "port_of_discharge": "NEW YORK, NY", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSOLEX LTD\\nNYC2201666\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nZHONGSHAN\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHENZHEN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nFRANCE\\nNEW YORK, NY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	SOLEX LTD	HAYWARD INDUSTRIES, INC.	SHENZHEN	NEW YORK, NY	NYC2201666	SLVU4877415, VOLU4543799	225.0	\N	Pending	2025-08-02 11:23:16.836508+00	2025-08-02 11:23:17.092375+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754133797/invoices/zp3chkxctxxqwy5iyx3q.pdf	RJG713773	ray40	450.0	https://pay.example.com/47?ctn=450.0&svc=225.0&uniquenum=RJG713773	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 11:23:17.092375+00		0	1	1	\N	\N	\N	0.00
60	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754188926/bill/yhp1dbxboeb8yzyrbsye.pdf	{"document_type": "BOL", "bl_number": "NYC2207777", "shipper": "RAY TOP", "consignee": "SMART FAMOUS", "port_of_loading": "HONG KONG", "port_of_discharge": "", "container_numbers": "OOCU7645898, TGBU8072666", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each", "paid_amount": "", "raw_text": "Proforma Bill of Lading - Draft\\nBILL OF LADING\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nRAY TOP\\nNYC2207777\\nFLAT L, 4/F., VALIANT INDUSTRIAL. \\n6. EXPORT REFERENCES\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\n ZIP CODE\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS\\nFREIGHT BROKERS GLOBAL SERVICES, INC.\\nC/O DEAN WAREHOUSE SVC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\n292 KILVERT STREET\\nTEL:347-926-7002 FAX:718-327-5318\\nWARWICK, RI 02886 USA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTEL: (401)583-1100 \\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nSAME AS CONSIGNEE\\n\\u8acb\\u5c0d\\u55ae\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nOOCL BERLIN v.041E\\nHONG KONG\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nNIGERIA\\nNIGERIA\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n(22)\\nNO SHIPPING MARKS\\n2X40'HQ\\nSHIPPER'S LOAD & COUNT\\n20486.80\\n`\\n129.14\\nCOUNTRY OF ORIGIN: CHINA\\n4872 CTNS in 84 x PLTS\\nCONTR # OOCU7645898\\nPO#38920A\\nSEAL  # 17531510\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013025A-3T Rev K\\n10255.60 KGS/64.57 CBM\\nqty:2436each\\nCONTR # TGBU8072666\\nPO#38894\\nSEAL  # 21863263\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n2436 CTNS IN 42 x PLTS\\nG1-013032A-3T Rev D\\n10231.20 KGS/64.57 CBM\\nqty:2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\n  \\nSHIPPED ON BOARD:\\n/JUN/2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the above mentioned\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limitations,\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\n\\u0018\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 10255.6, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	RAY TOP	SMART FAMOUS	HONG KONG	hong	NYC239	OOCU7645898, TGBU8072666	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754455385/receipts/xrxf7xqz94o5c6i21jh0.pdf	Awaiting Bank In	2025-08-03 02:42:10.319446+00	2025-08-03 02:42:10.57736+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754454458/invoices/ftorekme5dc8ztbkuqep.pdf		ray40	450		2025-08-06 12:43:06.375673+00	\N	\N	\N	OOCL BERLIN v.041E	20486.80 KGS/129.14 CBM, 2436 CTNS in 42 x PLTS, CONTR # OOCU7645898, PO#38920A, SEAL # 17531510, ENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013025A-3T Rev K, 10255.60 KGS/64.57 CBM, qty:2436each, CONTR # TGBU8072666, PO#38894, SEAL # 21863263, ENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY), 2436 CTNS IN 42 x PLTS, G1-013032A-3T Rev D, 10231.20 KGS/64.57 CBM, qty:2436each			0		\N	\N	ocean	40ft	2	10255.60	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 02:42:10.57736+00		0	1	1	\N	\N	\N	0.00
66	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754191839/bill/jf4ukvh3lfjo6saox5yn.pdf	{"document_type": "BOL", "bl_number": "B/L NUMBER", "shipper": "STAR RAPID LIMITED", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "NEW YORK, NY", "port_of_discharge": "NANSHA, CHINA", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "BILL OF LADING\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSTAR RAPID LIMITED\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nHAYWARD INDUSTRIES, INC. \\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAINERIZED(Vessel Only)\\nNEW YORK, NY\\nNEW YORK, NY\\nCY/CY\\nYES\\n NO\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B deta      Gross Weight\\n          Measurement\\nOF PACKAGES\\n \\n   (Kilos)\\n                  (18)\\n(19)\\n(20)\\n(21)\\n(22)\\n2x40'HQ SHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED ON BOARD :\\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN.,2022\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading and port of \\n                 SUBJECT TO CORRECTION\\nPREPAID COLLECT\\ndischage, and for arragement or  procurement of per-carriage from place of receipt and \\non-carriage to place of delivery, where stated above, the goods as specified above \\nin apparent good order and condition unless otherwise stated. The goods to be delivered at the abov\\nport of discharge or place of delivery, whichever is applicable, subject always to the exceptions, limit\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Consignee \\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwise stated \\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                      \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\nFreight Brokers Global Services, Inc.\\nTIMON v.2201E\\nNANSHA, CHINA\\nNYC2201003\\nZHONGSHAN\\n\\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	STAR RAPID LIMITED	HAYWARD INDUSTRIES, INC.	NEW YORK, NY	NANSHA, CHINA	NYC233	SLVU4877415, VOLU4543799	225	\N	Invoice Sent	2025-08-03 03:30:43.690817+00	2025-08-03 03:30:43.98544+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754451721/invoices/iroh7eigu7lmpmonruzb.pdf	FYJ490495	ray40	450	https://pay.example.com/66?ctn=450.0&svc=225.0&uniquenum=FYJ490495	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 03:30:43.98544+00		0	1	1	\N	\N	\N	0.00
67	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754201026/bill/xq7wchwsoublvbf5xxvy.PDF	{"document_type": "BOL", "shipper": "A Joint Service Agreement", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "", "port_of_discharge": "HAMBURG", "bl_number": "254148256214", "container_numbers": "KEIS2374724", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "KEIS2374724/20' /EGDGS5468/54 PACKAGES", "raw_text": "BLUELINERS CORP.\\n(2) Shipper/Exporter\\nA Joint Service Agreement\\nWANG TAI CO. LTD\\nV, Enterprise Square\\n38 Wang Chiu Rd\\nKowloon Bay, Hongkong\\nSEA WAYBILL\\nNON-NEGOTIABLE\\n(5) Document No.\\n(6) Export References\\n(3) Consignee(complete name and address)\\nBOHRMANN LOGISTICS GMBH & CO. OHG\\nPARKSTRASSE 1\\n38440 WOLFSBURG GERMANY\\n(7) Forwarding Agent-References\\n(4) Notify Party (complete name and address)\\nWHEELS AG BIELEFELD\\nHERFORDER STRASSE 306\\n33609 BIELEFELD GERMANY\\n(8) Point and Country of Origin (for the Merchant's reference only)\\n(9) Also Notify Party (complete name and address)\\nNOTIABLE\\nHONGKONG\\n(17) Place of Delivery\\nHAMBURG\\n(12) Pre-carriage by\\n(14) Ocean Vessel/Voy. No.\\nMEGA WAVE RIDER\\n245W\\n(16) Port of Discharge\\nHAMBURG\\nThis Sea Waybill is issued at the request and for the convenience of the Merchant, but is nevertheless\\nsubject to the terms and conditions of the Carrier's standard long form Bill of Lading for this trade\\nwhich may be viewed online at [http://www.evergreen-line.com] or a copy obtained from the Carrier\\nor its agents.\\n(10) Onward Inland Routing/Export Instructions (which are contracted separately by\\nMerchants entirely for their own account and risk)\\n(18) Container No. And Seal No.\\nMarks & Nos.\\nCONTAINER NO./SEAL NO.\\n(19) Quantity And\\nKind of Packages\\nParticulars furnished by the Merchant\\n(20) Description of Goods\\nKEIS2374724/20' /EGDGS5468/54 PACKAGES\\nINV NO. 10550578\\nDN NO. 10550578\\nWHEELS 12E (G15F)\\nHAMBURG\\nNO. 1-2\\nWHEELS 5WOG (G15F)\\nHAMBURG\\nNO. 1-2\\nINV NO. 10550578\\nDN NO.\\n10550578\\n(22) TOTAL NUMBER OF\\nCONTAINERS OR PACKAGES\\n(IN WORDS)\\n1 x 20'\\n4 PACKAGE(S)\\nOTIABLE\\nDUNS NUMBER: 455889824\\nPART NAME+QUANTITY\\nBAG FOR CHARGING CABLE\\n1800PCS\\nPART NUMBER 15E 554 812\\nHS CODE 42029200.00\\nPART NAME+QUANTITY\\nWARNING VEST 1200PCS\\nPART NUMBER 7K3 512 568\\n*THE BALANCE OF BILL OF LADING SEE ATTACHED LIST *\\nTOTAL NUMBER OF ATTACHED 1 PAGE\\n\\"OCEAN FREIGHT COLLECT\\"\\nSHIPPER'S LOAD & COUNT\\n25 PACKAGES\\nONE (1) CONTAINER ONLY\\n(24) FREIGHT & CHARGES\\nRevenue Tons\\n(21) Measurement (M\\u00b3)\\nGross Weight (KGS)\\n20.4700 CBM\\n4,616.100 KGS\\nRate\\nPer Prepaid\\nAS\\nARRANGED\\n(23)\\nDeclared Value S\\nMerchant enters actual value of Goods\\nand pays, the applicable ad valorem\\nTariff rate, Carrier's package limitation.\\nshall not apply.\\nCollect\\nNON-NEG ABLE\\n(25) Waybill No.\\n254148256214\\n(26) Service Type/Mode\\nFCL/FCL 0/0\\n(27) Number of Original Waybills\\nNIL (0)\\n(28) Place and Date of Issue\\nKOWLOON BAY, HONGKONG AUG. 22, 2024\\n(33) Laden on Board\\nAUG. 22,2024\\nMEGA WAVE RIDER\\n245W\\nKOWLOON BAY, HONGKONG\\n(29) Prepaid at\\n(31) Exchange Rate\\n(30) Collect at\\nDESTINATION\\n(32) Exchange Rate\\nAs agent for the Carrier and Vessel Provider Blueline Corp.\\ndoing business as \\"Blueline\\"\\nFORM NO. DOC-1-006-02\\n"}	A Joint Service Agreement	BOHRMANN LOGISTICS GMBH & CO. OHG	hong kong	HAMBURG	NYC232	KEIS2374724	200	\N	Invoice Sent	2025-08-03 06:03:48.353334+00	2025-08-03 06:03:48.608925+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754450566/invoices/i4p1wg89kmyavy75iu4x.pdf	ray48309483	ray100	150	https://pay.dummy.com/link/67?amount=350.00&currency=USD&email=ray633008%40gmail.com&ctn=None&description=Reserve+payment+for+CTN+ray48309483&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250806112243	\N	\N	\N	\N	MEGA WAVE RIDER	KEIS2374724/20' /EGDGS5468/54 PACKAGES			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-03 06:03:48.608925+00		0	0	0	\N	\N	\N	0.00
61	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754188970/bill/pnksqk5dxhtrmbrugora.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI	hong 	NYC238	SLVU4877415, VOLU4543799, BBBB4543799	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1754455271/receipts/qtzejo938lji21jwjcku.pdf	Awaiting Bank In	2025-08-03 02:42:54.304193+00	2025-08-03 02:42:54.586694+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754454435/invoices/xt8o4xjcz3z3fqq37qh6.pdf		ray40	450		2025-08-06 12:41:12.166519+00	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	3	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-08-03 02:42:54.586694+00		0	1	1	\N	\N	\N	0.00
27	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1753840017/bill/lkqfztw7cc5rdwrf2ahu.pdf	{"document_type": "BOL", "bl_number": "NYC2201666", "shipper": "SOLEX LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHENZHEN", "port_of_discharge": "NEW YORK, NY", "container_numbers": "SLVU4877415, VOLU4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nSOLEX LTD\\nNYC2201666\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSMART FAMOUS LTD\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nZHONGSHAN\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHENZHEN\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nFRANCE\\nNEW YORK, NY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: TWO(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 2, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.9100000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 2, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": [], "has_critical_missing": false, "confidence_score": 1.0, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 1.0, "overall": 0.9100000000000001}, "extraction_method": "ai"}	SOLEX LTD	HAYWARD INDUSTRIES, INC.	SHENZHEN	NEW YORK, NY	NYC2201666	SLVU4877415, VOLU4543799	225	https://res.cloudinary.com/dtm46mski/raw/upload/v1753840647/receipts/90d6c0a6b1b54481a928.pdf	Awaiting Bank In	2025-07-30 01:47:03.923822+00	2025-07-30 01:47:04.769317+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1753840056/invoices/nhdrajazcjkf9yqefssk.pdf	MRV248651	ray40	450	https://pay.example.com/27?ctn=450.0&svc=225.0&uniquenum=MRV248651	2025-07-30 01:57:29.560342+00	\N	https://res.cloudinary.com/dtm46mski/raw/upload/v1753840015/invoice/hxlnpq0bwkuzuriqsgvt.pdf	https://res.cloudinary.com/dtm46mski/raw/upload/v1753840016/packing/jynnfcfiezjzlw8z8iso.pdf	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL			0		\N	\N	ocean	40ft	2	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.91	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 2, "container_types": ["40ft", "40ft_hc"]}	2025-07-30 01:47:04.769317+00		0	1	1	\N	\N	\N	0.00
38	ray	ykrw13@gmail.com	5600	https://res.cloudinary.com/dtm46mski/raw/upload/v1753859182/bill/nfraoweahoc4n70myve1.pdf	{"document_type": "BOL", "shipper": "PERFECT TOP TECHNOLOGIES LTD.", "consignee": "JETHING", "port_of_loading": "YANTIAN", "port_of_discharge": "LARGOS", "bl_number": "NYC2206288", "container_numbers": "TGBU8072614", "flight_or_vessel": "OOCL BERLIN v.041E", "product_description": "(20)", "raw_text": "Proforma Bill of Lading\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\nPERFECT TOP TECHNOLOGIES LTD.\\nFLAT L, 4/F., VALIANT INDUSTRIAL.\\nCENTRE, 2-12 AU PUI WAN STREET.,\\nFO TAN, SHATIN, HONG KONG.\\nZIP CODE\\n3. CONSIGNED TO\\nJETHING\\nINTERNATIONAL\\nC/O DEAN WAREHOUSE SVC.\\n292 KILVERT STREET\\nWARWICK, RI 02886 USA\\nTEL: (401) 583-1100\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\nSAME AS CONSIGNEE\\n12. PRE-CARRIAGE BY\\n-\\nDraft\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\n5. DOCUMENT NUMBER\\n6. EXPORT REFERENCES\\nBILL OF\\n5a. B/L NUMBER\\nNYC2206288\\n7. FORWARDING AGENT (Name and address - references)\\nFREIGHT BROKERS GLOBAL SERVICES,\\nINC.\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 1169\\nTEL: 347-926-7002 FAX: 718-327-5318\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\n\\u8acb\\u5c0d\\u55ae\\n14. EXPORTING CARRIER\\nOOCL BERLIN v.041E\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\nLARGOS\\nMARKS AND NUMBERS\\n(18)\\nNO SHIPPING MARKS\\nCOUNTRY OF ORIGIN: CHINA\\n15. PORT OF LOADING/EXPORT\\nYANTIAN\\n17. PLACE OF DELIVERY BY ON-CARRIER\\nLARGOS\\nNUMBER\\nOF PACKAGES\\n(19)\\n2x40'HQ\\n10. LOADING PIER / TERMINAL\\n11. TYPE OF MOVE\\nCY/CY\\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n(20)\\n|SHIPPER'S LOAD & COUNT\\n4872 CTNS in 84 \\u00d7 PLTS\\n11a. CONTAINI\\nYES\\nGross Weight\\nMeas\\n(Kilos)\\n(21)\\n20486.80\\n129.14\\nCONTR # 0OCU7645789\\nSEAL # 17531510\\n2436 CTNS IN 42 \\u00d7 PLTS\\n10255.60 KGS/64.57 CBM\\nCONTR # TGBU8072614\\nSEAL # 21863263\\n2436 CTNS IN 42 \\u00d7 PLTS\\n10231.20 KGS/64.57 CBM\\nPO#38920A\\nENCL, AQR, NO XFRMR, WHT (PUR TURN-KEY)\\nG1-013025A-3T Rev K\\nqty: 2436each\\nPO#38894\\nENCL, TROL, NO XFRMR, WHT (PUR TURN-KEY)\\n|G1-013032A-3T Rev D\\nqty: 2436each\\n\\"FREIGHT COLLECT\\"\\nTOTAL: TWO (40'HQ) CONTAINERS ONLY.\\n\\" THIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS \\"\\nSHIPPED\\n/JUN/2\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\nSUBJECT TO CORRECTION\\nFREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nPREPAID\\nCOLLECT\\nReceived by Carrier for shipment by ocean vessel between port of loading and\\ndischage, and for arragement or procurement of per-carriage from place of re\\non-carriage to place of delivery, where stated above, the goods as specified ab\\nin apparent good order and condition unless otherwise stated. The goods to be delivered at\\nport of discharge or place of delivery, whichever is applicable, subject always to the excepti\\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Cons\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three (3) original Bills of Lading have been signed, not otherwise s\\nabove, one of which being accomplished the others shall be void.\\nDATED AT\\nBY\\nAGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n= LADING\\n91\\nERIZED(Vessel Only)\\nNO\\nsurement\\n(22)\\nON BOARD:\\n022\\nport of\\nceipt and\\nbove\\nthe above mentioned\\nons, limitations,\\nsignee\\nstated\\n\\n"}	PERFECT TOP TECHNOLOGIES LTD.	JETHING	YANTIAN	LARGOS	NYC2206288	TGBU8072614	\N	\N	Pending	2025-07-30 07:06:26.088642+00	2025-07-30 07:06:27.5183+00	\N	\N	ray401	\N	\N	\N	\N	\N	\N	OOCL BERLIN v.041E	(20)	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	\N	1	\N	kg	container	\N	\N	\N	\N	\N	f	\N	\N	\N	{}	2025-07-30 07:06:27.5183+00		0	0	0	\N	\N	\N	0.00
48	ray40	ykrw11@myyahoo.com	749324897	https://res.cloudinary.com/dtm46mski/raw/upload/v1754134254/bill/ahstngtlrrueq75vax8s.pdf	{"document_type": "BOL", "bl_number": "NYC2201777", "shipper": "JETHING INT LTD", "consignee": "HAYWARD INDUSTRIES, INC.", "port_of_loading": "SHANGHAI", "port_of_discharge": "", "container_numbers": "SLVU4877415, VOLU4543799, BBBB4543799", "flight_or_vessel": "TIMON v.2201E", "product_description": "G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL", "paid_amount": "", "raw_text": "Freight Brokers Global Services, Inc.\\nBILL OF\\n5. DOCUMENT NUMBER\\n5a. B/L NUMBER\\nJETHING INT LTD\\nNYC2201777\\n15 HUANMAO 1 ROAD\\n6. EXPORT REFERENCES\\nZHONGSHAN TORCH DEVELOPMENT ZONE\\n528437 ZHONGSHAN CITY,\\n ZIP CODE\\nGUANGDONG PROVINCE CHINA\\nMISS HELEN HUANG\\n3. CONSIGNED TO\\n7. FORWARDING AGENT (Name and address - references)\\nSO FUN NIGERIA\\nFREIGHT BROKERS GLOBAL SERVICES,INC.\\nC/O DEAN WAREHOUSE SVC. 292\\n1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691\\nKILVERT STREET WARWICK, RI 02886 USA\\nTEL:347-926-7002 FAX:718-327-5318\\nATTN: DIANNE BARBOSA\\n8. POINT (STATE) OF ORIGIN OR FTZ NUMBER\\nTel #401 583 1161\\n4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE (Name and addre4ss)\\n9. DOMESTIC ROUTING/EXPORT INSTRUCTIONS\\nHAYWARD INDUSTRIES, INC. \\nC/O DEAN WAREHOUSE SVC. 292\\nKILVERT STREET WARWICK, RI 02886 USA\\nATTN: DIANNE BARBOSA\\nTel #401 583 1161\\n12. PRE-CARRIAGE BY\\n13. PLACE OR RECEIPT BY PRE-CARRIER\\nSHANGHAI\\n14. EXPORTING CARRIER\\n15. PORT OF LOADING / EXPORT\\n10. LOADING PIER / TERMINAL                 \\nTIMON v.2201E\\nSHANGHAI\\n16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY)\\n17. PLACE OF DELIVERY BY ON-CARRIER\\n11. TYPE OF MOVE\\n11a. CONTAIN\\nHUNGARY\\nHUNGARY\\nCY/CY\\nYES\\n      MARKS AND NUMBERS\\n   NUMBER \\nDESCRIPTION OF COMMODITIES in Schedule B detail\\n      Gross Weight\\n          Meas\\nOF PACKAGES\\n \\n   (Kilos)\\n                   (18)\\n(19)\\n(20)\\n(21)\\n2x40'HQ \\nSHIPPER'S LOAD & COUNT\\n8170.00\\n76.633\\n852 CTNS (IN 36 x PLTS)\\nG1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL\\nSTAR RAPID\\nG1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nG1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL\\nH.S CODE:8421990040\\n\\" FREIGHT COLLECT \\"\\nCONTR #     / SEAL #                                               S/O #\\nSLVU4877415 / D225859/40'HQ  480 CTNS / 3740.000 KGS / 43.181 CBM /SLSNSAS00064 \\nVOLU4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nBBBB4543799 / D225867/40'HQ  372 CTNS / 4430.000 KGS / 33.452 CBM /SLSNSAS00063\\nTOTAL: THREE(40'HQ) CONTAINERS ONLY.\\nSHIPPED \\nTHIS SHIPMENT CONTAINS NO WOOD PACKING MATERIALS.\\n25,JAN\\nTHESE COMMODITIES, TECHNOLOGY, OF SOFTWARE WERE EXPORTED FORM THE US IN ACCORDANCE WITH THE EXPORT ADMINSTRATION ON REGULATIONS.\\nDIVERSION CONTRARY TO U.S. LAW IS PROHIBITED.\\n              FREIGHT RATES, CHARGES, WEIGHTS AND/OR MEASUREMENTS\\nReceived by Carrier for shipment by ocean vessel between port of loading a\\n                 SUBJECT TO CORRECTION\\nPREPAID\\nCOLLECT\\non-carriage to place of delivery, where stated above, the goods as specified \\nin apparent good order and condition unless otherwise stated. The goods to be delivered\\nport of discharge or place of delivery, whichever is applicable, subject always to the exce\\nagree to accepting this Bill of Loading.\\nIN WITNESS WHEREOF three(3) original Bills of Lading have been signed, not otherwis\\nabove, one of which being accomplished the others shall be void.\\nDATED AT                            \\nBY                                  \\n                                          AGENT OF THE MASTER\\nMO.\\nDAY\\nYEAR\\n2. EXPORTER (Principal or seller - licensee and address including ZIP Xode)\\ndischage, and for arragement or  procurement of per-carriage from place of \\nconditions and liberties set out on the revese side hereof, to which the Shipper and/or Co\\n\\nF LADING\\nNERIZED(Vessel Only)\\n NO\\nsurement\\n(22)\\n3\\nON BOARD :\\nN.,2022\\nand port of \\nabove \\n at the above mentioned\\neptions, limitations,\\nse stated \\n    \\nreceipt and \\nonsignee \\n", "container_count": 3, "container_types": ["40ft", "40ft_hc"], "container_type": "40ft", "container_count_20ft": 0, "container_count_40ft": 1, "container_count_40ft_hc": 1, "total_weight_kg": 4430.0, "weight_unit": "kg", "shipment_type": "ocean", "pricing_method": "ocean_container", "calculated_ctn_fee": 450.0, "calculated_service_fee": 225.0, "calculated_total_fee": 675.0, "ocr_confidence_score": 0.8500000000000001, "pricing_calculation_log": {"method": "ocean_container", "container_types": ["40ft", "40ft_hc"], "container_count": 3, "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}}, "validation_result": {"missing_fields": ["port_of_discharge"], "has_critical_missing": false, "confidence_score": 0.8, "needs_revalidation": false, "revalidation_performed": false}, "confidence_breakdown": {"container_detection": 0.9, "weight_detection": 0.8, "shipment_classification": 0.9, "field_validation": 0.8, "overall": 0.8500000000000001}, "extraction_method": "ai"}	JETHING INT LTD	HAYWARD INDUSTRIES, INC.	SHANGHAI		NYC2201777	SLVU4877415, VOLU4543799, BBBB4543799	\N	\N	Pending	2025-08-02 11:31:00.877876+00	2025-08-02 11:31:01.128702+00	\N	\N	ray40	\N	\N	\N	\N	\N	\N	TIMON v.2201E	G1-046480-ST Rev A  DEADFRONT,ENCLOSURE,AQR S3-SOFT TOOL, G1-046481-ST Rev A  DOOR,ENCLOSURE,AQR S3-SOFT TOOL, G1-046482-ST Rev A BASE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046483-ST Rev A HANDLE,ENCLOSURE,AQR S3-SOFT TOOL, G1-046484-ST Rev A COUPLER,HANDLE,ENCLOSURE,AQR S3-SOFT TOOL	not_selected_yet	pending	0	not_applicable	\N	\N	ocean	40ft	3	4430.00	kg	ocean_container	\N	\N	450.00	225.00	0.85	f	\N	\N	\N	{"method": "ocean_container", "rates_used": {"40ft": {"ctn_fee": 200.0, "service_fee": 100.0}, "40ft_hc": {"ctn_fee": 250.0, "service_fee": 125.0}}, "container_count": 3, "container_types": ["40ft", "40ft_hc"]}	2025-08-02 11:31:01.128702+00		0	1	1	\N	\N	\N	0.00
68	Sandy Kong	ray633008@gmail.com	0493245830	https://res.cloudinary.com/dtm46mski/raw/upload/v1754203066/bill/a0p9d9jybfanaxfvyhaw.PDF	{"document_type": "BOL", "shipper": "A Joint Service Agreement", "consignee": "BOHRMANN LOGISTICS GMBH & CO. OHG", "port_of_loading": "", "port_of_discharge": "HAMBURG", "bl_number": "254148256214", "container_numbers": "KEIS2374724", "flight_or_vessel": "MEGA WAVE RIDER", "product_description": "KEIS2374724/20' /EGDGS5468/54 PACKAGES", "raw_text": "BLUELINERS CORP.\\n(2) Shipper/Exporter\\nA Joint Service Agreement\\nWANG TAI CO. LTD\\nV, Enterprise Square\\n38 Wang Chiu Rd\\nKowloon Bay, Hongkong\\nSEA WAYBILL\\nNON-NEGOTIABLE\\n(5) Document No.\\n(6) Export References\\n(3) Consignee(complete name and address)\\nBOHRMANN LOGISTICS GMBH & CO. OHG\\nPARKSTRASSE 1\\n38440 WOLFSBURG GERMANY\\n(7) Forwarding Agent-References\\n(4) Notify Party (complete name and address)\\nWHEELS AG BIELEFELD\\nHERFORDER STRASSE 306\\n33609 BIELEFELD GERMANY\\n(8) Point and Country of Origin (for the Merchant's reference only)\\n(9) Also Notify Party (complete name and address)\\nNOTIABLE\\nHONGKONG\\n(17) Place of Delivery\\nHAMBURG\\n(12) Pre-carriage by\\n(14) Ocean Vessel/Voy. No.\\nMEGA WAVE RIDER\\n245W\\n(16) Port of Discharge\\nHAMBURG\\nThis Sea Waybill is issued at the request and for the convenience of the Merchant, but is nevertheless\\nsubject to the terms and conditions of the Carrier's standard long form Bill of Lading for this trade\\nwhich may be viewed online at [http://www.evergreen-line.com] or a copy obtained from the Carrier\\nor its agents.\\n(10) Onward Inland Routing/Export Instructions (which are contracted separately by\\nMerchants entirely for their own account and risk)\\n(18) Container No. And Seal No.\\nMarks & Nos.\\nCONTAINER NO./SEAL NO.\\n(19) Quantity And\\nKind of Packages\\nParticulars furnished by the Merchant\\n(20) Description of Goods\\nKEIS2374724/20' /EGDGS5468/54 PACKAGES\\nINV NO. 10550578\\nDN NO. 10550578\\nWHEELS 12E (G15F)\\nHAMBURG\\nNO. 1-2\\nWHEELS 5WOG (G15F)\\nHAMBURG\\nNO. 1-2\\nINV NO. 10550578\\nDN NO.\\n10550578\\n(22) TOTAL NUMBER OF\\nCONTAINERS OR PACKAGES\\n(IN WORDS)\\n1 x 20'\\n4 PACKAGE(S)\\nOTIABLE\\nDUNS NUMBER: 455889824\\nPART NAME+QUANTITY\\nBAG FOR CHARGING CABLE\\n1800PCS\\nPART NUMBER 15E 554 812\\nHS CODE 42029200.00\\nPART NAME+QUANTITY\\nWARNING VEST 1200PCS\\nPART NUMBER 7K3 512 568\\n*THE BALANCE OF BILL OF LADING SEE ATTACHED LIST *\\nTOTAL NUMBER OF ATTACHED 1 PAGE\\n\\"OCEAN FREIGHT COLLECT\\"\\nSHIPPER'S LOAD & COUNT\\n25 PACKAGES\\nONE (1) CONTAINER ONLY\\n(24) FREIGHT & CHARGES\\nRevenue Tons\\n(21) Measurement (M\\u00b3)\\nGross Weight (KGS)\\n20.4700 CBM\\n4,616.100 KGS\\nRate\\nPer Prepaid\\nAS\\nARRANGED\\n(23)\\nDeclared Value S\\nMerchant enters actual value of Goods\\nand pays, the applicable ad valorem\\nTariff rate, Carrier's package limitation.\\nshall not apply.\\nCollect\\nNON-NEG ABLE\\n(25) Waybill No.\\n254148256214\\n(26) Service Type/Mode\\nFCL/FCL 0/0\\n(27) Number of Original Waybills\\nNIL (0)\\n(28) Place and Date of Issue\\nKOWLOON BAY, HONGKONG AUG. 22, 2024\\n(33) Laden on Board\\nAUG. 22,2024\\nMEGA WAVE RIDER\\n245W\\nKOWLOON BAY, HONGKONG\\n(29) Prepaid at\\n(31) Exchange Rate\\n(30) Collect at\\nDESTINATION\\n(32) Exchange Rate\\nAs agent for the Carrier and Vessel Provider Blueline Corp.\\ndoing business as \\"Blueline\\"\\nFORM NO. DOC-1-006-02\\n"}	A Joint Service Agreement	BOHRMANN LOGISTICS GMBH & CO. OHG	hong kong	HAMBURG	NYC231	KEIS2374724	200	\N	Invoice Sent	2025-08-03 06:37:47.686434+00	2025-08-03 06:37:47.977959+00	https://res.cloudinary.com/dtm46mski/raw/upload/v1754450532/invoices/a2h5h14piskg2u2rgkl1.pdf	ray8398439	ray100	150	https://pay.dummy.com/link/68?amount=350.00&currency=USD&email=ray633008%40gmail.com&ctn=None&description=Reserve+payment+for+CTN+ray8398439&success=https%3A%2F%2Fyourdomain.com%2Fsuccess&cancel=https%3A%2F%2Fyourdomain.com%2Fcancel&timestamp=20250806112150	\N	\N	\N	\N	MEGA WAVE RIDER	KEIS2374724/20' /EGDGS5468/54 PACKAGES			0		\N	\N	ocean	\N	1	\N	kg	container	\N	\N	150.00	200.00	\N	f	\N	\N	\N	{}	2025-08-03 06:37:47.977959+00		0	0	0	\N	\N	\N	0.00
\.


--
-- Data for Name: customer_balance_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customer_balance_transactions (id, username, transaction_type, amount, reference_type, reference_id, payment_source, description, created_at, created_by) FROM stdin;
1	ray40	credit	10.00	manual_adjustment	\N	\N	test	2025-08-05 10:32:53.271248+00	{"id": 84, "role": "staff", "username": "ray40"}
2	ray40	application	10.00	invoice_application	74	\N	Balance applied to invoice NYC225	2025-08-05 10:33:21.089447+00	{"id": 84, "role": "staff", "username": "ray40"}
3	ray40	credit	10.00	manual_adjustment	\N	\N	test1	2025-08-05 11:28:35.374094+00	{"id": 84, "role": "staff", "username": "ray40"}
4	ray40	application	10.00	invoice_application	73	\N	Balance applied to invoice NYC2201777	2025-08-05 11:29:30.297738+00	{"id": 84, "role": "staff", "username": "ray40"}
5	ray40	debit	100.00	payment_match	74	email	Underpayment debit: Paid $100.0, Invoice $200.0	2025-08-05 11:37:22.67044+00	email_ingestor
6	ray40	credit	235.00	payment_match	73	email	Overpayment credit: Paid $900.0, Invoice $665.0	2025-08-05 11:39:55.519986+00	email_ingestor
7	ray40	credit	125.00	payment_match	71	email	Overpayment credit: Paid $800.0, Invoice $675.0	2025-08-06 02:54:07.571609+00	email_ingestor
8	ray40	credit	600.00	payment_match	72	email	Overpayment credit: Paid $800.0, Invoice $200.0	2025-08-06 02:54:08.703498+00	email_ingestor
9	ray100	debit	266.67	payment_match	70	email	Underpayment debit: Paid $83.33333333333333, Invoice $350.0	2025-08-06 03:03:30.229395+00	email_ingestor
10	ray40	debit	258.33	payment_match	69	email	Underpayment debit: Paid $416.6666666666667, Invoice $675.0	2025-08-06 03:04:22.363592+00	email_ingestor
11	ray100	debit	150.00	payment_match	68	email	Underpayment debit: Paid $200.0, Invoice $350.0	2025-08-06 03:24:25.790585+00	email_ingestor
13	ray100	debit	216.67	payment_match	67	email	Underpayment debit: Paid $133.33333333333334, Invoice $350.0	2025-08-06 03:26:51.717376+00	email_ingestor
15	ray40	debit	325.00	payment_match	66	email	Underpayment debit: Paid $350.0, Invoice $675.0	2025-08-06 03:47:03.586006+00	email_ingestor
17	ray40	credit	350.00	payment_match	65	email	Overpayment credit: Paid $700.0, Invoice $350.0	2025-08-06 04:06:59.080335+00	email_ingestor
18	ray40	credit	25.00	payment_match	64	email	Overpayment credit: Paid $700.0, Invoice $675.0	2025-08-06 04:15:14.608056+00	email_ingestor
19	ray40	credit	0.00	bill_of_lading	64	email	Payment marked as processed for BL 64	2025-08-06 04:15:15.029928+00	email_ingestor
20	ray40	credit	500.00	payment_match	63	email	Overpayment credit: Paid $850.0, Invoice $350.0	2025-08-06 04:23:02.527523+00	email_ingestor
21	ray40	credit	0.00	bill_of_lading	63	email	Payment marked as processed for BL 63	2025-08-06 04:23:02.963602+00	email_ingestor
22	ray40	credit	175.00	payment_match	62	email	Overpayment credit: Paid $850.0, Invoice $675.0	2025-08-06 04:23:03.675308+00	email_ingestor
23	ray40	credit	0.00	bill_of_lading	62	email	Payment marked as processed for BL 62	2025-08-06 04:23:04.099637+00	email_ingestor
26	admin	credit	0.00	bill_of_lading	999999	test	Payment marked as processed for BL 999999	2025-08-06 05:42:55.483813+00	test_script
27	admin	credit	20.00	bill_of_lading	999999	test	Payment processing for BL 999999	2025-08-06 05:42:56.660941+00	test_script
28	admin	credit	0.00	bill_of_lading	999999	test	Payment marked as processed for BL 999999	2025-08-06 05:57:33.603591+00	test_script
29	admin	credit	20.00	bill_of_lading	999999	test	Payment processing for BL 999999	2025-08-06 05:57:35.673605+00	test_script
30	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:16:14.082617+00	whatsapp_chat
31	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:17:09.548818+00	whatsapp_chat
32	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:20:03.851937+00	whatsapp_chat
33	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:22:04.116554+00	whatsapp_chat
34	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:22:05.353974+00	whatsapp_chat
35	admin	credit	0.00	bill_of_lading	999999	test	Payment marked as processed for BL 999999	2025-08-06 06:26:40.804113+00	test_script
36	admin	credit	20.00	bill_of_lading	999999	test	Payment processing for BL 999999	2025-08-06 06:26:42.084855+00	test_script
37	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:32:54.931805+00	whatsapp_chat
38	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:32:56.166914+00	whatsapp_chat
39	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:34:00.09774+00	whatsapp_chat
40	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:34:01.381953+00	whatsapp_chat
41	admin	credit	0.00	bill_of_lading	999999	test	Payment marked as processed for BL 999999	2025-08-06 06:37:10.082794+00	test_script
42	admin	credit	20.00	bill_of_lading	999999	test	Payment processing for BL 999999	2025-08-06 06:37:11.522762+00	test_script
43	admin	credit	0.00	bill_of_lading	999999	test	Payment marked as processed for BL 999999	2025-08-06 06:39:37.132872+00	test_script
44	admin	credit	20.00	bill_of_lading	999999	test	Payment processing for BL 999999	2025-08-06 06:39:38.405064+00	test_script
45	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:46:43.956099+00	whatsapp_chat
46	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:46:45.154591+00	whatsapp_chat
47	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:47:26.065465+00	whatsapp_chat
48	admin	credit	0.00	bill_of_lading	\N	whatsapp	Payment marked as processed for BL undefined	2025-08-06 06:47:27.995812+00	whatsapp_chat
49	ray100	credit	0.00	bill_of_lading	58	whatsapp	Payment marked as processed for BL 58	2025-08-06 06:54:29.718917+00	whatsapp_chat
50	ray100	credit	128.05	bill_of_lading	58	whatsapp	Payment processing for BL 58	2025-08-06 06:54:31.02203+00	whatsapp_chat
51	ray40	credit	0.00	bill_of_lading	59	whatsapp	Payment marked as processed for BL 59	2025-08-06 06:54:32.003249+00	whatsapp_chat
52	ray40	credit	246.95	bill_of_lading	59	whatsapp	Payment processing for BL 59	2025-08-06 06:54:33.290856+00	whatsapp_chat
53	ray100	credit	0.00	bill_of_lading	57	whatsapp	Payment marked as processed for BL 57	2025-08-06 07:11:32.914147+00	whatsapp_chat
54	ray100	credit	0.00	bill_of_lading	57	whatsapp	Payment processing for BL 57	2025-08-06 07:11:34.093827+00	whatsapp_chat
55	ray100	credit	1050.00	bill_of_lading	57	whatsapp	Payment processing for BL 57	2025-08-06 07:11:35.254284+00	whatsapp_chat
56	ray40	credit	0.00	bill_of_lading	55	whatsapp	Payment marked as processed for BL 55	2025-08-06 07:13:48.874261+00	whatsapp_chat
57	ray40	credit	0.00	bill_of_lading	55	whatsapp	Payment processing for BL 55	2025-08-06 07:13:50.0732+00	whatsapp_chat
58	ray100	credit	0.00	bill_of_lading	56	whatsapp	Payment marked as processed for BL 56	2025-08-06 07:13:50.992285+00	whatsapp_chat
59	ray100	credit	0.00	bill_of_lading	56	whatsapp	Payment processing for BL 56	2025-08-06 07:13:52.213215+00	whatsapp_chat
60	ray40	credit	725.00	bill_of_lading	55	whatsapp	Payment processing for BL 55	2025-08-06 07:13:53.414241+00	whatsapp_chat
61	ray100	credit	725.00	bill_of_lading	56	whatsapp	Payment processing for BL 56	2025-08-06 07:13:54.613196+00	whatsapp_chat
62	ray40	credit	0.00	bill_of_lading	54	whatsapp	Payment marked as processed for BL 54	2025-08-06 07:23:10.071422+00	whatsapp_chat
63	ray40	credit	0.00	bill_of_lading	54	whatsapp	Payment processing for BL 54	2025-08-06 07:23:11.270389+00	whatsapp_chat
64	ray40	credit	0.00	bill_of_lading	53	whatsapp	Payment marked as processed for BL 53	2025-08-06 07:23:12.170363+00	whatsapp_chat
65	ray40	credit	0.00	bill_of_lading	53	whatsapp	Payment processing for BL 53	2025-08-06 07:23:13.370273+00	whatsapp_chat
66	ray40	credit	650.00	bill_of_lading	54	whatsapp	Payment processing for BL 54	2025-08-06 07:23:14.591268+00	whatsapp_chat
67	ray40	credit	650.00	bill_of_lading	54	whatsapp	Overpayment credit: Paid $2000, Invoice $1350	2025-08-06 07:23:14.892077+00	whatsapp_chat
68	ray40	credit	0.00	bill_of_lading	51	whatsapp	Payment marked as processed for BL 51	2025-08-06 07:25:35.603137+00	whatsapp_chat
69	ray40	credit	0.00	bill_of_lading	51	whatsapp	Payment processing for BL 51	2025-08-06 07:25:37.499142+00	whatsapp_chat
70	ray40	credit	0.00	bill_of_lading	52	whatsapp	Payment marked as processed for BL 52	2025-08-06 07:25:38.929185+00	whatsapp_chat
71	ray40	credit	0.00	bill_of_lading	52	whatsapp	Payment processing for BL 52	2025-08-06 07:25:40.831104+00	whatsapp_chat
72	ray40	credit	650.00	bill_of_lading	51	whatsapp	Payment processing for BL 51	2025-08-06 07:25:42.770178+00	whatsapp_chat
73	ray40	credit	650.00	bill_of_lading	51	whatsapp	Overpayment credit: Paid $2000, Invoice $1350	2025-08-06 07:25:44.454665+00	whatsapp_chat
\.


--
-- Data for Name: customer_balances; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customer_balances (id, username, balance_amount, last_updated, created_at, notes, is_active) FROM stdin;
2	eee	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
3	fff	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
4	vvv	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
5	www	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
6	ee	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
7	aaaa	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
8	ttt	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
9	iii	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
10	ppp	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
11	ooo	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
12	lll	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
13	hhh	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
14	bbbb	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
15	bbbbb	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
16	sandy	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
17	ffff	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
18	sandykong	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
19	cccc	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
20	ggggg	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
21	qqqqq	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
22	sssss	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
23	kkkkk	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
24	kkkk	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
25	wong	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
26	hhhhh	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
27	ray ray	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
28	yes	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
29	ray1	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
30	ray3	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
31	ray2	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
32	ray5	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
33	ray6	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
34	ray8	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
35	xxx	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
36	ray7	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
37	abcabc	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
38	ray9	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
39	ray10	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
40	ray12	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
41	ray13	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
42	ray14	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
43	ray15	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
44	ray17	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
45	ray18	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
46	ray20	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
47	ray22	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
48	ray23	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
49	ray24	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
50	ray25	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
51	sandy2	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
52	ray30	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
53	alicevw	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
54	windrider824	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
55	sandy3	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
56	ykrw	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
57	ray33	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
58	ray35	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
59	ray36	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
60	ray85	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
61	ray42	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
62	ray47	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
63	ray46	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
64	ray60	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
65	ray61	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
66	ray71	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
67	ray82	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
68	ray83	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
69	ray90	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
70	ray84	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
71	ray41	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
72	ray81	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
73	ray110	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
74	terryng	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
75	john	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
76	ray91	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
77	ray112	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
79	ray401	0.00	2025-08-04 08:46:19.215297+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
78	ray100	1269.71	2025-08-06 07:13:54.305329+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
1	admin	100.00	2025-08-06 06:39:38.077935+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
80	ray40	3598.62	2025-08-06 07:25:42.282298+00	2025-08-04 08:46:19.215297+00	Initialized for existing user	t
\.


--
-- Data for Name: customer_email_replies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customer_email_replies (id, customer_email_id, sender, body, created_at, is_draft, sent_at, sent_via, confidence_score, confidence_reasoning, auto_send_recommended, auto_sent, auto_sent_at) FROM stdin;
715	9	openai_draft	Thank you for your payment. We have received your payment and it is being processed. If you need the invoice and container number for BL NYC2201666, please find them attached.	2025-08-01 02:32:15.53837	f	2025-08-01 02:32:15.53837	\N	0.95	\N	f	f	\N
716	10	openai_draft	Thank you for reaching out. To assist you further, could you please provide more details or clarify your inquiry regarding the BL NYC2201666? This will help us provide you with the accurate information you need. Looking forward to your response.	2025-08-01 02:32:27.876777	f	2025-08-01 02:32:27.876777	\N	0.85	\N	f	f	\N
717	11	openai_draft	Dear customer, \n\nHere are the details for BL NYC220: \n\nCTN Number: RAY001122 \nInvoice Link: [Click here to view the invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf) \n\nIf you have any further questions or need assistance, feel free to reach out. \n\nThank you! \nIQSTrade Support Team	2025-08-01 02:53:45.605172	f	2025-08-01 02:53:45.605172	\N	0.95	\N	f	f	\N
718	12	openai_draft	Dear customer, \n\nHere are the details for BL NYC220: \n\nCTN Number: RAY001122 \nInvoice Link: [Click here to download the invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf) \n\nIf you have any further questions or need assistance, feel free to reach out. \n\nThank you! \nIQSTrade Support Team	2025-08-01 03:06:55.953064	f	\N	\N	0.95	\N	f	f	\N
719	13	openai_draft	Dear customer, \n\nHere are the details for BL NYC220: \n\nCTN Number: RAY001122 \nInvoice Link: [Click here to view the invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf) \n\nIf you have any further questions or need assistance, feel free to reach out. \n\nThank you! \nIQSTrade Support Team	2025-08-01 03:07:16.752785	f	\N	\N	0.95	\N	f	f	\N
720	14	openai_draft	Dear customer, \n\nRegarding your inquiries: \n\nPayment Methods: We accept Bank Transfer, PayPal, and Credit Card. \n\nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 3 to 5 business days after your payment has been confirmed. \n\nFees: The CTN Fee is $100 per container, and the Service Fee is $100 per container, totaling $200 per container. \n\nIf you have any further questions or need assistance, feel free to reply to this email. \n\nThank you! \nIQSTrade Support Team	2025-08-01 03:09:25.711956	f	\N	\N	0.95	\N	f	f	\N
721	17	openai_draft	Subject: Payment Status Update\n\nDear Customer,\n\nRegarding your recent payment, we have received $420 for B/L NYC220. The total paid amount for this B/L is $700. You can view the invoice details here: [Invoice Link].\n\nThank you for your payment.\n\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 001-123: Not found in our system	2025-08-01 03:15:54.746832	t	\N	\N	0.7	\N	f	f	\N
722	18	openai_draft	Subject: Payment Status Update\n\nDear Customer,\n\nRegarding your recent payment, we have received $420 for B/L NYC220. The total amount paid for this B/L is $700. You can view the invoice details by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf).\n\nThank you for your payment.\n\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 001-123: Not found in our system	2025-08-01 03:20:07.278823	t	\N	\N	0.7	\N	f	f	\N
723	19	openai_draft	Subject: Payment Status\n\nDear Customer,\n\nThank you for your payment of $700 for B/L NYC220. The payment has been received and the status of the invoice is 'Invoice Sent'. You can view the invoice details by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf).\n\nIf you have any further inquiries regarding your payment, feel free to reach out.\n\nThank you,\nIQSTrade Support Team	2025-08-01 03:21:10.124077	t	\N	\N	0.95	\N	f	f	\N
724	20	openai_draft	Subject: Payment Status\n\nPayment for B/L NYC220 Amount: $700 Ref: TEST987\n\nStatus: Invoice Sent\n\nInvoice Link: [Click here to view the invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf)	2025-08-01 03:31:36.13494	t	\N	\N	0.95	\N	f	f	\N
725	21	openai_draft	Subject: Payment Status\n\nPayment for B/L NYC220 Amount: $720 Ref: TEST987\n\nStatus: Awaiting Bank In\n\n---\n\nSubject: Payment Receipt\n\nPayment for B/L NYC220 Amount: $720 Ref: TEST987\n\nInvoice Link: [Click here to view invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf)	2025-08-01 04:04:41.59066	t	\N	\N	0.95	\N	f	f	\N
726	22	openai_draft	Subject: Payment Status\n\nDear Customer,\n\nRegarding your payment for B/L NYC220, we have received an amount of $680. The status of B/L NYC220 is currently 'Awaiting Bank In'. You can track the payment status through the following link: https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf\n\nThank you for your payment.\n\nIQSTrade Support Team	2025-08-01 04:07:22.918615	t	\N	\N	0.95	\N	f	f	\N
727	23	openai_draft	Dear customer, \n\nThank you for your email. \n\nRegarding your payment receipt, we have received a payment of $720.0. Please find the invoice link for the valid Bill of Lading (BL) NYC220 here: [Invoice Link]. \n\nIf you have any general enquiries or need further assistance, feel free to reach out. \n\nThank you! \nIQSTrade Support Team\n\nAdditional BL Information:\nBL 987-654321: Not found in our system\n\n💰 OVERPAYMENT: We have received your payment of $720.00, but the invoice amount is $700.00. We will contact you regarding the excess payment of $20.00.	2025-08-01 06:05:47.007255	t	\N	\N	0.7	\N	f	f	\N
728	24	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team	2025-08-01 07:02:14.655503	t	\N	\N	0.95	\N	f	f	\N
729	25	openai_draft	Subject: Payment Confirmation - NYC221\n\nDear customer,\n\nThank you for your email regarding the payment confirmation for BL NYC221. We have received the attached file(s) and are currently processing your request.\n\nPlease note that the total fees for BL NYC221 are as follows:\n- CTN Fee: $450.00\n- Service Fee: $225.00\n\nYou have not made any payment yet. Once the payment is received, we will issue the payment receipt accordingly.\n\nIf you have any further questions or need assistance, feel free to reply to this email.\n\nThank you!\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011501: Not found in our system	2025-08-01 07:02:32.294945	t	\N	\N	0.7	\N	f	f	\N
730	26	openai_draft	Subject: Payment for NYC223\n\nDear customer,\n\nThank you for your email regarding the payment for BL NYC223. We have received the attached file(s) and will process your request accordingly.\n\nFor payment receipt, please note that the current status of BL NYC223 is 'Awaiting Bank In'. Once the payment is confirmed, we will issue the receipt. Please ensure the payment is made for the correct amount.\n\nIf you have any general enquiries or need further assistance, feel free to reply to this email.\n\nThank you!\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011501: Not found in our system	2025-08-01 07:02:52.482383	t	\N	\N	0.7	\N	f	f	\N
731	27	openai_draft	Dear customer, Our current fee structure for the NYC224 shipment is as follows: - CTN Fee: $100 per container - Service Fee: $100 per container This amounts to a total of $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. If you have any further questions or need assistance, feel free to reply to this WhatsApp message. Thank you! IQSTrade Support Team	2025-08-01 07:03:02.4803	t	\N	\N	0.95	\N	f	f	\N
732	28	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team	2025-08-01 07:03:11.835829	t	\N	\N	0.95	\N	f	f	\N
733	29	openai_draft	Dear customer, We have received your email regarding the payment receipt for BL NYC225. Unfortunately, we did not receive any payment for this Bill of Lading. If you have any further questions or need assistance with payment methods, fees, or any other inquiries, please feel free to reach out to us. Thank you! IQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011501: Not found in our system	2025-08-01 07:03:33.065929	t	\N	\N	0.7	\N	f	f	\N
734	30	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team	2025-08-01 07:03:42.46038	t	\N	\N	0.95	\N	f	f	\N
735	31	openai_draft	Dear customer, Our records show that the payment for BL NYC221 is still pending. Please proceed with the payment to the following link: https://res.cloudinary.com/dtm46mski/raw/upload/v1754028750/invoices/ljsjlp4jed7zq04oal7b.pdf. If you have any general enquiries or need further assistance, feel free to reach out. Thank you! IQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011501: Not found in our system	2025-08-01 07:04:01.001204	t	\N	\N	0.7	\N	f	f	\N
736	32	openai_draft	Subject: Payment Confirmation - NYC221\n\nDear customer,\n\nThank you for your email regarding the payment confirmation for BL NYC221. We have received the attached file(s) and are currently processing your request.\n\nPlease note that the total fees for BL NYC221 are as follows:\n- CTN Fee: $450.00\n- Service Fee: $225.00\n\nTo complete the payment process, please proceed with the bank transfer using the following details:\nBank Transfer Instructions: [Provide bank transfer details here]\n\nOnce the payment has been confirmed, we will issue the receipt accordingly.\n\nIf you have any further questions or require assistance, feel free to reply to this email.\n\nThank you!\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011518: Not found in our system	2025-08-01 07:19:36.605934	t	\N	\N	0.7	\N	f	f	\N
737	33	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team	2025-08-01 07:29:26.201618	t	\N	\N	0.95	\N	f	f	\N
738	34	openai_draft	Subject: Payment Confirmation - NYC221\n\nDear customer,\n\nThank you for your email regarding the payment confirmation for BL NYC221. We have received your attached file(s). Please note that the paid amount is currently at $0.0, and the status of BL NYC221 is 'Awaiting Bank In'.\n\nIf you have any further questions or need assistance with payment methods, fees, or invoice copies, please feel free to reach out to us.\n\nThank you!\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011528: Not found in our system	2025-08-01 07:29:47.701732	t	\N	\N	0.7	\N	f	f	\N
739	35	openai_draft	Subject: Payment for NYC223\n\nDear customer,\n\nThank you for your email regarding the payment for BL NYC223. As the paid amount is currently showing as 0.0, we kindly remind you to proceed with the payment to complete the transaction. You can make the payment using one of the following methods: Bank Transfer, Allinpay, or Stripe. Once the payment is confirmed, please upload the bank transfer receipt by replying to this WhatsApp message with the receipt attached.\n\nPlease find the invoice link for BL NYC223 here: [Invoice Link]\n\nIf you have any further questions or need assistance, feel free to reach out to us.\n\nThank you!\nIQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011528: Not found in our system	2025-08-01 07:30:10.768141	t	\N	\N	0.7	\N	f	f	\N
740	36	openai_draft	Dear customer, Our current fee structure for the NYC224 shipment is as follows: - CTN Fee: $100 per container - Service Fee: $100 per container This amounts to a total of $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. If you have any further questions or need assistance, feel free to reply to this WhatsApp message. Thank you! IQSTrade Support Team	2025-08-01 07:30:19.344961	t	\N	\N	0.95	\N	f	f	\N
741	37	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out by replying to this WhatsApp message. Thank you! IQSTrade Support Team	2025-08-01 07:30:27.690681	t	\N	\N	0.95	\N	f	f	\N
742	38	openai_draft	Dear customer, Unfortunately, the Bill of Lading (B/L) with the number NYC225 is invalid and cannot be processed for payment receipt. If you have any general enquiries or need assistance with valid documents, feel free to reach out. Thank you! IQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011528: Not found in our system	2025-08-01 07:30:47.195722	t	\N	\N	0.7	\N	f	f	\N
743	39	openai_draft	Dear customer, Our records show that the payment for BL NYC221 is still pending. Please proceed with the payment to the following link: [Invoice Link]. If you have any general enquiries or need further assistance, feel free to reach out. Thank you! IQSTrade Support Team\n\nAdditional BL Information:\nBL 202508011528: Not found in our system	2025-08-01 07:31:07.280873	t	\N	\N	0.7	\N	f	f	\N
744	40	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team	2025-08-01 07:31:14.649374	t	\N	\N	0.95	\N	f	f	\N
745	41	openai_draft	Hello,\n\nThe following BL numbers could not be found in our system: 202508011641. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-01 08:44:33.373193	t	\N	\N	0.9000000000000001	{"final_score": 0.9000000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 160, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
746	42	openai_draft	Hello,\n\nThe following BL numbers could not be found in our system: 202508011647. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-01 08:48:53.650811	t	\N	\N	0.9000000000000001	{"final_score": 0.9000000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 160, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
747	43	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC221: Payment record found.\n\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $25.00.\n\nThe following BL numbers could not be found in our system: 202508011651, 20250801. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-01 08:53:47.724495	t	\N	\N	0.9000000000000001	{"final_score": 0.9000000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 382, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
748	44	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC221: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $25.00.\nPayment status:\n  - BL NYC221: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-01 09:00:53.334546	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 335, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
749	45	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC220: Payment record found.\n⚠️ UNDERPAYMENT: We have received your payment of $600.00, but the invoice amount is $700.00. There is an outstanding balance of $100.00.\nPayment status:\n  - BL NYC220: Total Fee: $700.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-01 09:04:01.421269	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 321, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
750	46	openai_draft	Dear customer, \n\nThank you for your email. \n\nRegarding your payment receipt, we have received a payment of $700.0. Please find the invoice link for BL NYC220 here: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf). \n\nIf you have any general enquiries or need further assistance, feel free to reply to this message. \n\nThank you! \nIQSTrade Support Team\n\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\n\nBest regards,\nIQS Trade Team	2025-08-01 09:25:54.214312	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 521, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
751	48	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC220: Payment record found.\n\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\n\nBest regards,\nIQS Trade Team	2025-08-01 09:52:46.229294	t	\N	\N	0.7500000000000001	{"final_score": 0.7500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 176, "has_action_items": false, "has_contact_info": false, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": false, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	f	f	\N
752	49	openai_draft	Dear customer, \nRegarding your inquiries: \nPayment Method: We accept Bank Transfer, Allinpay, and Stripe. Please choose the most convenient option for you. \nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used. \nFee Inquiry: Our current fee structure for CTN processing is as follows: CTN Fee - $100 per container, Service Fee - $100 per container, totaling $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. \nIf you have any further questions or need assistance, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-01 09:53:03.618077	t	\N	\N	0.9500000000000002	{"final_score": 0.9500000000000002, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 789, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 4, "low_confidence_indicators": 0}	t	f	\N
753	50	openai_draft	Dear customer, \nRegarding your inquiries: \nPayment Methods: We accept Bank Transfer, Allinpay, and Stripe. Please choose the most convenient option for you. Instructions will be provided when you generate a payment link. \nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time may vary depending on the payment method used. \nFees: Our current fee structure for CTN processing is as follows: CTN Fee - $100 per container, Service Fee - $100 per container, totaling $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. \nIf you have any further questions or need assistance, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-01 10:09:15.34825	t	\N	\N	0.9500000000000002	{"final_score": 0.9500000000000002, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 847, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 4, "low_confidence_indicators": 0}	t	f	\N
756	49	support@iqstrade.com	Dear customer, \nRegarding your inquiries: \nPayment Method: We accept Bank Transfer, Allinpay, and Stripe. Please choose the most convenient option for you. \nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used. \nFee Inquiry: Our current fee structure for CTN processing is as follows: CTN Fee - $100 per container, Service Fee - $100 per container, totaling $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. \nIf you have any further questions or need assistance, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-01 18:39:47.090596	f	\N	\N	\N	\N	f	t	\N
757	48	support@iqstrade.com	Hello,\nPayment(s) found:\n  - For BL NYC220: Payment record found.\n\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\n\nBest regards,\nIQS Trade Team	2025-08-01 18:42:13.84946	f	\N	\N	\N	\N	f	t	\N
758	51	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-01 10:45:30.570829	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 275, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
759	52	openai_draft	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-01 10:48:51.400683	t	\N	\N	0.7	{"final_score": 0.7, "bl_numbers_found": false, "response_quality": {"has_greeting": false, "response_length": 53, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": false, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	f	f	\N
760	53	openai_draft	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-01 10:53:42.183562	t	\N	\N	0.7	{"final_score": 0.7, "bl_numbers_found": false, "response_quality": {"has_greeting": false, "response_length": 53, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": false, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	f	f	\N
761	54	openai_draft	Dear customer, \n\nThank you for your email. \n\nRegarding your payment receipt, we have received a payment of $700.0. Please find the invoice link for BL NYC220 attached: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf). \n\nIf you have any general enquiries or need further assistance, feel free to reply to this email. \n\nThank you! \nIQSTrade Support Team\n\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\n\nBest regards,\nIQS Trade Team	2025-08-01 10:56:05.856586	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 523, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
762	55	openai_draft	Dear customer, \n\nThank you for your email. \n\nRegarding your payment receipt, we have received a payment of $700.0. Please find the invoice link for BL NYC220 attached: [Invoice Link]. Kindly ensure the payment details are accurate. \n\nIf you have any general enquiries or need further assistance, feel free to reply to this message. \n\nThank you! \nIQSTrade Support Team\n\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\n\nBest regards,\nIQS Trade Team	2025-08-01 11:06:06.667836	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 478, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
763	56	openai_draft	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-01 11:06:33.692095	t	\N	\N	0.7	{"final_score": 0.7, "bl_numbers_found": false, "response_quality": {"has_greeting": false, "response_length": 53, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": false, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	f	f	\N
764	56	support@iqstrade.com	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-01 19:09:00.746312	f	\N	\N	\N	\N	f	t	\N
765	57	openai_draft	Hello,\nThe following BL numbers could not be found in our system: 460153, ce54356, bb713668. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-02 08:45:07.165346	t	\N	\N	0.9500000000000001	{"final_score": 0.9500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 171, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
766	58	openai_draft	Hi Will, Thank you for reaching out. If you have any questions or need assistance with your shipment, feel free to contact us. We look forward to supporting you in your logistics needs. Ship well! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-02 09:36:40.528088	t	\N	\N	0.9	{"final_score": 0.9, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 247, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
767	59	openai_draft	Dear customer, \nRegarding your inquiries: \nPayment Method: We accept Bank Transfer, Allinpay, and Stripe. Instructions will be provided when you generate a payment link. \nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. \nFee Inquiry: Our current fee structure is as follows: CTN Fee - $100 per container, Service Fee - $100 per container, totaling $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. \nIf you have any further questions or need assistance, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-02 10:40:54.9906	t	\N	\N	0.9500000000000002	{"final_score": 0.9500000000000002, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 722, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 4, "low_confidence_indicators": 0}	t	f	\N
768	59	support@iqstrade.com	Dear customer, \nRegarding your inquiries: \nPayment Method: We accept Bank Transfer, Allinpay, and Stripe. Instructions will be provided when you generate a payment link. \nCTN Processing Time: The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. \nFee Inquiry: Our current fee structure is as follows: CTN Fee - $100 per container, Service Fee - $100 per container, totaling $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. \nIf you have any further questions or need assistance, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-02 10:46:15.584636	f	\N	\N	\N	\N	f	t	\N
769	56	support@iqstrade.com	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-02 10:47:44.286841	f	\N	\N	\N	\N	f	t	\N
770	60	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC221: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $25.00.\nPayment status:\n  - BL NYC221: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nThe following BL numbers could not be found in our system: ray6330088. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-02 10:50:42.947582	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 456, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
771	61	openai_draft	Subject: Payment Status\nDear Customer,\nThank you for your payment of $600 for B/L NYC220. The payment has been received and processed successfully.\nPayment Details:\n- CTN Fee: $300\n- Service Fee: $400\nYou can view the invoice for B/L NYC220 by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf)\nIf you have any further inquiries regarding your payment, feel free to reach out.\nThank you,\nIQSTrade Support Team\n⚠️ UNDERPAYMENT: We have received your payment of $600.00, but the invoice amount is $700.00. There is an outstanding balance of $100.00.\nBest regards,\nIQS Trade Team	2025-08-02 10:53:53.013097	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 667, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
772	62	openai_draft	Subject: Payment Status\nPayment for B/L NYC220 has been received. Amount: $700. Payment Ref: TEST987\nValid BLs:\n- Container: RAY001122\n- Invoice Link: [Click here to view invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf)\n- CTN Fee: $300\n- Service Fee: $400\n- Status: Invoice Sent\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\nBest regards,\nIQS Trade Team	2025-08-02 10:56:47.168201	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 442, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
773	62	support@iqstrade.com	Subject: Payment Status\nPayment for B/L NYC220 has been received. Amount: $700. Payment Ref: TEST987\nValid BLs:\n- Container: RAY001122\n- Invoice Link: [Click here to view invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf)\n- CTN Fee: $300\n- Service Fee: $400\n- Status: Invoice Sent\n✅ PAYMENT MATCH: Your payment of $700.00 matches the invoice amount of $700.00.\nBest regards,\nIQS Trade Team	2025-08-02 11:22:49.720058	f	2025-08-02 11:22:49.720063	email	\N	\N	f	t	\N
774	63	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC220: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $800.00, but the invoice amount is $700.00. We will contact you regarding the excess payment of $100.00.\nPayment status:\n  - BL NYC220: Total Fee: $700.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-02 11:33:34.517295	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 336, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
784	73	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC226: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $925.00.\nPayment status:\n  - BL NYC226: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 02:51:40.394566	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 454, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
775	64	openai_draft	Dear customer, \n\nThank you for your email. \n\nRegarding your payment receipt, we have received a payment of $800.0. Please find the invoice link for BL NYC220 attached: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754016348/invoices/kmonwjjghirqm3p68qfd.pdf). \n\nIf you have any general enquiries or need further assistance, feel free to reach out. \n\nThank you! \nIQSTrade Support Team\n\n💰 OVERPAYMENT: We have received your payment of $800.00, but the invoice amount is $700.00. We will contact you regarding the excess payment of $100.00.\n\nBest regards,\nIQS Trade Team	2025-08-02 11:36:25.511939	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 586, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
776	65	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC221: Payment record found.\n  - For BL NYC220: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $1375.00. We will contact you regarding the excess payment of $225.00.\nPayment status:\n  - BL NYC221: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\n  - BL NYC220: Total Fee: $700.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-02 11:40:08.88866	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 452, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
777	66	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC220: Payment record found.\n⚠️ UNDERPAYMENT: We have received your payment of $600.00, but the invoice amount is $700.00. There is an outstanding balance of $100.00.\nPayment status:\n  - BL NYC220: Total Fee: $700.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-02 12:46:51.634928	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 321, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
778	67	openai_draft	Could not process email.\nBest regards,\nIQS Trade Team	2025-08-03 06:18:18.378971	t	\N	\N	0.7	{"final_score": 0.7, "bl_numbers_found": false, "response_quality": {"has_greeting": false, "response_length": 53, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": false, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	f	f	\N
779	68	openai_draft	Subject: Payment Status\nDear Customer,\nThank you for your payment of $100 for B/L NYC225. The payment status for this Bill of Lading is as follows:\n- CTN Fee: $100\n- Service Fee: $100\nYou can view the invoice details by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754390000/invoices/pi2esxbkb7t3v4swpt47.pdf)\nIf you have any further questions or need assistance, feel free to reach out to us.\nThank you!\nIQSTrade Support Team\n⚠️ UNDERPAYMENT: We have received your payment of $100.00, but the invoice amount is $200.00. There is an outstanding balance of $100.00.\nBest regards,\nIQS Trade Team	2025-08-05 11:37:21.40485	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 645, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
780	69	openai_draft	Subject: Payment Status\nDear Customer,\nWe have received your payment for B/L NYC226 in the amount of $900. The payment status for this Bill of Lading is as follows:\n- CTN Fee: $450\n- Service Fee: $225\nYou can view the invoice for this transaction by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf)\nIf you have any further questions or need assistance, feel free to reply to this email.\nThank you,\nIQSTrade Support Team\n💰 OVERPAYMENT: We have received your payment of $900.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $225.00.\nBest regards,\nIQS Trade Team	2025-08-05 11:39:54.281645	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 694, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
781	70	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC226: Payment record found.\n⚠️ UNDERPAYMENT: We have received your payment of $665.00, but the invoice amount is $675.00. There is an outstanding balance of $10.00.\nPayment status:\n  - BL NYC226: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-05 11:41:56.661322	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 320, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
782	71	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC226: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $925.00.\nPayment status:\n  - BL NYC226: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nBest regards,\nIQS Trade Team	2025-08-06 02:06:46.208965	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 337, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
783	72	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC226: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $925.00.\nPayment status:\n  - BL NYC226: Total Fee: $675.00, Paid: $0.00, Status: Awaiting Bank In\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 02:32:05.079474	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 454, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
785	74	openai_draft	Subject: Payment Status\nDear customer,\nThank you for your payment of $1600 for B/L NYC227, NYC228. The payment status for these Bill of Ladings is as follows:\n- B/L NYC227: Invoice Sent\n- B/L NYC228: Invoice Sent\nIf you have any further questions or need assistance, feel free to reply to this email.\nThank you!\nIQSTrade Support Team\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $875.00. We will contact you regarding the excess payment of $725.00.\nBest regards,\nIQS Trade Team	2025-08-06 02:54:06.386738	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 516, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
786	75	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC229: Payment record found.\n\n⚠️ UNDERPAYMENT: We have received your payment of $250.00, but the invoice amount is $350.00. There is an outstanding balance of $100.00.\n\nThe following BL numbers could not be found in our system: NYC999, EST987. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-06 03:03:28.629929	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 360, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
787	76	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC230: Payment record found.\n\n💰 OVERPAYMENT: We have received your payment of $1250.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $575.00.\n\nThe following BL numbers could not be found in our system: NYC999, EST987. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-06 03:04:20.604304	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 376, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
788	77	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC230: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $1250.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $575.00.\nPayment status:\n  - BL NYC230: Total Fee: $675.00, Paid: $0.00, Status: Invoice Sent\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 03:08:14.965921	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 450, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
789	78	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC231: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $400.00, but the invoice amount is $350.00. We will contact you regarding the excess payment of $50.00.\nPayment status:\n  - BL NYC231: Total Fee: $350.00, Paid: $0.00, Status: Invoice Sent\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 03:24:23.808282	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 448, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
790	79	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC232: Payment record found.\n\n💰 OVERPAYMENT: We have received your payment of $400.00, but the invoice amount is $350.00. We will contact you regarding the excess payment of $50.00.\n\nThe following BL numbers could not be found in our system: EST987, NYC999. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-06 03:26:50.00059	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 374, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
791	80	openai_draft	Subject: 230\nPayment for B/L NYC230 Amount: $1600 Ref: TEST987\nPayment Receipt:\n- B/L: NYC230\n- Container Number: HPF908350\n- Invoice Link: [Click here to view invoice](https://res.cloudinary.com/dtm46mski/raw/upload/v1754449240/invoices/czk1i0b6dxgvnvqrswef.pdf)\nPayment Status:\n- Paid Amount: $1600\nThank you!\n💰 OVERPAYMENT: We have received your payment of $1600.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $925.00.\nBest regards,\nIQS Trade Team	2025-08-06 03:34:26.082914	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 494, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
792	80	openai_draft	Hello,\n\n⚠️ DUPLICATE PAYMENT DETECTED:\n  - For BL NYC230: This payment has already been processed previously.\n\n💰 DUPLICATE PAYMENT: We detected that your payment of $1600.00 for BL(s) NYC230 has already been processed. No action is required from you.\n\nBest regards,\nIQS Trade Team	2025-08-06 03:34:33.03338	t	\N	\N	\N	\N	f	f	\N
793	81	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC233: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $25.00.\nPayment status:\n  - BL NYC233: Total Fee: $675.00, Paid: $0.00, Status: Invoice Sent\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 03:47:01.744802	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 448, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
794	82	openai_draft	Subject: Payment Status\nDear Customer,\nThe payment status for B/L NYC234 is as follows:\n- Amount Paid: $700\n- CTN Fee: $150\n- Service Fee: $200\nPayment for B/L NYC999 is not applicable as it is invalid.\nIf you have any further questions, feel free to reach out.\nThank you!\nIQSTrade Support Team\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $350.00. We will contact you regarding the excess payment of $350.00.\nBest regards,\nIQS Trade Team	2025-08-06 04:06:57.178479	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 476, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
795	83	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC235: Payment record found.\n💰 OVERPAYMENT: We have received your payment of $700.00, but the invoice amount is $675.00. We will contact you regarding the excess payment of $25.00.\nPayment status:\n  - BL NYC235: Total Fee: $675.00, Paid: $0.00, Status: Pending\nThe following BL numbers could not be found in our system: NYC999. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 04:15:12.780534	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 443, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
796	84	openai_draft	Hello,\nPayment(s) found:\n  - For BL NYC235: Payment record found.\n  - For BL NYC234: Payment record found.\n\n💰 OVERPAYMENT: We have received your payment of $1400.00, but the invoice amount is $1025.00. We will contact you regarding the excess payment of $375.00.\n\nThe following BL numbers could not be found in our system: ST987. Please double-check or contact us for assistance.\n\nBest regards,\nIQS Trade Team	2025-08-06 04:21:39.894997	t	\N	\N	0.8000000000000002	{"final_score": 0.8000000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 409, "has_action_items": true, "has_contact_info": true, "has_clear_structure": true}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
797	84	openai_draft	Hello,\n\n⚠️ DUPLICATE PAYMENT DETECTED:\n  - For BL NYC235: This payment has already been processed previously.\n  - For BL NYC234: This payment has already been processed previously.\n\n💰 DUPLICATE PAYMENT: We detected that your payment of $1400.00 for BL(s) NYC235, NYC234 has already been processed. No action is required from you.\n\nBest regards,\nIQS Trade Team	2025-08-06 04:21:52.470852	t	\N	\N	\N	\N	f	f	\N
798	85	openai_draft	Subject: 343\nPayment Status:\n- B/L NYC236: Paid\n- B/L NYC237: Paid\nTotal Paid Amount: $1700\nThank you for your payment. If you have any further questions, feel free to reach out.\n💰 OVERPAYMENT: We have received your payment of $1700.00, but the invoice amount is $1025.00. We will contact you regarding the excess payment of $675.00.\nBest regards,\nIQS Trade Team	2025-08-06 04:23:00.785464	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 362, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
799	86	openai_draft	Hello,\nInvoice(s) found:\n  - For BL NYC241: You can download your invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754460585/invoices/s3ngq3t3ovqotauohkz0.pdf\n  - For BL NYC240: You can download your invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754460557/invoices/l6ciziuqle3ci7rt86co.pdf\nThe following BL numbers could not be found in our system: NYC242. Please double-check or contact us for assistance.\nBest regards,\nIQS Trade Team	2025-08-06 06:35:58.480061	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 468, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.8, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
800	87	openai_draft	Dear customer, Our current fee structure for the NYC220 shipment is as follows: - CTN Fee: $100 per container - Service Fee: $100 per container. This amounts to a total of $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills. If you have any further questions or need assistance, feel free to reply to this message. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:23:58.277292	t	\N	\N	0.9500000000000001	{"final_score": 0.9500000000000001, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 444, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
801	88	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:24:03.411362	t	\N	\N	0.9	{"final_score": 0.9, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 275, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
802	89	openai_draft	Dear customer, you can request a copy of your invoice by replying to this WhatsApp message. If you need assistance, please provide your B/L or CTN number. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:24:08.875201	t	\N	\N	0.9500000000000001	{"final_score": 0.9500000000000001, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 216, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
803	90	openai_draft	Dear customer,\nThank you for your inquiry regarding the payment status for NYC223. If you have any further questions or need assistance, please feel free to reply to this WhatsApp message.\nThank you!\nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:24:15.250071	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 250, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 2, "low_confidence_indicators": 0}	t	f	\N
804	91	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to contact our support team by replying to this WhatsApp message or calling our hotline at [your phone number]. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:24:20.312421	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 367, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
805	93	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:31:37.827446	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 275, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
806	94	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:31:43.284624	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 275, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
807	95	openai_draft	Dear customer, Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day. If you have any further questions, feel free to reach out to us. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:31:49.810073	t	\N	\N	0.9	{"final_score": 0.9, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 275, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 1, "low_confidence_indicators": 0}	t	f	\N
808	96	openai_draft	Dear customer,\nThe processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used.\nIf you have any further questions, just reply to this WhatsApp message.\nThank you!\nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-06 08:31:55.742152	t	\N	\N	0.8	{"final_score": 0.8, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 337, "has_action_items": false, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
809	97	openai_draft	Dear Client, Here are the updates for your requested shipments: 1. NYC224: Payment status and CTN number - Invalid BL, no payment status or CTN available. 2. NYC225: Invoice and tracking details - Invoice link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754390000/invoices/pi2esxbkb7t3v4swpt47.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754390000/invoices/pi2esxbkb7t3v4swpt47.pdf), CTN number: UTY010214. 3. NYC226: Reserve settlement amount - Awaiting Bank In, no payment amount available. If you need further assistance, feel free to reach out. Best regards, IQS Trade\nBest regards,\nIQS Trade Team	2025-08-06 08:37:13.225727	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 620, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
810	98	openai_draft	Hello Client, \nThe CTN number for shipment NYC227 is RAY090909. You can find the invoice for this shipment by clicking on the following link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754445798/invoices/asvvpk0dpu1f4z9qrelh.pdf). \nRegarding the pickup arrangement, please let us know your preferred date and time so we can schedule the container for pickup. \nThank you!\nBest regards,\nIQS Trade Team	2025-08-06 08:37:19.809974	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 421, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
811	99	openai_draft	Hi Client, \nThe CTN number for shipment NYC228 is RAY765432. The current status of this shipment is 'Awaiting Bank In'. If you have any further questions, feel free to reach out. Have a great day! \nIQS Trade\nBest regards,\nIQS Trade Team	2025-08-06 08:37:25.38446	t	\N	\N	0.9000000000000001	{"final_score": 0.9000000000000001, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 236, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 2, "low_confidence_indicators": 0}	t	f	\N
812	100	openai_draft	Dear Client,\nWe have received your partial payment of $150 for NYC229. However, please note that the total amount due for this shipment is $200, and the remaining balance of $50 is still outstanding.\nRegarding payment methods, we accept the following:\n- Bank Transfer\n- Allinpay\n- Stripe\nIf you have any further questions or need assistance, feel free to reach out.\nThank you!\nIQSTrade Support Team\n💰 OVERPAYMENT: We have received your payment of $400.00, but the invoice amount is $350.00. We will contact you regarding the excess payment of $50.00.\nBest regards,\nIQS Trade Team	2025-08-06 08:37:32.605054	t	\N	\N	0.9500000000000002	{"final_score": 0.9500000000000002, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 579, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 2, "low_confidence_indicators": 0}	t	f	\N
813	100	openai_draft	Hello,\n\n⚠️ DUPLICATE PAYMENT DETECTED:\n  - For BL NYC229: This payment has already been processed previously.\n\n💰 DUPLICATE PAYMENT: We detected that your payment of $150.00 for BL(s) NYC229 has already been processed. No action is required from you.\n\nBest regards,\nIQS Trade Team	2025-08-06 08:37:39.387853	t	\N	\N	\N	\N	f	f	\N
814	101	openai_draft	Hello Client, \nRegarding your inquiries: \nNYC230: \n1. The CTN number is HPF908350. \n2. You can access the invoice through this link: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754449240/invoices/czk1i0b6dxgvnvqrswef.pdf). \n3. The payment status is currently unpaid. \nNYC231 and NYC232: \nUnfortunately, there is no information provided for these Bill of Ladings. \nIf you have any further questions or need assistance, feel free to reach out. \nThank you, \nIQS Trade\nBest regards,\nIQS Trade Team	2025-08-06 08:38:04.30415	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 514, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 6, "low_confidence_indicators": 0}	t	f	\N
815	102	openai_draft	Hello Client, Here are the details you requested: NYC230 - CTN number: HPF908350, Invoice: [Invoice Link], Payment Status: Invoice Sent, Reserve Amount: $675. NYC231 - CTN number: ray8398439, Invoice: [Invoice Link], Payment Status: Invoice Sent, Reserve Amount: $350. NYC232 - CTN number: ray48309483, Invoice: [Invoice Link], Payment Status: Invoice Sent, Reserve Amount: $350. If you need further assistance, feel free to reach out. Thank you, IQS Trade\nBest regards,\nIQS Trade Team	2025-08-06 09:03:02.903216	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 485, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 6, "low_confidence_indicators": 0}	t	f	\N
816	103	openai_draft	Hello,\nPayment status:\n  - BL NYC230: Total Fee: $675.00, Paid: $0.00, Status: Invoice Sent\n  - BL NYC232: Total Fee: $350.00, Paid: $0.00, Status: Invoice Sent\n  - BL NYC231: Total Fee: $350.00, Paid: $0.00, Status: Invoice Sent\nInvoice(s) found:\n  - For BL NYC230: You can download your invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754449240/invoices/czk1i0b6dxgvnvqrswef.pdf\n  - For BL NYC232: You can download your invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754450566/invoices/i4p1wg89kmyavy75iu4x.pdf\n  - For BL NYC231: You can download your invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754450532/invoices/a2h5h14piskg2u2rgkl1.pdf\nCTN(s) found:\n  - For BL NYC230: The CTN number is HPF908350.\n  - For BL NYC232: The CTN number is ray48309483.\n  - For BL NYC231: The CTN number is ray8398439.\nBest regards,\nIQS Trade Team	2025-08-06 09:22:32.817145	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 884, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 6, "low_confidence_indicators": 0}	t	f	\N
817	104	openai_draft	Hello, Regarding BL2024014: 1. The CTN number is currently processing and will be available within 24 to 48 hours after payment confirmation. 2. You can request the invoice by replying to this message with the invoice link. 3. The payment status is 'Paid and CTN Valid.' For BL2024013 and BL2024012: The CTN numbers are also processing and will be available within the same timeframe. If you have any further questions, feel free to ask. Thank you!\nBest regards,\nIQS Trade Team	2025-08-06 09:34:48.905576	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 477, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 7, "low_confidence_indicators": 0}	t	f	\N
818	105	openai_draft	Hello, Regarding NYC226: 1. The CTN number is Ray010101. 2. You can access the invoice through this link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf). 3. The payment status is 'Paid and CTN Valid'. For NYC227 and NYC228, please provide the specific request types for further assistance.\nBest regards,\nIQS Trade Team	2025-08-06 09:38:38.782324	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 462, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 6, "low_confidence_indicators": 0}	t	f	\N
819	106	openai_draft	Hello, regarding NYC226: 1. The CTN number is Ray010101. 2. You can access the invoice here: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf). 3. The payment status is 'Paid and CTN Valid'. 4. The arrival time at the port is not specified in your request. 5. The reserve amount is not specified in your request. For NYC227: 1. The CTN number is RAY090909. 2. The invoice link is [https://res.cloudinary.com/dtm46mski/raw/upload/v1754445798/invoices/asvvpk0dpu1f4z9qrelh.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754445798/invoices/asvvpk0dpu1f4z9qrelh.pdf). 3. The payment status is 'Paid and CTN Valid'. 4. The arrival time at the port is not specified in your request. 5. The reserve amount is not specified in your request. For NYC228: 1. The CTN number is RAY765432. 2. The invoice link is [https://res.cloudinary.com/dtm46mski/raw/upload/v1754445844/invoices/pitab1ide6k59vywsa9c.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754445844/invoices/pitab1ide6k59vywsa9c.pdf). 3. The payment status is 'Paid and CTN Valid'. 4. The arrival time at the port is not specified in your request. 5. The reserve amount is not specified in your request.\nBest regards,\nIQS Trade Team	2025-08-06 10:02:08.308581	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 1338, "has_action_items": false, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 6, "low_confidence_indicators": 0}	t	f	\N
820	107	openai_draft	Dear customer, regarding your inquiries: \nFor BL NYC233, we do not have any information available in our records. \nFor BL NYC234, the status is 'Invoice Sent'. You can access the invoice here: [Invoice Link](https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf). The CTN number is ray787944. The CTN fee is $150.00, and the service fee is $200.00. The paid amount is $0.00. \nFor BL NYC236, the status is 'Awaiting Bank In'. The CTN number is DDZ549122. The invoice link is [here](https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf). The CTN fee is $150.00, and the service fee is $200.00. The paid amount is $0.00. \nTo settle the payment, you can choose from the following methods: Bank Transfer, Allinpay, or Stripe. Instructions will be provided when you generate a payment link. \nThe CTN processing time is typically between 24 to 48 hours after payment confirmation. Please note that the exact time may vary depending on the payment method used. \nIf you have any further questions, feel free to reply to this message. \nThank you! \nIQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-08 00:26:26.07382	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 1169, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
821	108	openai_draft	Dear customer, regarding your requests: \nFor BL NYC233:\n- Invoice link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754451721/invoices/iroh7eigu7lmpmonruzb.pdf]\n- Status: Invoice Sent\nFor BL NYC234:\n- Invoice link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf]\n- Status: Invoice Sent\nFor BL NYC236:\n- Invoice link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf]\n- Status: Awaiting Bank In\nTo settle the payment, you can use Bank Transfer, Allinpay, or Stripe. Instructions will be provided when you generate a payment link. The processing time for CTN is 24 to 48 hours after payment confirmation. If you need further assistance, feel free to reply to this message. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-08 00:29:30.658321	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 833, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
822	105	support@iqstrade.com	Hello, Regarding NYC226: 1. The CTN number is Ray010101. 2. You can access the invoice through this link: [https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf](https://res.cloudinary.com/dtm46mski/raw/upload/v1754393369/invoices/v9v851u7onyp6f8xhebo.pdf). 3. The payment status is 'Paid and CTN Valid'. For NYC227 and NYC228, please provide the specific request types for further assistance.\nBest regards,\nIQS Trade Team	2025-08-08 00:31:02.737515	f	2025-08-08 00:31:02.737519	email	\N	\N	f	t	\N
823	109	openai_draft	Dear customer, regarding your request: \nFor BL NYC233:\n- Invoice has been sent. You can access it here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf\n- Status: Invoice Sent\nFor BL NYC234:\n- Invoice has been sent. You can access it here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf\n- Status: Invoice Sent\nFor BL NYC236:\n- Invoice link: https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf\n- Status: Awaiting Bank In\nTo settle the payment, you can choose from the following methods: Bank Transfer, Allinpay, Stripe. Instructions will be provided when you generate a payment link.\nThe CTN processing time is typically between 24 to 48 hours after payment confirmation. Please let us know if you have any further questions. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-09 05:38:37.161832	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 920, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
824	110	openai_draft	Dear customer, regarding your requests: \nFor BL NYC233:\n- Invoice: Please find the invoice link here: N/A\n- Status: Not provided\n- Payment: You can settle the payment via Bank Transfer, Allinpay, or Stripe\nFor BL NYC234:\n- Invoice: You can access the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf\n- Status: Invoice Sent\n- Payment: Bank Transfer, Allinpay, Stripe are accepted\nFor BL NYC236:\n- Invoice: You can view the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf\n- Status: Awaiting Bank In\n- Payment: Bank Transfer, Allinpay, Stripe are accepted\nCTN Processing Time: The processing time for CTN is 24 to 48 hours after payment confirmation. If you have any further questions, feel free to reach out. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-09 07:55:39.667618	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 887, "has_action_items": true, "has_contact_info": false, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
825	111	openai_draft	Dear customer, regarding your recent inquiry: 1. For BL number: ABC123456 - Cargo Tracking Note (CTN) processing time is typically between 24 to 48 hours after payment confirmation. - Accepted payment methods include Bank Transfer, Allinpay, and Stripe. - Current fee structure is $100 CTN Fee and $100 Service Fee per container. - To track CTN status, provide your B/L or CTN number. 2. For any further questions or assistance, feel free to reply to this message. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-09 08:08:17.129353	t	\N	\N	0.8500000000000001	{"final_score": 0.8500000000000001, "bl_numbers_found": false, "response_quality": {"has_greeting": true, "response_length": 526, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.7, "auto_send_recommended": true, "high_confidence_keywords": 0, "low_confidence_indicators": 0}	t	f	\N
826	112	openai_draft	Dear customer, regarding your requests: \nFor BL NYC233:\n- Invoice: Not requested\n- Status: Not provided\n- Payment: Not mentioned\n- CTN Process: Not mentioned\nFor BL NYC234:\n- Invoice: You can access the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf\n- Status: Invoice Sent\n- Payment: Not mentioned\n- CTN Process: 24 to 48 hours after payment confirmation\nFor BL NYC236:\n- Invoice: You can access the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf\n- Status: Awaiting Bank In\n- Payment: Not mentioned\n- CTN Process: 24 to 48 hours after payment confirmation\nTo settle the payment, you can choose from Bank Transfer, Allinpay, or Stripe. The CTN processing time is typically 24 to 48 hours after payment confirmation. If you need further assistance, feel free to reach out. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-09 08:10:36.381138	t	\N	\N	1	{"final_score": 1.0, "bl_numbers_found": true, "response_quality": {"has_greeting": true, "response_length": 954, "has_action_items": true, "has_contact_info": true, "has_clear_structure": false}, "classification_score": 0.5, "auto_send_recommended": true, "high_confidence_keywords": 5, "low_confidence_indicators": 0}	t	f	\N
827	112	support@iqstrade.com	Dear customer, regarding your requests: \nFor BL NYC233:\n- Invoice: Not requested\n- Status: Not provided\n- Payment: Not mentioned\n- CTN Process: Not mentioned\nFor BL NYC234:\n- Invoice: You can access the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf\n- Status: Invoice Sent\n- Payment: Not mentioned\n- CTN Process: 24 to 48 hours after payment confirmation\nFor BL NYC236:\n- Invoice: You can access the invoice here: https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf\n- Status: Awaiting Bank In\n- Payment: Not mentioned\n- CTN Process: 24 to 48 hours after payment confirmation\nTo settle the payment, you can choose from Bank Transfer, Allinpay, or Stripe. The CTN processing time is typically 24 to 48 hours after payment confirmation. If you need further assistance, feel free to reach out. Thank you! IQSTrade Support Team\nBest regards,\nIQS Trade Team	2025-08-09 08:11:04.346759	f	2025-08-09 08:11:04.346765	email	\N	\N	f	t	\N
\.


--
-- Data for Name: customer_emails; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customer_emails (id, sender, subject, body, attachments, bl_numbers, created_at, processed_at, classification, openai_processed, processed_for_payments, message_id, from_addr, outlook_message_id, processed_by_outlook, outlook_user_id, status, updated_at, cc, bcc, reply_to, "to") FROM stdin;
1	Jething John <johnwongjething@gmail.com>	Fwd: a	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:34:55.394574	\N	\N	f	f	<CAF7a8r3_FE8fNsmpK2dMdLSJsQrQwNcOQDejLFmjJ2TNUOFh_Q@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
2	Jething John <johnwongjething@gmail.com>	hh	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:36:58.544994	\N	\N	f	f	<CAF7a8r2SG3qP5TdR7o-+OR_emL_AbP221TLo_cv85iWfq4OYXA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
3	Jething John <johnwongjething@gmail.com>	gg	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:39:00.064095	\N	\N	f	f	<CAF7a8r3p+4+8n+2dAjeD5CY5FpO+h8a60ZnqV650X_rs8SJ_gg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
4	Jething John <johnwongjething@gmail.com>	hhh	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:47:28.853359	\N	\N	f	f	<CAF7a8r3PPUUDv1N=TKPrrDuuy=v=K4azL3LP33KmJisXCnCUCw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
5	Jething John <johnwongjething@gmail.com>	hhh	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:49:58.474491	\N	\N	f	f	<CAF7a8r3KbpLFpDsZGetYLPof=fOenbNVwj-BxVWitDdjFudc6Q@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
6	Jething John <johnwongjething@gmail.com>	hhk	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 01:53:52.23837	\N	\N	f	f	<CAF7a8r1RLGoNyhaxP-hwg-vMsJxyNnxhiyX6T9nVuNLYGrJdog@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
7	Jething John <johnwongjething@gmail.com>	aaa	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 02:00:29.465784	\N	\N	f	f	<CAF7a8r0m3JM8G=MB_zOBhTHHwyDxz+ZvEeHX8=zFFkmYD=sm2g@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
8	Jething John <johnwongjething@gmail.com>	asd	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 02:10:35.899788	\N	general	t	f	<CAF7a8r20+Q9kU1wHKCFw0xzzar318hoaz29fND5OA1UKPmzsbQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
9	Jething John <johnwongjething@gmail.com>	ashh	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 02:32:12.528594	\N	payment_receipt	t	f	<CAF7a8r3P9LphN1GyBVS5SLQp_BHtAkB8TpBfWUa=aj6VfTYBRw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
10	Jething John <johnwongjething@gmail.com>	ray	Can you send me invoice and ctn number for BL NYC2201666\r\n	\N	{}	2025-08-01 02:32:23.611858	\N	bl_inquiry	t	f	<CAF7a8r0K30UQ0gy2XvmMAHK0eYKtapRgjy-2czsNH3Xn0EZrHA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
11	Jething John <johnwongjething@gmail.com>	KJHGFD	Can you send me invoice and ctn number for BL NYC220\r\n	\N	{NYC220}	2025-08-01 02:53:42.561307	\N	combined_request	t	f	<CAF7a8r2m+ExEFuWW3daPwpf_5MHjEWa88GP0DLjBjg05NZ2kfA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
12	Jething John <johnwongjething@gmail.com>	dfdfd	Can you send me invoice and ctn number for BL NYC220\r\n	\N	{NYC220}	2025-08-01 03:06:51.635905	\N	combined_request	t	f	<CAF7a8r1MHsX0GNyLasBwEzKHv9+df_JW4GvmZESn6ibpa1CbVg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
13	Jething John <johnwongjething@gmail.com>	aaaaaa	Can you send me invoice and ctn number for BL NYC220\r\n	\N	{NYC220}	2025-08-01 03:07:12.453223	\N	combined_request	t	f	<CAF7a8r2sru_+oCLozPdGqV=ZVb1Os5kPQ2Eeu-Wa22EtyA9VoQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
14	Jething John <johnwongjething@gmail.com>	hf	can you advise your payment method, ctn process time i also want to know\r\nhow much is the fee and how long it takes to process the ctn what is your\r\npayment method\r\n	\N	{}	2025-08-01 03:09:22.738955	\N	combined_request	t	f	<CAF7a8r2ZBRZXCV9dFy1TcEsj53bK3chW2p8Vvn6QrpvpTA9Baw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
15	Jething John <johnwongjething@gmail.com>	rr	Hi Team, I'm sending payment for: - BL NAM20: $100 (should be $250 total) -\r\nBL 001-123: $150 (should be $200 total) - BL NYC220: $50 (should be $200\r\ntotal) Total sent: $300. Please confirm what's still due. Thanks, John\r\n	\N	{NAM20,NYC220,001-123}	2025-08-01 03:09:37.524098	\N	combined_request	t	f	<CAF7a8r3YHdKnLf8JvEnFybxCNBvywPF6dy4kqO8r-75CAwbNZQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
16	Jething John <johnwongjething@gmail.com>	aaahh	Payment for B/L  001-123, NYC220 Amount: $420 Ref: TEST987\r\n	\N	{NYC220,001-123}	2025-08-01 03:11:24.258959	\N	combined_request	t	f	<CAF7a8r1K5Ot-f+w=ZCQCqfXqPOPzc6GB33W=fGS8dCZYxZHVAg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
17	Jething John <johnwongjething@gmail.com>	aaahh	Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987	\N	\N	2025-08-01 03:15:48.173912	\N	combined_request	t	f	\N	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
18	Jething John <johnwongjething@gmail.com>	fafaf	Payment for B/L  001-123, NYC220 Amount: $420 Ref: TEST987\r\n	\N	{NYC220,001-123}	2025-08-01 03:20:04.217129	\N	combined_request	t	f	<CAF7a8r2aqC_cxjSB_RkaA+YuCZ19-6MEe4a0Z0G+r2VLE-06Qg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
19	Jething John <johnwongjething@gmail.com>	hgf	Payment for B/L  NYC220 Amount: $700 Ref: TEST987\r\n	\N	{NYC220}	2025-08-01 03:21:07.109821	\N	combined_request	t	f	<CAF7a8r2WWfE4R5ZZkSUq36HFw0JCDnJeHd6C5radcOcHScy8Rg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
20	Jething John <johnwongjething@gmail.com>	hhhjhgfd	Payment for B/L  NYC220 Amount: $700 Ref: TEST987\r\n	\N	{NYC220}	2025-08-01 03:31:33.106191	\N	combined_request	t	t	<CAF7a8r0xXmgXQ-BBUFCDBRqKFD1vVRwhJAxs6YN6HYB8hcrHzw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
21	Jething John <johnwongjething@gmail.com>	kjh	Payment for B/L  NYC220 Amount: $720 Ref: TEST987\r\n	\N	{NYC220}	2025-08-01 04:04:38.583409	\N	combined_request	t	t	<CAF7a8r0rQ_UHHHhtq6x+o4LkZEFDN4=nNGMZ3yiQcM++cU=MzA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
22	Jething John <johnwongjething@gmail.com>	kkkk	Payment for B/L  NYC220 Amount: $680 Ref: TEST987\r\n	\N	{NYC220}	2025-08-01 04:07:19.867172	\N	combined_request	t	t	<CAF7a8r1Wxf6aS7fa2whPi2YydC-7TLD1edQX39fZ5Xkfpc4X6w@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
23	Jething John <johnwongjething@gmail.com>	afdsg	\r\n	["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\overpayment_receipt.pdf"]	{987-654321,NYC220}	2025-08-01 06:05:44.084818	\N	combined_request	t	t	<CAF7a8r3ZYxpcnMk=eUNkDovHPu3x6SujqFPo=uUvXD=ZR2iaWg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
24	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Receipt - NYC220		\N	{}	2025-08-01 07:02:11.731308	\N	general_enquiry	t	f	<202508010701.26860702577@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
25	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Confirmation - NYC221		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc221.pdf"]	{202508011501,NYC221}	2025-08-01 07:02:29.61285	\N	combined_request	t	f	<202508010701.82804796013@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
26	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment for NYC223		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc223.pdf"]	{202508011501,NYC223}	2025-08-01 07:02:48.53305	\N	combined_request	t	f	<202508010701.51885190402@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
27	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment for NYC224		\N	{}	2025-08-01 07:02:58.611199	\N	general_enquiry	t	f	<202508010701.61539115519@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
28	"Test Payment System" <ray6330099@9433503.brevosend.com>	Partial Payment - NYC220		\N	{}	2025-08-01 07:03:07.96242	\N	general_enquiry	t	f	<202508010701.58432882898@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
29	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Receipt - NYC225		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc225.pdf"]	{NYC225,202508011501}	2025-08-01 07:03:29.10481	\N	combined_request	t	f	<202508010701.88245773389@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
30	"Test Payment System" <ray6330099@9433503.brevosend.com>	Bulk Payment - Multiple BLs		\N	{}	2025-08-01 07:03:38.498912	\N	general_enquiry	t	f	<202508010701.17480320695@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
31	"Test Payment System" <ray6330099@9433503.brevosend.com>	Overpayment - NYC221		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc221_overpayment.pdf"]	{202508011501,NYC221}	2025-08-01 07:03:57.076599	\N	combined_request	t	f	<202508010701.61673161963@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
32	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Confirmation - NYC221		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc221.pdf"]	{202508011518,NYC221}	2025-08-01 07:19:33.111225	\N	combined_request	t	f	<202508010718.36509451846@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
33	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Receipt - NYC220		\N	{}	2025-08-01 07:29:21.445403	\N	general_enquiry	t	f	<202508010728.40660165158@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
34	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Confirmation - NYC221		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc221.pdf"]	{202508011528,NYC221}	2025-08-01 07:29:44.641472	\N	combined_request	t	f	<202508010728.77178193028@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
35	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment for NYC223		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc223.pdf"]	{NYC223,202508011528}	2025-08-01 07:30:06.62327	\N	combined_request	t	f	<202508010728.37944541355@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
36	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment for NYC224		\N	{}	2025-08-01 07:30:16.6607	\N	general_enquiry	t	f	<202508010728.54216887995@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
37	"Test Payment System" <ray6330099@9433503.brevosend.com>	Partial Payment - NYC220		\N	{}	2025-08-01 07:30:24.947104	\N	general_enquiry	t	f	<202508010728.70135307242@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
38	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Receipt - NYC225		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc225.pdf"]	{202508011528,NYC225}	2025-08-01 07:30:43.258683	\N	combined_request	t	f	<202508010728.71282926241@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
39	"Test Payment System" <ray6330099@9433503.brevosend.com>	Overpayment - NYC221		["C:\\\\Users\\\\My Account\\\\Desktop\\\\iqs\\\\iqstrade\\\\backend\\\\pdf_attachments\\\\receipt_nyc221_overpayment.pdf"]	{202508011528,NYC221}	2025-08-01 07:31:04.593085	\N	combined_request	t	f	<202508010728.11710441619@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
40	"Test Payment System" <ray6330099@9433503.brevosend.com>	Bulk Payment - Multiple BLs		\N	{}	2025-08-01 07:31:12.016549	\N	general_enquiry	t	f	<202508010728.69097453825@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
41	"Test Payment System" <ray6330099@9433503.brevosend.com>	Payment Confirmation - NYC221		["https://res.cloudinary.com/dtm46mski/raw/upload/v1754037853/email_attachments/cvmrszkilmt3l8esakks.pdf"]	{NYC221,202508011641}	2025-08-01 08:44:15.265853	\N	\N	f	f	<202508010841.21808397433@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
42	"Test Payment System" <ray6330099@9433503.brevosend.com>	Overpayment - NYC221		["https://res.cloudinary.com/dtm46mski/raw/upload/v1754038111/email_attachments/gqlyr8l9q3vt1qmotxuk.pdf"]	{202508011647,NYC221}	2025-08-01 08:48:33.355801	\N	\N	f	f	<202508010847.60501449936@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
81	Jething John <johnwongjething@gmail.com>	hsgs	Payment for B/L  NYC233, NYC999 Amount: $700 Ref: TEST987\r\n	\N	{NYC233}	2025-08-06 03:46:58.11169	\N	\N	f	t	<CAF7a8r1yvMvmss3KHh3iEDTXHSz1RnUG8qsvJCL1Tc-Cza2Ong@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:46:58.122666	\N	\N	\N	\N
43	"Test Payment System" <ray6330099@9433503.brevosend.com>	Overpayment - NYC221		["https://res.cloudinary.com/dtm46mski/raw/upload/v1754038404/email_attachments/bwogbjihrrbgssbkavaq.pdf"]	{202508011651,NYC221,20250801}	2025-08-01 08:53:26.732832	\N	\N	f	t	<202508010851.73860151359@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
44	Jething John <johnwongjething@gmail.com>	afafa	Payment for B/L  NYC221 Amount: $700 Ref: TEST987\r\n	\N	{NYC221}	2025-08-01 09:00:32.184644	\N	\N	f	t	<CAF7a8r2rdHYn98FBXc-1r_UNLiYW6AQVFiBwaTeeYODeCgjRfw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
45	Jething John <johnwongjething@gmail.com>	aaafff	Payment for B/L  NYC220 Amount: $600 Ref: TEST987\r\n	\N	{NYC220}	2025-08-01 09:03:50.626799	\N	\N	f	t	<CAF7a8r1iZ=L9=-xo7HQy-TooT_N4jrj8_cuA-TCOD0cwWVC1Kw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
46	Jething John <johnwongjething@gmail.com>	fgfg	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754040331/email_attachments/wfweclqkywvhtynkszvz.pdf"]	{NYC220}	2025-08-01 09:25:33.13712	\N	\N	f	t	<CAF7a8r2p_VORFP+hp-tfUjHPt2XkkeNFtix+0rCtNN8sUwGQbQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
47	Jething John <johnwongjething@gmail.com>	Fwd: r2	can you advise your payment method, ctn process time i also want to know\r\nhow much is the fee and how long it takes to process the ctn what is your\r\npayment method\r\n	\N	{}	2025-08-01 09:31:15.131647	\N	\N	f	f	<CAF7a8r2-tNXS_5HNiWJMUxwFhnNc-2B-RHW=YsOtWsQMzX68cg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
50	Jething John <johnwongjething@gmail.com>	lkjhgf	can you advise your payment method, ctn process time i also want to know\r\nhow much is the fee and how long it takes to process the ctn what is your\r\npayment method\r\n	\N	{}	2025-08-01 10:09:07.28643	\N	\N	f	f	<CAF7a8r08xmLtT7hhxN39R1DgB2UxB6r+BwcWK6PVXYtM2fsy1w@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:38:04.873298	\N	\N	\N	\N
49	Jething John <johnwongjething@gmail.com>	rrere	can you advise your payment method, ctn process time i also want to know\r\nhow much is the fee and how long it takes to process the ctn what is your\r\npayment method\r\n	\N	{}	2025-08-01 09:52:54.074351	\N	\N	f	f	<CAF7a8r2+MgXWPUgtC0-=rGLbyf1k4pxqeiF_-cSA+bFE5QdL6Q@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-01 18:39:47.577988	\N	\N	\N	\N
48	Jething John <johnwongjething@gmail.com>	Fwd: fgfg	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754041942/email_attachments/da55qwh7mfynvt3b0g4j.pdf"]	{NYC220}	2025-08-01 09:52:24.613913	\N	\N	f	t	<CAF7a8r00m1OmnDi8MmmHPfdQrQf3VQ10kBEv5Die1M9ufQgbBA@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-01 18:42:14.326073	\N	\N	\N	\N
51	Jething John <johnwongjething@gmail.com>	test	test\r\n	\N	{}	2025-08-01 10:45:17.643584	\N	\N	f	f	<CAF7a8r1ocjguQxixv8HYwVNbE4zD2v9NRAtC3M-2ugjj=7Vudw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:45:16.558754	\N	\N	\N	\N
52	Jething John <johnwongjething@gmail.com>	test23	3fff\r\n	\N	{}	2025-08-01 10:48:42.646957	\N	\N	f	f	<CAF7a8r2rDh8kZEeZW=_okmQiS7U1gZfWyT1pp5rjeGqHRUVLXg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:48:41.557201	\N	\N	\N	\N
53	Jething John <johnwongjething@gmail.com>	hhhh	hhhhh\r\n	\N	{}	2025-08-01 10:53:32.755432	\N	\N	f	f	<CAF7a8r2nCuQvh1h2Ae_PYaAG4E02Ep8h0M6p1=0i_9j1nmAzNg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:53:31.670502	\N	\N	\N	\N
54	Jething John <johnwongjething@gmail.com>	Fwd: fgfg	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754045742/email_attachments/m4wy0tptyjaexwimxvxm.pdf"]	{NYC220}	2025-08-01 10:55:44.30444	\N	\N	f	t	<CAF7a8r3s0ZtgZ3bAihufy=Az=pPOmjy9r-0hdpcKyROU97rBaA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 10:55:43.228692	\N	\N	\N	\N
55	Jething John <johnwongjething@gmail.com>	Fwd: fgfg	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754046340/email_attachments/dj1gpmv0zwwynntr4vxy.pdf"]	{NYC220}	2025-08-01 11:05:43.007418	\N	\N	f	t	<CAF7a8r1VnL3HFnW7Usg1uNJ7SOaswWdQh0gVng6D7ONpR9turA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-01 11:05:41.925548	\N	\N	\N	\N
82	Jething John <johnwongjething@gmail.com>	fsdfs	Payment for B/L  NYC234, NYC999 Amount: $700 Ref: TEST987\r\n	\N	{NYC234}	2025-08-06 04:06:53.731721	\N	\N	f	f	<CAF7a8r0FA=g5M5f8XHaWXBOY87+KU3CnbHDTGRAZ2NTq7NqoSA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 04:06:53.741643	\N	\N	\N	\N
57	Fly <support@fly.io>	Activate your Fly.io account	Welcome to Fly.io!\r\n\r\nCheck out our docs to help you get things rolling: https://fly.io/docs/\r\n\r\nIf you have questions, get stuck, or want to talk about what you're building, visit our community discussion forum: https://community.fly.io/\r\n\r\nWe've created your user account. You can set a password for future logins: https://fly.io/app/password_resets/bb713668e460153c7ce54356e391f13fb9b92bc5a3c88bdadbaae3c06c7fad7e\r\n\r\n- The Fly.io team\r\n\r\n\r\n	\N	{460153,ce54356,bb713668}	2025-08-02 08:45:04.480627	\N	\N	f	f	<688dce2922484_1cb115bd0234a0@e822e92c77dd38.mail>	\N	\N	f	\N	New	2025-08-02 08:45:04.495831	\N	\N	\N	\N
58	Will <w.stewart@northflank.com>	Ready to deploy	Hi,\r\n\r\nI’m Will, CEO at Northflank. Great to have you with us.\r\n\r\nLet us know if anything’s unclear as you get set up. Excited to see\r\nwhat you build.\r\n\r\nFeel free to share feedback, your replies go straight to me.\r\n\r\nShip well,\r\nWill\r\n	\N	{}	2025-08-02 09:36:38.274164	\N	\N	f	f	<CAD6p0v1Za2WbtNvAcyO5uouCmQ9hXWWMxoU_LAH6WOg8xYS_QQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 09:36:38.28859	\N	\N	\N	\N
59	Jething John <johnwongjething@gmail.com>	fff	can you advise your payment method, ctn process time i also want to know\r\nhow much is the fee and how long it takes to process the ctn what is your\r\npayment method\r\n	\N	{}	2025-08-02 10:40:52.076506	\N	\N	f	f	<CAF7a8r2ii4i2P5g6NWarXjzV2VN9jGVD=BrMkN69GyMVmR1wQQ@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-02 10:46:15.616332	\N	\N	\N	\N
56	Jething John <johnwongjething@gmail.com>	fdfdd	fdffs\r\n	\N	{}	2025-08-01 11:06:23.08878	\N	\N	f	f	<CAF7a8r2pzDyPk=dz92YbTswpZsk31yvN92sH+9hAOEG3Jtz-Xw@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-02 10:47:44.319546	\N	\N	\N	\N
60	Jething John <johnwongjething@gmail.com>	g	Jething John <johnwongjething@gmail.com>\r\n8月1日 週五 下午4:59 (1 天前)\r\n寄給 ray6330088\r\nPayment for B/L  NYC221 Amount: $700 Ref: TEST987\r\n	\N	{NYC221,ray6330088}	2025-08-02 10:50:40.473479	\N	\N	f	t	<CAF7a8r1a9US8kYa=gTNoA3ncnE+1-dwybXStLwBTyzZZ04_nNg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 10:50:40.48865	\N	\N	\N	\N
61	Jething John <johnwongjething@gmail.com>	fg	Payment for B/L  NYC220 Amount: $600 Ref: TEST987\r\n	\N	{NYC220}	2025-08-02 10:53:50.251738	\N	\N	f	t	<CAF7a8r1Wc8tahfT9TpPWxkGDma8x-UAQ1WrUysZ1UHVrbBA5fA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 10:53:50.26541	\N	\N	\N	\N
62	Jething John <johnwongjething@gmail.com>	hhh	Payment for B/L  NYC220 Amount: $700 Ref: TEST987\r\n	\N	{NYC220}	2025-08-02 10:56:44.108026	\N	\N	f	t	<CAF7a8r1aA0tib4nrL=6HQ8s16eJ9H4_JOd5CB=4W_WuUtK3SaQ@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-02 11:22:49.752894	\N	\N	\N	\N
63	Jething John <johnwongjething@gmail.com>	gdas	Payment for B/L  NYC220 Amount: $800 Ref: TEST987\r\n	\N	{NYC220}	2025-08-02 11:33:31.656881	\N	\N	f	t	<CAF7a8r1P5kCesRNC8fhuF0v8p4jkfxVh4XdjRo=kXPGAcwdKhg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 11:33:31.672764	\N	\N	\N	\N
64	Jething John <johnwongjething@gmail.com>	t	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754134580/email_attachments/fk6jtpabgfeomampuzgt.pdf"]	{NYC220}	2025-08-02 11:36:21.275064	\N	\N	f	t	<CAF7a8r1tZgJVyHEaCUNJgNn8Bh1drBSMjMWRK5KKxMBS0LMtrw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 11:36:21.289339	\N	\N	\N	\N
65	Jething John <johnwongjething@gmail.com>	dfd	Payment for B/L  NYC220, NYC221 Amount: $1600 Ref: TEST987\r\n	\N	{NYC221,NYC220}	2025-08-02 11:40:05.363748	\N	\N	f	t	<CAF7a8r1md=+r+pTpedt1YdCcO+H3Pjj4+EQT7Q=fcAXzL7XkiQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 11:40:05.379848	\N	\N	\N	\N
66	Jething John <johnwongjething@gmail.com>	Fwd: aaafff	Payment for B/L  NYC220 Amount: $600 Ref: TEST987\r\n	\N	{NYC220}	2025-08-02 12:46:49.418844	\N	\N	f	t	<CAF7a8r2rnim1rTMiDWQn=gpZVrOL8zjk4bEUGQ5vZ68eStpFKQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-02 12:46:49.436163	\N	\N	\N	\N
67	Jething John <johnwongjething@gmail.com>	yuu	yyy\r\n	\N	{}	2025-08-03 06:18:16.152227	\N	\N	f	f	<CAF7a8r3L9iwOCu43ztmhOhRTiphKnL_MBHLY0pbgXhGiBvvYww@mail.gmail.com>	\N	\N	f	\N	New	2025-08-03 06:18:16.166013	\N	\N	\N	\N
68	Jething John <johnwongjething@gmail.com>	ry	Payment for B/L  NYC225  Amount: $100 Ref: TEST987\r\n	\N	{NYC225}	2025-08-05 11:37:17.505113	\N	\N	f	t	<CAF7a8r2+eNTvoVCHagd4iV_L9Y6-vigi1xcdDzUSZb1gDy2=nw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-05 11:37:17.520751	\N	\N	\N	\N
69	Jething John <johnwongjething@gmail.com>	gga	Payment for B/L  NYC226 Amount: $900 Ref: TEST987\r\n	\N	{NYC226}	2025-08-05 11:39:49.982216	\N	\N	f	t	<CAF7a8r27RHQeOmcGkpisewxReMBOFS7cGqEw0BJRxN2BmiFSPQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-05 11:39:49.997573	\N	\N	\N	\N
70	Jething John <johnwongjething@gmail.com>	h	Payment for B/L  NYC226 Amount: $665 Ref: TEST987\r\n	\N	{NYC226}	2025-08-05 11:41:53.475013	\N	\N	f	t	<CAF7a8r3PzJ8p6RxLsvoYcVXfCF79YfkBDQWMmch5GOree9KD+w@mail.gmail.com>	\N	\N	f	\N	New	2025-08-05 11:41:53.490417	\N	\N	\N	\N
71	Jething John <johnwongjething@gmail.com>	F	Payment for B/L  NYC226 Amount: $1600 Ref: TEST987\r\n	\N	{NYC226}	2025-08-06 02:06:43.26332	\N	\N	f	f	<CAF7a8r1tF5z+RVTExRzZzfvX768ijBZhy+UWK_EaDSm3jRC_8g@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 02:06:43.276743	\N	\N	\N	\N
72	Jething John <johnwongjething@gmail.com>	gg	Payment for B/L  NYC226, NYC999 Amount: $1600 Ref: TEST987\r\n	\N	{NYC226}	2025-08-06 02:32:01.146816	\N	\N	f	t	<CAF7a8r3xd-7_zG8xWkeo4HurL8N_=6JyU_BwyGQQMQQrzb=kGg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 02:32:01.161549	\N	\N	\N	\N
73	Jething John <johnwongjething@gmail.com>	hhh	Payment for B/L  NYC226, NYC999 Amount: $1600 Ref: TEST987\r\n	\N	{NYC226}	2025-08-06 02:51:36.093182	\N	\N	f	t	<CAF7a8r2vRJB61E9oi9mFp3d9YiePDVFqcLRk3z3N41+PhwuLwg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 02:51:36.110483	\N	\N	\N	\N
74	Jething John <johnwongjething@gmail.com>	bes	Payment for B/L  NYC227, NYC228 Amount: $1600 Ref: TEST987\r\n	\N	{NYC228,NYC227}	2025-08-06 02:54:02.953047	\N	\N	f	t	<CAF7a8r1TvdKhe_TGDsghk0ufXkQVXZnp28s_sBsCK=kjw7LLzw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 02:54:02.966952	\N	\N	\N	\N
75	Jething John <johnwongjething@gmail.com>	hh	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754449398/email_attachments/pk34bggvjmkkbgoxrrjk.pdf"]	{NYC229}	2025-08-06 03:03:19.090036	\N	\N	f	t	<CAF7a8r3d+1y8Pk=AtzQMsDwmeHSp6Cn0cO-09GXJCwCHKXRhUQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:03:19.104126	\N	\N	\N	\N
76	Jething John <johnwongjething@gmail.com>	jj	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754449454/email_attachments/e4z78lads6mxxz6y9pvu.pdf"]	{NYC230}	2025-08-06 03:04:15.271882	\N	\N	f	t	<CAF7a8r3DJEz++FWQt8ch_NHozGEvOSEDWynvC5o+JDMAh8idtA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:04:15.285709	\N	\N	\N	\N
77	Jething John <johnwongjething@gmail.com>	hhhhds	Payment for B/L  NYC230, NYC999 Amount: $1250 Ref: TEST987\r\n	\N	{NYC230}	2025-08-06 03:08:11.201694	\N	\N	f	t	<CAF7a8r2fhDmVZ2kmF9fYk7v+7D3HMmnGvAR78=tJDG-n21PEFQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:08:11.21675	\N	\N	\N	\N
78	Jething John <johnwongjething@gmail.com>	kg	Payment for B/L  NYC231, NYC999 Amount: $400 Ref: TEST987\r\n	\N	{NYC231}	2025-08-06 03:24:20.502238	\N	\N	f	t	<CAF7a8r0qXwmTdfnW3j9swD_9ge-HKMwqqkTir+CyDmpapeXDnA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:24:20.515813	\N	\N	\N	\N
79	Jething John <johnwongjething@gmail.com>	ssf	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754450799/email_attachments/bt5fcvh2ocbs6qepissr.pdf"]	{NYC232}	2025-08-06 03:26:39.348232	\N	\N	f	t	<CAF7a8r1-6xWcLSQ0-Xx5h2hj7WNkRRbqWD+egMnKP38sikXTUw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:26:39.362014	\N	\N	\N	\N
80	Jething John <johnwongjething@gmail.com>	230	Payment for B/L  NYC230 Amount: $1600 Ref: TEST987\r\n	\N	{NYC230}	2025-08-06 03:34:23.120544	\N	\N	f	f	<CAF7a8r30CCRCoaMGARXSnCuK3D1eBs6Y4whkZziMdh6u0=sCZg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 03:34:23.133559	\N	\N	\N	\N
83	Jething John <johnwongjething@gmail.com>	234	Payment for B/L  NYC235, NYC999 Amount: $700 Ref: TEST987\r\n	\N	{NYC235}	2025-08-06 04:15:10.133069	\N	\N	f	t	<CAF7a8r0cX6Cx6jirZv6X+PeW16tD6j_Fvph-Wxep5GFo-1i6RQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 04:15:10.147504	\N	\N	\N	\N
84	Jething John <johnwongjething@gmail.com>	r	\r\n	["https://res.cloudinary.com/dtm46mski/raw/upload/v1754454088/email_attachments/lhmwd1whlv1ggbka4s3e.pdf"]	{NYC235,NYC234}	2025-08-06 04:21:28.539225	\N	\N	f	f	<CAF7a8r3jQ+g+uOFKGvzfGqB31itqtszb=5K_Y0mwQGFSmpcDjQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 04:21:28.554753	\N	\N	\N	\N
85	Jething John <johnwongjething@gmail.com>	343	Payment for B/L  NYC236, NYC237 Amount: $1700 Ref: TEST987\r\n	\N	{NYC236,NYC237}	2025-08-06 04:22:57.91055	\N	\N	f	t	<CAF7a8r3q7ZhMf9mb2Y7dW62xRj-QehprRAk99mhay8XXPCRftA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 04:22:57.92511	\N	\N	\N	\N
86	Jething John <johnwongjething@gmail.com>	f	can i have my invoice NYC240, NYC241, NYC242\r\n	\N	{NYC241,NYC240}	2025-08-06 06:35:55.303105	\N	\N	f	f	<CAF7a8r1fFtYRLdKg9Yggmnu0d7MbJ95ZuPG2tr+5GKkT7gVJKg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 06:35:55.31813	\N	\N	\N	\N
87	<ray6330099@9433503.brevosend.com>	Payment for NYC220		\N	{}	2025-08-06 08:23:55.558747	\N	\N	f	f	<202508060822.35026176139@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:23:55.570316	\N	\N	\N	\N
88	<ray6330099@9433503.brevosend.com>	CTN number for NYC221		\N	{}	2025-08-06 08:24:01.737061	\N	\N	f	f	<202508060822.61851095255@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:24:01.748833	\N	\N	\N	\N
89	<ray6330099@9433503.brevosend.com>	Invoice for NYC222		\N	{}	2025-08-06 08:24:06.974175	\N	\N	f	f	<202508060822.91519807810@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:24:06.987489	\N	\N	\N	\N
90	<ray6330099@9433503.brevosend.com>	Payment status NYC223		\N	{}	2025-08-06 08:24:12.143264	\N	\N	f	f	<202508060822.48036462725@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:24:12.154928	\N	\N	\N	\N
91	<ray6330099@9433503.brevosend.com>	General question		\N	{}	2025-08-06 08:24:18.662277	\N	\N	f	f	<202508060822.95214880012@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:24:18.673995	\N	\N	\N	\N
92	<ray6330099@9433503.brevosend.com>	Multiple shipments - NYC224, NYC225, NYC226		\N	{}	2025-08-06 08:24:23.676934	\N	\N	f	f	<202508060822.10695066944@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:24:23.688799	\N	\N	\N	\N
93	<ray6330099@9433503.brevosend.com>	Mixed language request - NYC227		\N	{}	2025-08-06 08:31:35.330896	\N	\N	f	f	<202508060822.83093894384@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:31:35.342433	\N	\N	\N	\N
94	<ray6330099@9433503.brevosend.com>	Weather and shipment - NYC228		\N	{}	2025-08-06 08:31:41.817826	\N	\N	f	f	<202508060822.26139087913@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:31:41.831499	\N	\N	\N	\N
95	<ray6330099@9433503.brevosend.com>	Partial payment and reserve - NYC229		\N	{}	2025-08-06 08:31:47.080916	\N	\N	f	f	<202508060823.92346636230@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:31:47.092513	\N	\N	\N	\N
96	<ray6330099@9433503.brevosend.com>	Various requests - NYC230		\N	{}	2025-08-06 08:31:53.305834	\N	\N	f	f	<202508060823.98222472998@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-06 08:31:53.317265	\N	\N	\N	\N
97	Jething John <johnwongjething@gmail.com>	t1	Dear IQS Trade,\r\n\r\nI need information for multiple shipments:\r\n\r\n1. NYC224: Payment status and CTN number\r\n2. NYC225: Invoice and tracking details\r\n3. NYC226: Reserve settlement amount\r\n\r\nPlease provide updates for all three shipments.\r\n\r\nBest regards,\r\nClient\r\n	\N	{NYC225,NYC226}	2025-08-06 08:37:09.648339	\N	\N	f	f	<CAF7a8r3HcpL-rR6CJcBWWeHDTHKuGia0eudeZmMijgLi6ck2=A@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 08:37:09.660029	\N	\N	\N	\N
98	Jething John <johnwongjething@gmail.com>	t2	Hello IQS Trade,\r\n\r\n请问NYC227的CTN号码是多少？\r\nCan you also send me the invoice for this shipment?\r\n\r\n另外，什么时候可以安排提货？\r\nWhen will the container be available for pickup?\r\n\r\nThanks,\r\n谢谢,\r\nClient\r\n	\N	{NYC227}	2025-08-06 08:37:16.50823	\N	\N	f	f	<CAF7a8r0Lk8=OMjEnY+Krsu2oBSjJPUECST2NPnc5Bf_3GAa4Jg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 08:37:16.51994	\N	\N	\N	\N
99	Jething John <johnwongjething@gmail.com>	t3	Hi IQS Trade,\r\n\r\nThe weather is really nice today!\r\nI hope you're having a good day.\r\n\r\nBy the way, I need the CTN number for NYC228.\r\nAlso, what's the current status of this shipment?\r\n\r\nHave a great day!\r\nClient\r\n	\N	{NYC228}	2025-08-06 08:37:22.93168	\N	\N	f	f	<CAF7a8r1iBGuwMAXH2WFKeL3GvK7WUxgePVkaKCm1BS=0m3EDpg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 08:37:22.943395	\N	\N	\N	\N
100	Jething John <johnwongjething@gmail.com>	t4	Dear IQS Trade,\r\n\r\nI have made a partial payment of $150 for NYC229.\r\nThe total amount is $200, so I still owe $50.\r\n\r\nCan you confirm the payment receipt?\r\nAlso, what is the reserve amount for this shipment?\r\n\r\nI will settle the remaining amount next week.\r\n\r\nThanks,\r\nClient\r\n	\N	{NYC229}	2025-08-06 08:37:28.544869	\N	\N	f	f	<CAF7a8r0+1FKxKEtPx+ZzbkZFx3RiN1LnCGT90SRGy60DbnUs4A@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 08:37:28.556671	\N	\N	\N	\N
101	Jething John <johnwongjething@gmail.com>	t5	Hello IQS Trade,\r\n\r\nI have several questions about NYC230:\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nAlso, I need to know about NYC231 and NYC232 as well.\r\n\r\nThanks,\r\nClient\r\n	\N	{NYC232,NYC231,NYC230}	2025-08-06 08:38:01.435664	\N	\N	f	f	<CAF7a8r2sJHea0Eu=wOMh2_sey7v_fhZ8vKJRQHxXL2PjSzVPaw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 08:38:01.448405	\N	\N	\N	\N
102	Jething John <johnwongjething@gmail.com>	t6	Hello IQS Trade,\r\n\r\nI have several questions about NYC230, NYC231, NYC232\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nThanks,\r\nClient\r\n	\N	{NYC232,NYC231,NYC230}	2025-08-06 09:02:59.982842	\N	\N	f	f	<CAF7a8r0CT_y+jiOWUYdrHRk2J5rdNKLLUQ=zEn5fuyYVc-ETpw@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 09:02:59.99655	\N	\N	\N	\N
103	Jething John <johnwongjething@gmail.com>	6	Hello IQS Trade,\r\n\r\nI have several questions about NYC230:\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nAlso, I need to know about NYC231 and NYC232 as well.\r\n	\N	{NYC230,NYC232,NYC231}	2025-08-06 09:22:28.963528	\N	\N	f	f	<CAF7a8r3VKUja8tO6GHcB_A4KhRzuHsuEM6TAdQd7yfguw=Pj=w@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 09:22:28.978253	\N	\N	\N	\N
104	Jething John <johnwongjething@gmail.com>	t7	Hello IQS Trade,\r\n\r\nI have several questions about  BL2024014\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nAlso, I need to know about  BL2024013 and  BL2024012\r\n	\N	{BL2024014,BL2024013,BL2024012}	2025-08-06 09:34:46.02871	\N	\N	f	f	<CAF7a8r2OM7_Wg263ht0XCwHccvJ7-0Gm-8x1YcyN1WSf6+zu7w@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 09:34:46.04373	\N	\N	\N	\N
106	Jething John <johnwongjething@gmail.com>	t11	Hello IQS Trade,\r\n\r\nI have several questions about NYC226:\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nAlso, I need to know about NYC227 and NYC228 as well.\r\n	\N	{NYC227,NYC228,NYC226}	2025-08-06 10:02:00.570127	\N	\N	f	f	<CAF7a8r2Hm-LzwS9FHEH7m32wsTBukmOwPq8jyBcMaFObX-G2sQ@mail.gmail.com>	\N	\N	f	\N	New	2025-08-06 10:02:00.586078	\N	\N	\N	\N
107	Jething John <johnwongjething@gmail.com>	questions	hi\r\n\r\ncan you please send me invoice for NYC 233 NYC234 NYC236\r\n\r\nwhat is the status of these BL\r\n\r\nhow can I settle the payment\r\n\r\nhow Long it takes to complete ctn process\r\n	\N	{NYC234,NYC236}	2025-08-08 00:26:18.64725	\N	\N	f	f	<CAF7a8r1NBJ4i0h9dhXnFKfTTYPSvSVWCekSP7j9nh4h2FXeaVg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-08 00:26:18.662403	\N	\N	\N	\N
108	Jething John <johnwongjething@gmail.com>	q1	hi\r\n\r\ncan you please send me invoice for NYC233 NYC234 NYC236\r\n\r\nwhat is the status of these BL\r\n\r\nhow can I settle the payment\r\n\r\nhow Long it takes to complete ctn process\r\n	\N	{NYC234,NYC236,NYC233}	2025-08-08 00:29:22.979507	\N	\N	f	f	<CAF7a8r0KWF07_pq6FqcLH+zftDRzUjoG=Q-50wKVzUw8EonGZg@mail.gmail.com>	\N	\N	f	\N	New	2025-08-08 00:29:22.993058	\N	\N	\N	\N
105	Jething John <johnwongjething@gmail.com>	t9	Hello IQS Trade,\r\n\r\nI have several questions about NYC226:\r\n\r\n1. What is the CTN number?\r\n2. Can you send the invoice?\r\n3. What is the payment status?\r\n4. When will it arrive at the port?\r\n5. How much is the reserve amount?\r\n\r\nPlease provide all this information.\r\n\r\nAlso, I need to know about NYC227 and NYC228 as well.\r\n	\N	{NYC226,NYC228,NYC227}	2025-08-06 09:38:35.442654	\N	\N	f	f	<CAF7a8r20K0UYfUadbbRH+wSOcc_W3ACUxmRATXTVVLu1oZjvqA@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-08 00:31:02.768532	\N	\N	\N	\N
109	Jething John <johnwongjething@gmail.com>	test12	hi\r\n\r\ncan you please send me invoice for NYC 233 NYC234 NYC236\r\n\r\nwhat is the status of these BL\r\n\r\nhow can I settle the payment\r\n\r\nhow Long it takes to complete ctn process\r\n	\N	{NYC236,NYC234}	2025-08-09 05:38:31.991364	\N	\N	f	f	<CAF7a8r2wqA0PQ+hBLbzSoz0fo+3Y1tRgGTRJJegFFZoDJPzTiA@mail.gmail.com>	\N	\N	f	\N	New	2025-08-09 05:38:31.998261	{ray633008@gmail.com}	{}	{}	\N
110	Jething John <johnwongjething@gmail.com>	r	can you please send me invoice for NYC 233 NYC234 NYC236\r\n\r\nwhat is the status of these BL\r\n\r\nhow can I settle the payment\r\n\r\nhow Long it takes to complete ctn process\r\n	\N	{NYC236,NYC234}	2025-08-09 07:55:34.767429	\N	\N	f	f	<CAF7a8r1XHSuF2EbwTxNpBYuJOmbWT8X4MG3VNGOAp6qyiLLS7g@mail.gmail.com>	\N	\N	f	\N	New	2025-08-09 07:55:34.781095	{ray633008@gmail.com}	{}	{}	{ray6330088@gmail.com,ykrw11@myyahoo.com}
111	"Logistics Company" <ray6330099@9433503.brevosend.com>	Re: r		\N	{}	2025-08-09 08:08:14.814235	\N	\N	f	f	<202508090756.35000981729@smtp-relay.sendinblue.com>	\N	\N	f	\N	New	2025-08-09 08:08:14.827503	{ray633008@gmail.com}	{}	{ray6330099@gmail.com}	{johnwongjething@gmail.com,ray6330088@gmail.com,ykrw11@myyahoo.com}
112	Jething John <johnwongjething@gmail.com>	r3	can you please send me invoice for NYC 233 NYC234 NYC236\r\n\r\nwhat is the status of these BL\r\n\r\nhow can I settle the payment\r\n\r\nhow Long it takes to complete ctn process\r\n	\N	{NYC236,NYC234}	2025-08-09 08:10:28.730445	\N	\N	f	f	<CAF7a8r1aOO1dUyn_BteaLs-m-otWJwCZp-QLWXh8apjbfjKE_A@mail.gmail.com>	\N	\N	f	\N	Replied	2025-08-09 08:11:04.37881	{ray633008@gmail.com}	{}	{}	{ray6330088@gmail.com,ykrw11@myyahoo.com}
\.


--
-- Data for Name: email_editing_locks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_editing_locks (id, email_id, user_id, created_at, expires_at) FROM stdin;
83	60	84	2025-08-06 02:16:32.390582	2025-08-06 02:26:32.390582
\.


--
-- Data for Name: email_ingest_errors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_ingest_errors (id, filename, reason, raw_text, created_at) FROM stdin;
22	C:\\Users\\MYACCO~1\\AppData\\Local\\Temp\\tmphf1b82s4.pdf	Payment amount mismatch or missing B/L (email body PDF)	Welcome to UI Bakery 🍩 - a visual internal tools builder tailored to save hours of development time!\r\n\r\n********************\r\nWelcome to UI Bakery\r\n********************\r\n\r\nHi ray ray,\r\n\r\nGlad to meet you at our UI Bakery platform 🍩 - a visual internal tools builder tailored to save hours of development time! We’re thrilled to have you!\r\n\r\nTo get you started, here are some key resources you might find helpful:\r\n\r\n* *Intro video* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFuPV3KNdSOedzw4ghkC6wZB29j9nhDrk0VnDdUR9kHK-2FT7F90khArAiwCcUR0ccijXmhpKT9HLVT7PjaZpuTxyzCvT0ozgzoctIZho2x9FAtDGNZrDzThAqPgu2vYMwU3w-3D-3Dzc6K_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkdXE1za223shLtvi-2Fud7ouO4tvcg7RIZQsu6FhsJuMQpruwhkG60zZvvqG3titk-2Bz34XGCkeB9CukBCp-2BRFqn7cADFTkiqmLiroIqy0vy7ebPmRaDbIaVhHabh9cJPJMsvrbQs4j8xD390g5ZRGcqe4-3D ) : Dive deep into our features\r\n* Check out the *Getting Started Guide* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFsPIW4b6VFLYmheg0GcRTbZJTQARovgx8o64twL1UDT4nU4W8hfec-2Bfj6CVrCYXv-2Bg-3D-3DGi-L_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkQMuzJWIF8UwScqJGQgDiu-2BR1Pw3zDffpKkqyApjEv0em3JTFGJrCztXixrgBfB2KLcRb6ttgdRJdLmbfEpBSaMwwJIePdnc9MoYpB4ZIfoGPXBHzK0pXspBFHlfpP72BI3eyClwBAubyHOSQMMoAJw-3D ).\r\n* Join our *Community* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFg66nNxgDHelqLyeeObCiCzuAhu7l4VNeHuleaMpScLaUxD2_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkUPU5j0q14WzrGhPObrGWZvUs1EjvTToflqmMS5Z75p-2FKv7RAOaGgy7UjovUp-2FVd6Znw3B6QsKLu99lsmNXTaIIlV3sH-2B-2B0BAkZDRbQ5R9bzB-2BdBBa25gmLsHpsbUER9XTXunJy0GuN5szjgMU2e7so-3D ).\r\n* Be the first to know about our releases by subscribing to our *Changelog* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFrbV-2B1Sndofo-2B-2BA-2BtCIVFBmx4iNxNTAQ1b8LD0JHTM5l5Elr_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkcPn-2B6mLvWu5u-2FpSDM01M-2FOUYT1tvu4yERPZxzhqn4WB1JvtOvZS8c-2FVM3HOBGMReczbyv-2FqI0NuG56ekD39yPuxlr4WYjyoiHcHkn-2FR46-2FJng1T7mRsPvGtJfl5tAB3ojByZsRFBSOMmbjlrtN-2B18s-3D ).\r\n\r\nIf you need any help, our support team is just a click away. Feel free to contact us in the live chat or at *support@uibakery.io* ( support@uibakery.io?subject=&body= ).\r\n\r\n- UI Bakery team\r\n\r\nLet's bake your first app! ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFtTIEfvDNKJlb-2B8GNGsVuM0nozZFxJPoW2zqEuFfHJ7w0IH0_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkWV26Fckgb2ZPojV5knaUBulADP20eh8c5Gs2zCL8mvsGhElhe9Z-2Fi28Nlt5sGjM0sX8iGWCRV41lb-2F53LLHhQUEuUM8-2BZHr2Poc9K4UyyArCCQchGBGj2leIID3iDRJ338Li0PocSlAVlV86lkI8J0-3D )\r\n\r\nUnsubscribe ( <%asm_group_unsubscribe_raw_url%> )	2025-07-22 07:29:31.869171+00
23	C:\\Users\\MYACCO~1\\AppData\\Local\\Temp\\tmpx1k81lb_.pdf	Payment amount mismatch or missing B/L (email body PDF)	Welcome to UI Bakery 🍩 - a visual internal tools builder tailored to save hours of development time!\r\n\r\n********************\r\nWelcome to UI Bakery\r\n********************\r\n\r\nHi ray ray,\r\n\r\nGlad to meet you at our UI Bakery platform 🍩 - a visual internal tools builder tailored to save hours of development time! We’re thrilled to have you!\r\n\r\nTo get you started, here are some key resources you might find helpful:\r\n\r\n* *Intro video* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFuPV3KNdSOedzw4ghkC6wZB29j9nhDrk0VnDdUR9kHK-2FT7F90khArAiwCcUR0ccijXmhpKT9HLVT7PjaZpuTxyzCvT0ozgzoctIZho2x9FAtDGNZrDzThAqPgu2vYMwU3w-3D-3Dzc6K_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkdXE1za223shLtvi-2Fud7ouO4tvcg7RIZQsu6FhsJuMQpruwhkG60zZvvqG3titk-2Bz34XGCkeB9CukBCp-2BRFqn7cADFTkiqmLiroIqy0vy7ebPmRaDbIaVhHabh9cJPJMsvrbQs4j8xD390g5ZRGcqe4-3D ) : Dive deep into our features\r\n* Check out the *Getting Started Guide* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFsPIW4b6VFLYmheg0GcRTbZJTQARovgx8o64twL1UDT4nU4W8hfec-2Bfj6CVrCYXv-2Bg-3D-3DGi-L_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkQMuzJWIF8UwScqJGQgDiu-2BR1Pw3zDffpKkqyApjEv0em3JTFGJrCztXixrgBfB2KLcRb6ttgdRJdLmbfEpBSaMwwJIePdnc9MoYpB4ZIfoGPXBHzK0pXspBFHlfpP72BI3eyClwBAubyHOSQMMoAJw-3D ).\r\n* Join our *Community* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFg66nNxgDHelqLyeeObCiCzuAhu7l4VNeHuleaMpScLaUxD2_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkUPU5j0q14WzrGhPObrGWZvUs1EjvTToflqmMS5Z75p-2FKv7RAOaGgy7UjovUp-2FVd6Znw3B6QsKLu99lsmNXTaIIlV3sH-2B-2B0BAkZDRbQ5R9bzB-2BdBBa25gmLsHpsbUER9XTXunJy0GuN5szjgMU2e7so-3D ).\r\n* Be the first to know about our releases by subscribing to our *Changelog* ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFrbV-2B1Sndofo-2B-2BA-2BtCIVFBmx4iNxNTAQ1b8LD0JHTM5l5Elr_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkcPn-2B6mLvWu5u-2FpSDM01M-2FOUYT1tvu4yERPZxzhqn4WB1JvtOvZS8c-2FVM3HOBGMReczbyv-2FqI0NuG56ekD39yPuxlr4WYjyoiHcHkn-2FR46-2FJng1T7mRsPvGtJfl5tAB3ojByZsRFBSOMmbjlrtN-2B18s-3D ).\r\n\r\nIf you need any help, our support team is just a click away. Feel free to contact us in the live chat or at *support@uibakery.io* ( support@uibakery.io?subject=&body= ).\r\n\r\n- UI Bakery team\r\n\r\nLet's bake your first app! ( http://url9994.uibakery.io/ls/click?upn=u001.2ht3Qf1a4-2FfJqk-2BZMouOFtTIEfvDNKJlb-2B8GNGsVuM0nozZFxJPoW2zqEuFfHJ7w0IH0_6PEJC-2BUeUuuG9DOtUwJeUQvfr2hjpYDu2iQQ4NQr-2Bzrc8UGkRT89OylGP9Md-2B-2FyhDrtLU0sESHwU-2FVRflbtTXzXP8bVTnHNBv7RsGoFWHwmAO6-2FP-2BgqF8pBxlWxc-2FJ3E55JDTrTUO8y81-2Fp411JtA70P0heBu9wp789-2FDImNyKwsyoEuFv7sWtipSeW774KB56Z1IoSR4kGyMyIUtPBKkWV26Fckgb2ZPojV5knaUBulADP20eh8c5Gs2zCL8mvsGhElhe9Z-2Fi28Nlt5sGjM0sX8iGWCRV41lb-2F53LLHhQUEuUM8-2BZHr2Poc9K4UyyArCCQchGBGj2leIID3iDRJ338Li0PocSlAVlV86lkI8J0-3D )\r\n\r\nUnsubscribe ( <%asm_group_unsubscribe_raw_url%> )	2025-07-22 07:29:31.870196+00
24	C:\\Users\\MYACCO~1\\AppData\\Local\\Temp\\tmp7a0gfxg9.pdf	Payment amount mismatch or missing B/L (email body PDF)	Payment for B/L NAM20\r\nAmount: $1000\r\nRef: TEST987\r\n	2025-07-22 07:55:24.860185+00
27	N/A	Invalid BL number(s) detected: 001-222	From: Jething John <johnwongjething@gmail.com>\nSubject: h6\n\nPayment for B/L  001-222\r\nAmount: $420\r\nRef: TEST987\r\n	2025-07-22 17:11:21.54183+00
28	N/A	Invalid BL number(s) detected: BL-12345, 678901	From: Jething John <johnwongjething@gmail.com>\nSubject: s1\n\nDear IQS Trade Team,\r\n\r\nI hope this message finds you well. Please find attached the payment advice\r\nfor our recent remittance.\r\n\r\nWe have transferred a total of USD $8,500 today, covering the following\r\nshipments:\r\n\r\n   - BL No: NYC22062889 (Container Fee: $3,000, Service Fee: $500)\r\n   - BL No: BL-12345 (Container Fee: $2,000, Service Fee: $300)\r\n   - Bill of Lading: 678901 (Container Fee: $2,500, Service Fee: $200)\r\n\r\nPlease note that for BL No: NYC22062889, we have already settled $1,000\r\nlast week (Ref: TXN998877), so the current payment is for the outstanding\r\nbalance only.\r\n\r\nHowever, for BL No: BL-12345, we noticed a discrepancy in the service fee\r\namount compared to your last invoice. Kindly clarify if the correct amount\r\nis $300 or $350.\r\n\r\nThe payment reference for today’s transfer is Ref: PAY0722A. The remittance\r\nwas made from our HSBC account and should reach you within 1-2 business\r\ndays.\r\n\r\nAttached is the bank advice in PDF format. If you require any further\r\ndocumentation or clarification, please let us know.\r\n\r\nThank you for your prompt attention to this matter.\r\n\r\nBest regards,\r\nJane Lee\r\nAccounts Payable\r\nAcme Logistics Ltd.\r\n	2025-07-22 17:43:22.170611+00
\.


--
-- Data for Name: email_processing_locks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_processing_locks (id, user_id, created_at, expires_at) FROM stdin;
\.


--
-- Data for Name: email_prompt_locks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_prompt_locks (sender_id, locked_until) FROM stdin;
85265381629@s.whatsapp.net	2025-07-23 08:36:41.979494
\.


--
-- Data for Name: fcm_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fcm_notifications (id, email_id, notification_type, sent_at, created_at) FROM stdin;
1	53	new_email	2025-08-01 18:53:48.80223+00	2025-08-01 10:53:45.706612+00
2	54	new_email	2025-08-01 18:56:17.498262+00	2025-08-01 10:56:14.800782+00
3	55	new_email	2025-08-01 19:06:21.556562+00	2025-08-01 11:06:17.58807+00
4	56	new_email	2025-08-01 19:06:40.913966+00	2025-08-01 11:06:37.281194+00
5	66	new_email	2025-08-02 12:46:53.623672+00	2025-08-02 12:46:53.138555+00
6	67	new_email	2025-08-03 06:18:21.397771+00	2025-08-03 06:18:18.775242+00
7	68	new_email	2025-08-05 11:37:29.208507+00	2025-08-05 11:37:26.345833+00
8	69	new_email	2025-08-05 11:40:02.071433+00	2025-08-05 11:39:59.111501+00
9	70	new_email	2025-08-05 11:42:03.990236+00	2025-08-05 11:42:01.101039+00
10	72	new_email	2025-08-06 02:32:18.239318+00	2025-08-06 02:32:15.54678+00
11	73	new_email	2025-08-06 02:51:53.508396+00	2025-08-06 02:51:50.839672+00
12	74	new_email	2025-08-06 02:54:15.317375+00	2025-08-06 02:54:12.632452+00
13	75	new_email	2025-08-06 03:03:37.267041+00	2025-08-06 03:03:34.371127+00
14	76	new_email	2025-08-06 03:04:28.413615+00	2025-08-06 03:04:25.77192+00
15	77	new_email	2025-08-06 03:08:27.39395+00	2025-08-06 03:08:24.844924+00
16	78	new_email	2025-08-06 03:24:32.299+00	2025-08-06 03:24:29.650771+00
17	79	new_email	2025-08-06 03:26:58.503336+00	2025-08-06 03:26:55.652446+00
18	80	new_email	2025-08-06 03:34:36.11825+00	2025-08-06 03:34:33.488875+00
19	81	new_email	2025-08-06 03:47:10.514079+00	2025-08-06 03:47:07.677185+00
20	83	new_email	2025-08-06 04:15:20.89181+00	2025-08-06 04:15:18.081276+00
21	84	new_email	2025-08-06 04:21:55.787673+00	2025-08-06 04:21:52.865874+00
22	85	new_email	2025-08-06 04:23:10.290081+00	2025-08-06 04:23:07.320469+00
23	86	new_email	2025-08-06 06:36:02.00623+00	2025-08-06 06:35:59.063626+00
24	87	new_email	2025-08-06 08:24:01.505841+00	2025-08-06 08:23:58.669832+00
25	88	new_email	2025-08-06 08:24:06.747803+00	2025-08-06 08:24:03.813726+00
26	89	new_email	2025-08-06 08:24:11.930621+00	2025-08-06 08:24:09.297068+00
27	90	new_email	2025-08-06 08:24:18.433194+00	2025-08-06 08:24:15.639846+00
28	91	new_email	2025-08-06 08:24:23.4508+00	2025-08-06 08:24:20.711135+00
29	93	new_email	2025-08-06 08:31:41.571063+00	2025-08-06 08:31:38.228066+00
30	94	new_email	2025-08-06 08:31:46.841072+00	2025-08-06 08:31:43.684059+00
31	95	new_email	2025-08-06 08:31:53.077336+00	2025-08-06 08:31:50.216811+00
32	96	new_email	2025-08-06 08:31:59.674267+00	2025-08-06 08:31:56.188153+00
33	97	new_email	2025-08-06 08:37:16.285926+00	2025-08-06 08:37:13.828142+00
34	98	new_email	2025-08-06 08:37:22.698857+00	2025-08-06 08:37:20.328402+00
35	99	new_email	2025-08-06 08:37:28.334801+00	2025-08-06 08:37:25.898758+00
36	101	new_email	2025-08-06 08:38:07.594005+00	2025-08-06 08:38:04.897701+00
37	102	new_email	2025-08-06 09:03:06.381778+00	2025-08-06 09:03:03.522447+00
38	103	new_email	2025-08-06 09:22:36.047158+00	2025-08-06 09:22:33.415462+00
39	104	new_email	2025-08-06 09:34:51.855882+00	2025-08-06 09:34:49.503299+00
40	105	new_email	2025-08-06 09:38:42.778836+00	2025-08-06 09:38:39.393428+00
41	106	new_email	2025-08-06 10:02:12.080146+00	2025-08-06 10:02:08.933362+00
42	107	new_email	2025-08-08 00:26:27.424077+00	2025-08-08 00:26:26.759764+00
43	108	new_email	2025-08-08 00:29:32.017877+00	2025-08-08 00:29:31.252154+00
44	109	new_email	2025-08-09 05:38:38.450979+00	2025-08-09 05:38:37.717812+00
45	110	new_email	2025-08-09 07:55:40.852491+00	2025-08-09 07:55:40.217511+00
46	111	new_email	2025-08-09 08:08:18.05796+00	2025-08-09 08:08:17.526057+00
47	112	new_email	2025-08-09 08:10:37.742237+00	2025-08-09 08:10:36.969152+00
\.


--
-- Data for Name: fcm_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fcm_tokens (id, user_id, token, created_at, updated_at, is_active) FROM stdin;
5	\N	fTp9k8GIumfk5o827m3Jnz:APA91bFldEWo6eqe_nc8Cpy8U8yYDi8y5ljGasfRUW4PysGcp0ljO2MVpcwtulQ5eV81otmgffJEzmW_-sEygJi4Ar_0FVnfnXgCHLk1VeSUqotMEBM5QwY	2025-07-31 12:32:49.057934+00	2025-08-01 01:37:42.98915+00	t
12	107	dCiHT_rn02j9QLv06ofwNP:APA91bFgO3s6GgmCXB76nO9dzsPZ3xnF591KK1QyVGkp-TxIGigMsvLzPRr1uHZvtw9stRTGdeTZFYaV36dEVLSPXWVI6_Ud4ast2rihOLDbKrqrUJg24Go	2025-08-03 03:08:02.549629+00	2025-08-03 03:24:28.796898+00	t
6	84	cOIbVI9RTkVhaXy-ZNIWNC:APA91bH4vodhjcVsmoETUbuTVPXHHcU9dHzqvgSw4qUV1dYji5sOktxgvd7IAythCQkIFIaB0F7dVAtJ5tXggxuCfe9zNPCUpStB2ZT3R6XLjyL6nli3KXc	2025-08-03 02:38:51.662094+00	2025-08-03 02:38:51.662115+00	f
7	107	ePh-dsdhvZRZNH4Y4JsTCu:APA91bF7DRJlEvJmOxLjA80nv5g7FpxstSfPfM2EmKlNopvKCs6KQxl5o5dw-NDylS3T3iLA5MyjqFDi3HwBfSceiNj4rjAko-w4TBjZDG63HfPy70WofYY	2025-08-03 02:40:03.458941+00	2025-08-03 02:40:03.458963+00	f
8	107	cwQUMYNBDjmT4gMJ69mz0z:APA91bG7MSiJARjZmC906HNW6gsSoAbrB2XEhFXM1yjM6H83zV_Y7o8McNtZkQO4KhIvxtENhXN4GcvgRBcS93nC-Mzibu0PGsDz2_K-Y44Evr-Mt8juAxU	2025-08-03 02:41:49.557363+00	2025-08-03 02:41:49.557384+00	f
9	107	f6Yz_Jtj8UL3v7ZLNNMBXP:APA91bGWFu4LrP1W8DoL7EgTGStMKwQE_VifMISOCmQWcLcutJFEtWxbJkJCT_k4LHivjrdhlPRF1vXA0nRK4xYPztgBfyyZuzmv5G_kYq8hO7_BKqRjsWM	2025-08-03 02:43:18.913677+00	2025-08-03 02:43:18.913701+00	f
10	107	fwoGK_G_0k98i34SfBEEvk:APA91bH_rV-j_8l8wot6AqZO53EhPTFNe0rPmXX4TbR-5pw0jTLFMnQqLb2KG4YodNL2pbCeFiXEbceeR23mPxp74A8ErykSb9Ias9nBNm3cf9QO_eVQnpg	2025-08-03 03:01:46.268386+00	2025-08-03 03:01:46.268406+00	f
11	107	c7plZwvkoFiykftJACK8ui:APA91bHFcwXUjWIMsdQD12Fpp80l0K6LhHadhpwLrMAePcvI2vv-WB_zld0fZJiKP-2curYmqlP-5FAOmyBV1YlgyGaPvCppSOcXvni-GZtjvIft5gREKfE	2025-08-03 03:07:25.904481+00	2025-08-03 03:07:25.904498+00	f
13	84	fYpNTSJUj7aTgco31Vwkz9:APA91bH5YlgwR0CfR__2E_s6mQimnYV_zjV161RjqHpvPntHWE3GHzSOmnJPWRIKEzpcROmN3qklZBuO8FV5zJ-F_DvSostBbxr8wrr9-IAG3fFCKMdhFak	2025-08-04 09:25:05.074572+00	2025-08-04 09:25:05.074595+00	f
\.


--
-- Data for Name: outlook_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.outlook_sessions (id, user_id, session_token, created_at, last_activity, is_active) FROM stdin;
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.password_reset_tokens (id, user_id, token, expires_at) FROM stdin;
31	47	k2dnnjMhPtJ9texsWqyLXJdsw0_2wxI4KrHxrNfkxtw	2025-07-13 14:45:39.217653+00
32	26	xNgoJBB7p3133ovWNXWFspWElCRFZ7-FtZIuoKomkIA	2025-07-13 14:47:04.975255+00
33	74	q_5LJzgUqw7UAKRpDPeMhPxE4lGTYTnjJB6fhH3qF6c	2025-07-14 09:06:56.766418+00
34	74	uGLajtHi0TKiEvPePHH2U4LMNR8woSexBUMgBelqBYw	2025-07-14 09:34:39.653025+00
35	74	P4eJ0EDhm_UHKB4xiI8cTg3pjo-QDK6NeluD1XDilMs	2025-07-14 09:43:18.986144+00
36	74	GAmnqgFlvWjGrQ1sHU4F7iNucqdcFhhaYGxV7_ehYVg	2025-07-14 09:55:42.054152+00
37	45	1u0Q-qcw9PZqBHk20XBkbK1_ajx5RH1Pugadv8WsXpE	2025-07-16 12:45:48.873771+00
38	45	6O-E4S-WRk1rQcxvCwGlkxBlfWd6BeZ77khvRNS1LpA	2025-07-16 13:11:42.436044+00
39	45	UYEwLihdQ8unpf3a4mAqLzHPzljmyK3c-64pWQYMWTg	2025-07-17 04:05:05.06315+00
40	45	R37CDasNok36c4OWaO_tFEWPqrXP-Epdi6H0X-vMeLo	2025-07-17 04:16:07.349158+00
41	45	PZqO4Ib5WJ_KEAGLRvCuoDG9v8laa-KDsl2M3VGuLcE	2025-07-17 12:07:01.579806+00
42	45	u3Q5QEynwu2oZlsV1NWACeCD_sF77pVjmXDvbM4XDerZOF06v57b6QXW7eUbb79_	2025-07-18 11:14:17.293706+00
43	26	lCBxAKjOZkinkITvGhq9qbDRz7DcEqaTJq4qhBNXUPltz_39Et1yGa3bYyE9FZ5P	2025-07-19 04:59:05.163563+00
44	45	dCcn-nQzLITYCTGmQ5TFkvizpdHrCT1c1-mxHpqr4k54UVocsKZWCQgRbtcWNKoQ	2025-07-19 07:38:50.602373+00
45	45	mkc68jOcuKO7jdCf4Pq4Zoq6K1zFbY3XJA0ww8-DZ9vMbxJHllmTx8XZKs4lH5jN	2025-07-19 08:09:12.881697+00
\.


--
-- Data for Name: pricing_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pricing_config (id, shipment_type, container_type, pricing_method, ctn_fee_per_unit, service_fee_per_unit, unit_type, minimum_charge, maximum_charge, is_active, created_at, updated_at, created_by, notes) FROM stdin;
1	ocean	20ft	container	150.00	200.00	container	350.00	\N	t	2025-07-28 04:41:02.961844+00	2025-07-28 04:41:02.961844+00	system	Standard 20ft container pricing
2	ocean	40ft	container	200.00	300.00	container	500.00	\N	t	2025-07-28 04:41:02.961844+00	2025-07-28 04:41:02.961844+00	system	Standard 40ft container pricing
3	ocean	40ft_hc	container	250.00	350.00	container	600.00	\N	t	2025-07-28 04:41:02.961844+00	2025-07-28 04:41:02.961844+00	system	High cube 40ft container pricing
4	air	\N	weight	1.00	1.50	kg	150.00	\N	t	2025-07-28 04:41:02.961844+00	2025-07-28 04:41:02.961844+00	system	Air freight per kg pricing
5	loose_cargo	\N	weight	0.50	0.75	kg	100.00	\N	t	2025-07-28 04:41:02.961844+00	2025-07-28 04:41:02.961844+00	system	Loose cargo per kg pricing
\.


--
-- Data for Name: pricing_overrides; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pricing_overrides (id, bill_of_lading_id, original_ctn_fee, original_service_fee, new_ctn_fee, new_service_fee, reason, overridden_by, overridden_at, notes) FROM stdin;
\.


--
-- Data for Name: test123; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test123 (id) FROM stdin;
\.


--
-- Data for Name: unmatched_receipts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.unmatched_receipts (id, date, description, amount, reason, created_at, raw_text) FROM stdin;
1	2025-07-22	Email from Jething John <johnwongjething@gmail.com> - Subject: h6	420.00	Invalid BL: 001-222	2025-07-22 17:11:22.520723+00	Payment for B/L  001-222\r\nAmount: $420\r\nRef: TEST987\r\n
2	2025-07-22	Email from Jething John <johnwongjething@gmail.com> - Subject: s1	8500.00	Invalid BL: BL-12345, 678901	2025-07-22 17:43:23.171789+00	Dear IQS Trade Team,\r\n\r\nI hope this message finds you well. Please find attached the payment advice\r\nfor our recent remittance.\r\n\r\nWe have transferred a total of USD $8,500 today, covering the following\r\nshipments:\r\n\r\n   - BL No: NYC22062889 (Container Fee: $3,000, Service Fee: $500)\r\n   - BL No: BL-12345 (Container Fee: $2,000, Service Fee: $300)\r\n   - Bill of Lading: 678901 (Container Fee: $2,500, Service Fee: $200)\r\n\r\nPlease note that for BL No: NYC22062889, we have already settled $1,000\r\nlast week (Ref: TXN998877), so the current payment is for the outstanding\r\nbalance only.\r\n\r\nHowever, for BL No: BL-12345, we noticed a discrepancy in the service fee\r\namount compared to your last invoice. Kindly clarify if the correct amount\r\nis $300 or $350.\r\n\r\nThe payment reference for today’s transfer is Ref: PAY0722A. The remittance\r\nwas made from our HSBC account and should reach you within 1-2 business\r\ndays.\r\n\r\nAttached is the bank advice in PDF format. If you require any further\r\ndocumentation or clarification, please let us know.\r\n\r\nThank you for your prompt attention to this matter.\r\n\r\nBest regards,\r\nJane Lee\r\nAccounts Payable\r\nAcme Logistics Ltd.\r\n
3	2025-08-05	Email payment for BL NYC225	100.00	Underpayment: Expected $200.0, Paid $100.0	2025-08-05 11:37:22.07342+00	Email from Jething John <johnwongjething@gmail.com>: ry
4	2025-08-06	Duplicate payment for BL NYC226 from ray40	800.00	Duplicate Payment: Payment of $800.00 already processed (Original: 2025-08-05 11:39:55)	2025-08-06 02:51:42.239624+00	Duplicate payment detected for BL NYC226 via email. Customer: ray40
5	2025-08-06	Email payment for BL NYC229	83.33	Underpayment: Expected $350.0, Paid $83.33333333333333	2025-08-06 03:03:29.630639+00	Email from Jething John <johnwongjething@gmail.com>: hh
6	2025-08-06	Email payment for BL NYC230	416.67	Underpayment: Expected $675.0, Paid $416.6666666666667	2025-08-06 03:04:21.746799+00	Email from Jething John <johnwongjething@gmail.com>: jj
7	2025-08-06	Duplicate payment for BL NYC230 from ray40	625.00	Duplicate Payment: Payment of $625.00 already processed (Original: 2025-08-06 03:04:22)	2025-08-06 03:08:16.33036+00	Duplicate payment detected for BL NYC230 via email. Customer: ray40
8	2025-08-06	Email payment for BL NYC231	200.00	Underpayment: Expected $350.0, Paid $200.0	2025-08-06 03:24:25.152318+00	Email from Jething John <johnwongjething@gmail.com>: kg
9	2025-08-06	Email payment for BL NYC232	133.33	Underpayment: Expected $350.0, Paid $133.33333333333334	2025-08-06 03:26:51.125329+00	Email from Jething John <johnwongjething@gmail.com>: ssf
10	2025-08-06	Duplicate payment for BL NYC230 from ray40	1600.00	Duplicate Payment: Payment of $1600.00 already processed (Original: 2025-08-06 03:04:22)	2025-08-06 03:34:26.978678+00	Duplicate payment detected for BL NYC230 via email. Customer: ray40
11	2025-08-06	Email payment for BL NYC233	350.00	Underpayment: Expected $675.0, Paid $350.0	2025-08-06 03:47:03.009393+00	Email from Jething John <johnwongjething@gmail.com>: hsgs
12	2025-08-06	Duplicate payment for BL NYC235 from ray40	700.00	Duplicate Payment: Payment of $700.00 already processed (Original: 2025-08-06 04:15:15)	2025-08-06 04:21:41.226038+00	Duplicate payment detected for BL NYC235 via email. Customer: ray40
13	2025-08-06	Duplicate payment for BL NYC234 from ray40	700.00	Duplicate Payment: Payment of $700.00 already processed (Original: 2025-08-06 04:06:59)	2025-08-06 04:21:47.124245+00	Duplicate payment detected for BL NYC234 via email. Customer: ray40
14	2025-08-06	Duplicate payment for BL NYC229 from ray100	150.00	Duplicate Payment: Payment of $150.00 already processed (Original: 2025-08-06 03:03:30)	2025-08-06 08:37:33.494324+00	Duplicate payment detected for BL NYC229 via email. Customer: ray100
\.


--
-- Data for Name: user_activity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_activity (id, user_id, current_email_id, current_action, last_activity) FROM stdin;
2	84	\N	\N	2025-08-09 08:11:05.453039
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password_hash, role, approved, customer_name, customer_email, customer_phone, failed_attempts, lockout_until) FROM stdin;
4	admin	123456	staff	t	\N	\N	\N	0	\N
11	eee	eee	customer	t	\N	\N	\N	0	\N
12	fff	fff	customer	t	\N	\N	\N	0	\N
13	vvv	vvv	customer	t	\N	\N	\N	0	\N
14	www	www	customer	t	\N	\N	\N	0	\N
15	ee	ee	customer	t	\N	\N	\N	0	\N
18	aaaa	aaa	customer	t	\N	\N	\N	0	\N
20	ttt	ttt	customer	t	lok tung	lok@lok.com	666	0	\N
21	iii	iii	customer	t	lok	lok@lok.com	667	0	\N
23	ppp	ppp	customer	t	ppp	a@a.com	333	0	\N
22	ooo	ooo	customer	t	LA TROBE UNIVERSITY	iaa@g.com	3333	0	\N
24	lll	lll	customer	t	lll	lok@lok.com	888	0	\N
25	hhh	hhh	customer	t	hhh	a@a.com	222	0	\N
28	bbbb	bbb	customer	t	bbb	b@b.com	656	0	\N
29	bbbbb	bbb	customer	t	bbb	b@b.com	787	0	\N
30	sandy	sandy	staff	t	sandy	a@a.com	111	0	\N
31	ffff	ffff	customer	t	ffff	a@a.com	111	0	\N
32	sandykong	1234	customer	t	miao miao compay	fishball@gmail.com	0491345678	0	\N
33	cccc	cccc	customer	t	ccc	a@a.com	222	0	\N
34	ggggg	ggggg	customer	t	gggg	a@a.com	222	0	\N
37	qqqqq	scrypt:32768:8:1$EFY1RMwcExPguj5D$dfcbb238dae75d460758316186183c21c9fa5d85a4aa04065e2ac223621fc038319b04d8a7f3405e40b73e93e77d1e9a651e7bf77a83e40ff180a365ce55bc5c	customer	t	qqqqq	a@a.com	12345	0	\N
40	sssss	scrypt:32768:8:1$chq7T9cokGEYSnM1$944abac0fc898050a1045e95621a7574defba0376da740513ecee58edaa1fe7b7673d9e97ebb24f1a3ae2f8843750107e8cd9a1d2379aa75b3f5c375c88e96ef	customer	t	sssss	a@a.com	111	0	\N
41	kkkkk	scrypt:32768:8:1$AGicFldG3dajOwsH$fd8c1a2009a0141f2e77954898ae007061928e6b02b89b053f5121b17336da95a33f2288435bf4a7364cb0bcb4420bca378ecfb8340fffa9450130a4058ad57b	customer	t	kkkk	a@a.com	111	0	\N
42	kkkk	scrypt:32768:8:1$J7bZTi62uL7quYwJ$d2fc4eab304ef4a61d7109abf2fa87fa6720edc4b37c169d400ca5ef56a130b8c91468d6b915fda2f17fbdc10e5f12b1b3f7bb7b765ca71b7068672002bc8a99	customer	t	kkkk	a@a.com	6666	0	\N
44	wong	scrypt:32768:8:1$8Lap75jCWj9oIAnD$92045e141c2815aa21fc9512415dd4cafb68886d750374fb8e83b79dbd2383e51a7bef21548b8898ca7960504f73977a5695ca73534b1b361ef03ded0b949ba8	customer	t	ying kit	a@a.com	111	0	\N
49	hhhhh	scrypt:32768:8:1$x1o1DPlu0jLZcb9P$5a725ab3f09354a8968e64ecd382ddc4f3229d7d8939e6e5988173e2b2040e65ab6721b56fcd03791d24ee0aab94bfe197f93afd16483031d532a2677d0a77a6	customer	t	cat	sandykong327@yahoo.com.hk	334	0	\N
47	ray ray	scrypt:32768:8:1$xGUteAlH2fAR29Ap$ec3b6a24e294835c360e64aa73634ba30b681714ceb3e6713507a841f2c717d5a08de49db2c632a6352f9a3257e9002d0b6874593f1cbb12a901dc73fd3494d6	customer	t	ray company	ray633008@gmail.com	6538	0	\N
48	yes	scrypt:32768:8:1$WIPcKslZTpT2AJYc$522520ae7d61c2611f88a045ab1eb907daac806dc7fb77df72fe42c53a077f8d6d00ae4b189f0d506f912ca36bafd8b8bc235d30f0286eed239ebfdc570eba18	customer	t	yes yes con	ray6330099@gmail.com	999	0	\N
50	ray1	pbkdf2:sha256:600000$UrbsfK2seSI8by0F$7ad907976fbbcbda0778553d92469d3136033bcfa3d1973f32485bb348b8dbaa	customer	t	ray	gAAAAABoUzuuu5FgY0ss5dWVDwzTa5ZTOCwq7goqn6uSrKRxGGnGA6VStrbR_L5B29sT4rwgAFMxewX3SsV5CLgHGPMqB2Et0zDgbzIidSBfr0l4nn8TSnw=	gAAAAABoUzuuTiGbAYw6hlg5OfRiRz6-1swzgYp2OGW96cO_QDub4mqCYoruLXaHox3CwAemqOZwS8tpHIN6Y5qEuRQU0Pd1Cw==	0	\N
52	ray3	pbkdf2:sha256:600000$diOw7vf1pIyyR1Bp$987e54f732834f76bb59bb60dabe362b15c9553bb4e233abae0901bb5b31ce08	customer	t	rayray	gAAAAABoU2xA8SMiS7kVGhpNRDO1H4DCKzqnRy_yFkSPHU6fIr0iF29vILusFxtRP9F4IOInSFenlXz_XcuIdYDHlEAAQDU8Wutf8XN3ZOIn5vHCIgKmD-I=	gAAAAABoU2xAcxb83whNtgL7yPz8wdAcHttPYt0hsCOunUk7mNDyZMIgWvmMQkUCyp_9EvHsIbhMm__zq8p_MB82Z9AX6fQfcg==	0	\N
51	ray2	pbkdf2:sha256:600000$yKAZtPYS0MqE1QLj$35a5c4ba198ef27b228b1c1063d28a10e2dc749e1f0cfb6f0574ba4e1a4dca6c	customer	t	ray	gAAAAABoU2RLcneLqLYuITDks_uWnMxGwbMFcZkEWw9it3Y5c1-9x_FUarIA1iLeNdQ478UX7pVLQp0kyDSDdgA7A5IoxqrxmYhGeVLz3mpUCOxVM5kilLY=	gAAAAABoU2RLNnmguwD9I_q9kY9f5qaLprBfsxjm-Lzr9g_Snzdc3njXUZaOYysDt6CiupgRfBgKnBFCBso5oqb7T4LbTFzqcw==	0	\N
53	ray5	pbkdf2:sha256:600000$0YfqZ59qVQzVA8na$fc7d2a931c65d5d0b3a98f099191fb27864d249605c583e17c8090d4b3f87cd0	customer	t	rayy	gAAAAABoU3AJAww1x4k0y5Thq2f16J603jNU5nPi7VlgGzi9_a6Zg-qZwf9f6qcyVy6Imx3XmCPkhRSD4PnRSW_tDdn_3OIuqftP9x32ndR12JRTNDBLMYE=	gAAAAABoU3AJLerOh8jYFkuU_a6LNrDFjAtWMqyW-cDcIgDrIq92YUiq7GVk9EqgSB-E4NjJvzmo05LkiOjhCcODOnm5NuXXpQ==	0	\N
54	ray6	pbkdf2:sha256:600000$FeUpdMaoHtHYxB3L$5f03a04bbd500b3b3654cd6e35d931795859c4b5400985872b9111de65b6ebe9	customer	t	ray	gAAAAABoU3so6aKs3xcUC7Ru9ZC9jC7pxUX_CRyLRuR1pUghje3qQ9G-uzMZj0WAOeme-8pV-cKyX-u7U2B-CcESQI6LKtnDfJ__pKIrGKBc5E84JZJTHR8=	gAAAAABoU3so71y2tWHWRjI0bBiDoyQQnsAGlJCcj_dR-tB-MMneI5fnlHB_G-pAfCzIZTYF5zROQQgx4tmmjUzPbYbIr0rSTg==	0	\N
56	ray8	pbkdf2:sha256:600000$xn3KcRyg0dtXLh2o$62ecb47004dc1178c59ab8a4535531abba0ba09109ce48d054cb4bdbcd5e9931	staff	t	wongwong	gAAAAABoU3wCG9W7LzvRtuDbVojicBGnaS_bt586-wjjluz_HwV2x9FZFq8rdNd86n33FQ8jHRfjN7gfbh-TrPHrnlZGU2hUOJ3aU8YOOklknPSb_kBw918=	gAAAAABoU3wCLosKYIEAGyTkWwaAtja_4c48ouK55qrr2yRgRl_AsknCIqsdzznp1oxv6oGqV9MymSL0eEBL8lm9MSedYGDExg==	0	\N
26	xxx	pbkdf2:sha256:600000$eieiu5wQ1Gyoh3ta$6816b5537c2f0e878db31e613b463ee37ffe162fdbc10e2f5f41e2b0ac96cbbb	customer	t	Ray	ykrw11@gmail.com	567	0	\N
55	ray7	pbkdf2:sha256:600000$Ebbp6IK6HpyTIRuH$865baca9f1154c4f74657f81c9629dbb4778af60b2e403a7bd4f0eb900c2d07d	customer	t	wongying	gAAAAABoU3vqklpQUJ7D_fsxGhSOQNeXvkRCCTlWlU4sE0T1_JrMe0UNZZOavO0E0QoZvLSfQSmshhBsBZHSBuHf0d72bWyOWZpLbiasYxCxwHCmUfipOeE=	gAAAAABoU3vqk0jqPTnNki7RxdbM0pD5czj4f91nYhcZo1tXcOTVuEhXUF0hkyLo95rxcya40MUZR-jInitIi_hOlO02GMDwVw==	0	\N
39	abcabc	scrypt:32768:8:1$XfVH8LiaMvBDQoy1$43ba1e4e37a410095b8474e268fdb1d08889dac5fda79dc5f905163f17fa83f2167844ba61e829a5ce6971e9813bdf7782146d5c90ac99491a303f2fb5f7e81a	staff	t	Admin	admin@example.com	1234567890	0	\N
57	ray9	pbkdf2:sha256:600000$m1SO7rSjP5RpcJf5$fcb20a09ab7d7d1a9f89803f68d768852c5e8c6132e3602b5e44731ddb37f586	customer	t	rayw	gAAAAABoU4Kw7GDIuSMcCQw4QFyNFxqyQGyndu8lGbJ3su-u22tUR2Jgj9zWgNVD2Fa_uXgeko_n41OjZKLh7BJymG_1dfz19P0SUxnYDNUiCFAk_a8-zck=	gAAAAABoU4KxLC-3WloULyyD9xEprvumHud0YcdB52ZcKN65XXFb6b8-U_9fuSPtMS8Fu-JY-QOVGVMNYDu-7lnfkXEPm3nnqg==	0	\N
60	ray10	pbkdf2:sha256:600000$b6cMv14wRe6pPAlr$0cdf252199ce2c54ca3dbd0969081bb025f7bb82870380da5ce8922b00ca184d	customer	t	rayj	gAAAAABoU4lWrguFaZFehNbGTrpvX_vp9hO8t7JI-1DEBTqY7NmiPWD_I-OOgbBrWzWygcVCAf-zzkeRr8qkoRgEHkBoqtc1-fM5nEN3AmldDFyOVhviWeY=	gAAAAABoU4lWS3oEpFHdjC790-lKn0M7pTqRRBdhEEI5t7bEEQdvuzZpPAmP3OaLWuAyEu5mp9yT-k02I0OcoksrHSqhVEbzgA==	0	\N
61	ray12	pbkdf2:sha256:600000$RiCbUozKMF0llbow$106bafb19fb6750469359f3210e41e1611c68fd3dcae39101767988d05420c97	customer	t	wongyy	gAAAAABoU4vanrA0sp-LoEGzTNQbbtbH35qoCRT4QkjKEI8GDzwTh5ASps9O8QX0KkLdYHJHTUIXNyJ2zD1EPTvbwsH8_LLlNvBE3QNgGSd5Kb8xEa_0SvY=	gAAAAABoU4vaOVSetiWFLDeJfGqHDYlDOptLOCpHZlH_JPnXoMPRfKZO8I0vaAE88GOV2EXhiZevSaAXDrrz8mySJF34zyVyRQ==	0	\N
62	ray13	pbkdf2:sha256:600000$Ayv8knIGHBqMIQqW$eec90476e54a175343ccbcd21d9fdd39d5745a08cdd970e4be4d3133a24f5cf5	customer	t	rayray	gAAAAABoU51sJR6EmRx9sPUDL4qQn0Hcp-e1C06ItOCAgFzGGcV8PdoSwh0rEj4G5hvMbWBrnR5ZkdYsMxqZWqxH_RvyfktQsWBBJB0gTeNGn1bNs4gBC1M=	gAAAAABoU51sxFyS7p1N0XPd7Jx2fxM_GsDv5qrga3y1z2CPF7_JZU0RHnA_WL8XAvEgM6_tpVJ8--VtokDLfEi48epZvJdsgA==	0	\N
63	ray14	pbkdf2:sha256:600000$8u4BcZQHMOMHp31l$29805900f817b3d500fb4cd56c9210acbba322bd9f31c9eb319188796c93cd4b	customer	t	ray2	gAAAAABoU52CpgKLE_nEC_Lc1xNSqwqlW8XaWuA8dGqurGSmE33jCgitHaA-Ly1dfep1rXvNftJqs_vRv6P6_77Qo2XJihvuLwITM9NhDHCMqdbYp4UU65k=	gAAAAABoU52CJEhHmxLVekz4FlXNrUtIVh0RDcwOumDHkF61puHEM2FAMpKngeSrhUUmLPMouGyylp5s6GeFUFaLr780WAFKZQ==	0	\N
64	ray15	pbkdf2:sha256:600000$cNAvjxIt3Iv3bYQW$809d66d30086ec5d4ae45bb9cc6d0bfac8cf96cacb763ccd2c689b30906d09d4	customer	t	ray4	gAAAAABoU52l7n8EVTikoLW3r_GNGypfhPBHUGcpVK5DetwEpKcjB26KA8p_ytGO-uru6Vk0UWeQkgp_apVIs3UcCRsTdpenR5RH8pRrHYcEbXIFYhcUfaA=	gAAAAABoU52lZPAHa6UxELUNmvb3NPCEv8C__HNC59SSL9EZLWhO6tHyedXqR6NY8TSIRL5iNt8OTYCJ_BLieaDczIMeVnrU6A==	0	\N
65	ray17	pbkdf2:sha256:600000$XduOrmQMrHDgacl9$0a9e316cff7e0c8f714f4b1670489727080a3e6b86d40cd53c3ff0301e2f675a	customer	t	jjj	gAAAAABoU53XF7KDWcyZcQDgGEUus96tSemkf7aEic4O0VVllnekGpPYbGgTrcei2Z3s96fosm7QnpSqtRx58y5cVqc5TE4xNhgOs-tdLqxp6c8gr0Eb5kc=	gAAAAABoU53XGLTEgvP0ayAvA0wrpaBFigfpdNsuz0-wqHl7vUt1QZ-PZ7U4t3elu4fIK7itX4kCQeXT2FgfkAngXmJKAWUdLQ==	0	\N
66	ray18	pbkdf2:sha256:600000$sqTFaLfNzZeFJcJe$f4b523ba64b6ae4d3bf10693cad90ae164e4b04258d7ba232342f3c2aef4d3d1	customer	t	raj	gAAAAABoU53nVYfIRCje3pytDh8h8mPymW5Zd4CrzSsAHS7qRRQ5VXbPCfYteqyKbL8n44s_4KNnfems3yvgymxpbNc1XyLpxKMuc9HC2WDrnA8Yw6XMry8=	gAAAAABoU53nkIww11rb44uFWMGBwZOqZkg9RkC2Le_Yf_r5aGjwar08G0FXgiKzzquqUQaRE9zilc3G5gjY5NH2goRZUHRE_Q==	0	\N
67	ray20	pbkdf2:sha256:600000$3qaqZjBW5qT0UFWp$e5cc31ed0d54071845c6b71715c4dc25bf4cfe82913a6838fbcb42a91fbcb6f1	staff	t	new	gAAAAABoU_Gy7WqEgBLf4NJ3LKeKZtZbuFQn-jBB4Bab7gxblsoY-qaqMNk16CBmz7LqZvXUn6_OYxVfroTueGhF9WWefIkb0Ql4f2LXInFjHsB0N275cgE=	gAAAAABoU_GyUtbZFmMNvErl6-vZ0ErZBfXrWBwmXLShzPgTePYyotWUQXdf_LVj9PZrUAzmlD5eTZjiLKcrSt6c5SOXoNJAFg==	0	\N
68	ray22	pbkdf2:sha256:600000$ayfiK8qJOKv8jLCG$b21129463df6b0e896c8b1c0cbbd5df2d93df01cf4be0fe999b8fd9f9eea7fa4	customer	t	wongyyy	gAAAAABoVQwSL2u_uR0HBslldgyp-8AYPi7MoKvJwuE36u58F0hPesnViOPd3GMidVEPT0hxmPsNjEHBND77bNX6bOnAyupc-k5BySa94dtTF1VRypofx1M=	gAAAAABoVQwSgJjp5X6bq9t6FThBQBHCXjt72vvdSRsl9gBlWKnD0EQyv02r5pJUBlr3Tgw7mVbWrCkJOKkw0zi5LmljqAxLmw==	0	\N
69	ray23	pbkdf2:sha256:600000$q6DjBMc8ic83HK6b$c4b8e75f89f8b00786d7d20d39bcd40d6cb1c11ae6eecbf94639a22ea766af4a	staff	t	ray company	gAAAAABoVQwwf5ntDNG6erECy31KXun3aYfnTPrJKqNgdYo8IrnXHUX9ZP421eWnvXsWiWAxbFyb1G0dkRZPSG7QkV6gFJXzl3rlPh-Yb8qtxR45o12WlzM=	gAAAAABoVQwwtLU-cayCmR50POYVhX5Yy7sgrtCq8YFaLORXB9y0k1xj-mP3BVvqiK08lcnoWWufmmzsnhNS61suZjgtIqrRaQ==	0	\N
70	ray24	pbkdf2:sha256:600000$5CoPyKRPUFp2IvP5$6aa25edcf9eb455c474b8585dbf2988f8fe2fdc6c4c18d4095edf0fd93a8cb78	customer	t	fff	gAAAAABoVRFqCzDmu4NnN0o_ugzLQox5kntN_nGrwgXQE6eqlQFy90HdS5npcGia4Xxq7DnYsgdFx11R-Xux4c4oyzf5MUiPsg==	gAAAAABoVRFq02icp0DHNbze_KSnwDqwKq8pM4Gmvs6ilT8gZYV8NhnJVjC3tUzDdGfKKmwbvMyQCM5ihH8vwb0Vex_CqN5iog==	0	\N
71	ray25	pbkdf2:sha256:600000$yMLpIH6LuymL2tl8$1d888fe629888a5d72ea25329b3073b32b6b14ce1389eb9e04a77460d3ebf407	customer	t	raywong	gAAAAABoVRwnz0k0mxVPp1RTCiVHcnfq2GeM5hat8xpa70oPsNCtPMdapZJWbA-qmnUf9Kk5G3fqtLie0AculxQTpfuzqxYn-Swt4fqyjifCBZOoR0xixG0=	gAAAAABoVRwnJJueuLGJG6-_xkJzXY9amKEKFBwlxFsu2xblxUEhE0kN-a-laNbwGB108ag-mdFhc9FLs61tdLRz4US90tca5g==	0	\N
72	sandy2	pbkdf2:sha256:600000$vsNb8xamSjuOKppA$576dcf3202ee16f944d8bbad7e540e48f23b0c2d8a821319cc85e18a1365d00a	customer	t	Sandy	gAAAAABoVUBK5q8ipkgW07_r-xPyW0imlDzOCnidgylGOBYpyw7irnswpd3Ligi_Ja7HvcxkGTBnznQqAFSHNfmiUiBz3lcOMV_agS1r11eQ9xeZ4Z_21SM=	gAAAAABoVUBKS9ft6LkzqR3FNF0Odu--Q6YMJTeTL7FrnyAR-4X-l22erI0HJGD7x4EG655OypkdbE3uFxfYKt54tZjHFqgYhQ==	0	\N
75	ray30	pbkdf2:sha256:600000$MiZoze1Is2lG8inm$2047811ec319f9b777d234afa440dc3c439b6ca33422b69cd798abc911f8600e	customer	t	ray	gAAAAABoV7fCWStf7cS0Z5oC8HwPXWa6zbW2WoDT6oQVJQiuss_ge_THDmBN6MK-5lTU5mXuNHnhP1WDhhL-epCe_Jv1T74S__-erwG4X-XCraL9LyP2YdU=	gAAAAABoV7fCLDtxvAF2GLKPQ1Zbd3MHsmgV8ru6FBYLUdVVgMcs4UngYN9_FPhmgRawmElOK3hDPE8lHv3SY7h4hoyP_odO9Q==	0	\N
77	alicevw	pbkdf2:sha256:600000$BIto4yP4R8OWGZ89$7dd91e3cf2bf464d2b5a82c0652f98fbd1295357034fe07171c1bed1fc82ad1d	customer	t	Alice	gAAAAABoV9cO3lsI-GqAof078JrqFjNwmrF3yIqauEiHkJora0mccBYm1VmlKGuxZn9bkdFFlLvIxLjgZYZrJAVODn1DF5MQbzeleORnslDFlTqFIaqKTlM=	gAAAAABoV9cOarhvoBvKwAVfb72FyUslDyNCvOYQxhwCwcvOGmuIcLC1uzseBn6GIDjOB-qEYNk62fLBtgYS7bYYnF79IhZvEA==	0	\N
78	windrider824	pbkdf2:sha256:600000$4I3oGD4SBV9PEZM9$a0185a5ce2d148b87cce0d9e409ea9043adfe01723a19cf242f86eba91b737bd	customer	t	Jay	gAAAAABoWJ3W2u7UYyboq0IfZqg9sUAX4o80SnToeMYRTFq6lNXtM4HTH2sPCZzwk_DGE7XG8wbEWWfrJkoc7wJPN3rGXZd6dNN5soxIzQxZdtpFBlqxB1w=	gAAAAABoWJ3WJqk2AAFkAsrXa7Ni-3QIpe4CpGsCoe54RsNS3pPEjE0ZJyUCod7inARXfxIhiPOih1U7ULZQjwzDtfoHVMJwKA==	0	\N
73	sandy3	pbkdf2:sha256:600000$WvmSNdzd03roor8t$db37a92587b5d12bb3fd30c1a7c2b367536e999d06e9571363d4d36155cc2789	customer	t	jjj	gAAAAABoVUbagj1cOdnUsh-f4KiBKixlFd8saxMi-pi807FewL1eNkk0vf4zoIf4Ax5bH2huSc91d32vVgnqAEiaheQmK6yST9Lw5ysMjkDDZz1iLDd4wzQ=	gAAAAABoVUba4JCW4-Wp6orCl6MUeu89y21OuCLwp9kmzDZ0hH1tBfjEIUnQt4DN8CVZRFslefbyRYWIvWH9UNsE-yXj1081XA==	0	\N
74	ykrw	pbkdf2:sha256:600000$gNOEcOBUqRXnv84S$6927b1b752b20ec26a09bd887d9ae04f0cb9200764b445b6d6d32ee5e5590bc4	customer	t	jjjj	gAAAAABoVUctfw0A0uGCe7zroL9c641Is4DTljQ4VMN8WtPltbvfStSRNTWsUK7VfBdEEtFTXb6BX3gZL4mCUwcmqarLX71U95nt_Z48CekV8ef4kOOfqwg=	gAAAAABoVUct2XntxWSYK8MzFE_zkfTUe63cR97nJT1LTlLiPBSQqjBVgpBrP_SogFIfEUJwvdOz7jDXHXApuYRpnAV1pt3-gA==	0	\N
79	ray33	pbkdf2:sha256:600000$8vwBzgANZrBFmZLT$e4565cbbae78ad6017a4484be687d29f68b12b89be81e2c3e60e28eec45376ce	customer	t	rr	gAAAAABoWkQ0dKqOvw8tcqYlvgUQu0uCCoamd9VVqWPC10rhXnfqbiX7wp-HDvcAehbKwMWkE9jbfgJGsQhIXD8YweAGNk-kK6Y2-dr7fWoU1W-CdX0Vttc=	gAAAAABoWkQ0PrSOCfkAEVIcP8wS5IRl-OXvAhilg_tUSxamS6hDgfMdwuGS-VRDgRYI4u2e7tuXEYH9UPfU4X6Q4OtFUJmeFQ==	0	\N
80	ray35	pbkdf2:sha256:600000$lIbko2ICG89yad22$8678aa421ffab670711e7e418954ca9f79df5f88113e75fc133695741240f729	customer	t	rayray	gAAAAABoWmZBoDglHutt-cp1IE7Hp9NJ5uDdSFbGLuZH3OLD2LTGrLRp4WfzVXvV-BbTNvvPcqB0ynF0mMtSS8f_KyT7qOYjEHtpaSkUmqnJLIUgTrXwtYc=	gAAAAABoWmZBi1T84FjMeFJSIWTLxz3nodlwQ-3HCene_8jFhkZhE-CCz0Cy2coeD02n0uzFTNxYHuR1qnq8Tx873Cz5JaJBGw==	0	\N
81	ray36	pbkdf2:sha256:600000$PT8ipzHs412Ag9Vm$546688bc2dd6d8e8a50eae1bcc8bc097d69ee0c51a53b46815becb9c2530ce66	customer	t	fjsdlkfjd	gAAAAABoWoRH8n1c2WZ0NHXrRIIigauLQAXluy-Gdglg3T0XFIPGKxRm4UDtH5gj5p8vnqMbOOvDbpbeOC7EM2KPFC8liR3E88dPfAts24RQhy3Tb5jsUIU=	gAAAAABoWoRHnWuSjDDzrKZBDkfMcH7NethjfQfMaJwfTPP41dNvGPW3XGr4U85k-7VbzhMej5DuigPPzBuQxiAH_b2fGco1YQ==	0	\N
103	ray85	pbkdf2:sha256:600000$e4us2ymJRF4PdxvY$0980088ab9cf82d838f5e9d1f585feecc222f8a10f5964dff3175b341984d2bb	customer	t	ray84	gAAAAABobf4MAE0yPhwpp6hBj9vDGXC5y1Pq2aIOeEbdjqnqzvrDHNLLyrGVdkw9ga11RkzWCby9SYOB7SjM55UAUFdMpjk1n3sCrm1BLCq57ct26C95Y7k=	gAAAAABobf4MkF-8NBKUOokeX34sNVhJr3JnyAYNMD5f3HDL2wMI6H8HRuDyvIp0e4RHGAu1Rb_AT7qkJ_4NzADssJfA_gbpqw==	0	\N
86	ray42	pbkdf2:sha256:600000$AMxFNpYN5CD76hH7$fee79c1752eff0346e89f3460f9a496c466410e1100b8835d76a1dad70836454	customer	t	ttt	gAAAAABoXmoEr9Ddl0FlDL_IEon-kwJC2dRTgSXXVzAC2MIU8WrnUFMYLqqJeOFEt3qxoawJ_WOkAkqn8AaFrhjMTD523-AocCbJrOTwb5_EEo-2GiY6Ihk=	gAAAAABoXmoE_Pwh45SIHGqNtquqUrTG06p2c9DSmyGPlopaRVWJNgE4xwgmT0CzSC9LHpt-LnRV-6dhA17475AnEBVHKrU06w==	0	\N
89	ray47	pbkdf2:sha256:600000$kMldJuiGImJUD9Bd$ab55a57cc008c09e57d88beedb92c77a3591dd628be7a684e9a4e2f3910694f7	customer	t	Ray Wong	gAAAAABoX4M9vkBMJiYqx-iBF0s8Dg7f0py3N62FSDpQuUVibX8jEQBSwWXLXEfen-07SccnJwnZyr0ovXz39bVeEKGQmL75fwnhBpr-DuO2ocoFCbsBUkg=	gAAAAABoX4M9I_tFPWDCESxtxFddTOW5DAZtGUJXsibGlkm3h6TAFwMLA3Zdtn3aW1YENYS9uE_p79_xPez7LL65Y6N4B0MM7A==	0	\N
90	ray46	pbkdf2:sha256:600000$bdaOzbPUdqwCJPbA$45b1c3bbdd1829f3ca30724429baceff2c07ca86d64cfc61de677d9a1d3f1261	customer	t	rajlj	gAAAAABoZ4QZIwKnW1WmJqGys4PH_FKbOQ804JuaY9_h-2Lzh9JxOOp5RhnNy-ZVTPpbKaR9zCQOW91KcIfEzMFxYyMOIKSRyEqHx3Tb6EdNULOqbmXyhtk=	gAAAAABoZ4QZbhGIP1ilJAD7pbT1upYxTj68SJwYO5dCr2OSsqiGFMHR3D34HwR8J2U6d4lNug3TK57UY3-t_u46hC9xugkvjA==	0	\N
94	ray60	pbkdf2:sha256:600000$n01wTh1fxnhXXS83$e6ef55c9f2b7b701fa604d2f3ebb8358ffc4099b7f408c6e316f85a853b67c63	customer	t	rajlj	gAAAAABoZ4si9RfOh6UD7eMeD7BkEvYrAA0tK5eFKrpszooVneE53Jy3Ex_vGu2H8ahMWVwO2pSdOi5vG1gm5ZdMGUQAzxZjpSp97D_7j2K7DIpsWa0SLxU=	gAAAAABoZ4siFsCipwTWDeTh_CoeYxPMSvedEhJYRsmFGtn7KPZm4isFeWF9g6QWumWGYzdLLfeGyTsmceBw2sxl-v-KHP_Qag==	0	\N
95	ray61	pbkdf2:sha256:600000$wGPj8y6pxCHvQK58$f23463176ffbdbd03b9ac6009715b3e4f8f4d3ab90e3006a0dbb7f5683a44417	customer	t	jjjjjjj	gAAAAABoZ4_lWzROmKacV080U2sL_T7-fnbi8h73TiPC7hR5fTZMFE7AKaA4Uj8bhwYGj9SxU439iQOFwb1072TnrKvSMl7FyOjzDEg4QLvZBVar_2OQvWA=	gAAAAABoZ4_l_DC1NxhfH5XEYmQG67i3PRzKK7LWLUdW3hTx7XAQphy0lZG9DGdpMWR23JJVq1a6zVqtDNJA4zrIZbZPEEeiyw==	0	\N
96	ray71	pbkdf2:sha256:600000$bpbOhII0isp8hQpe$d6f1c3b4df498e266ce7dabd09957c66463e1e8c40521619db87bac9e49cd578	customer	t	jfdalkj	gAAAAABoZ7ZdPovOi1HKjXZaFOT47GtenK-M6NMs-hYVe6U3406JzaBB581VnkWOpqJzrPAu8WNFXmmt8NYoxCBx71Osnwisfw==	gAAAAABoZ7Zd9Q9RttqtWj3mloY_Aq-UbbTGOMaqHRbYkk8CeD3oZMMPCFgLlLFbM5Pij7GCzNxllIMmGlRgWLFKBgBSjuBZAg==	0	\N
98	ray82	pbkdf2:sha256:600000$bj24Oz7zj7cpntKd$32975f9a55e27fe77b8b919ec721b2707554f557de27bdb3011c10c4fa7e4b4e	staff	t	ray82	gAAAAABobc9ZRyrGQYa87jej1LeK4fhledXr75rSXRu9r39SvU5fdh5AE4lv20Dmm4BCEPOn79DNrivauWfVp1slxepykObKgzsd_b2eQGuhuUW43bZR0eE=	gAAAAABobc9ZE3THEVisozNBUM_JFh-YEUXK5crulhDIr70GsDViHAn4956_pqLCquzfPG43p7Uy3Osc_z2oLhe3zE-mac_vVg==	0	\N
100	ray83	pbkdf2:sha256:600000$9zSjjJTDkaAetucI$77db27f2609a9424843fa61d2e32496068be08dd2e199df412c88fa1cbdc2143	customer	t	ray83	gAAAAABobdCH3KQMpCQMwgtvdN3aGEFUM2iN2potfHzc81FZLkVg3Gg0YvRBMB7WEsqtbJdXM-Z5Kjqpv-unO1xIhSB76CbagfMchI7qqtA0HSPDnFq9gvc=	gAAAAABobdCH8rJk54MTPCWmZPpRcYBUstWMhWXqbW32greBG1vVhx02Z24NVGekq0w82X5mi0tJ_1vARBqRjaeoMZfCtj-78w==	0	\N
105	ray90	pbkdf2:sha256:600000$NFhTK6gySuEvgWAf$9f32f0daf4f93dad5f0eba8a2606c4e01b000cd3c156219e9ad55dee321c0dd4	customer	t	ray90	gAAAAABobf4-vrMPV4h_V0kMhLNn7MildJUqGzquE4kdOLViFlG7EKvvNZKCzmP-t4HSmD3EliamRdPU36otXa37YLy7phoTlCFqvdxCZ3WMzNoEPrEPAN4=	gAAAAABobf4-WunPDnQEAd0vWA4e0gf_hkQGij0GLRt3Ee457SZJ7-PSWw9H9su_Y213Qu4gA7EKuV43-Jqm4RTg0m6JZIW0Tg==	0	\N
101	ray84	pbkdf2:sha256:600000$911BrT3DjZ2Ljldc$86abede24ccdde976925161af1255863aa2f3c230fd987643f96fd39d154af7b	customer	t	ray84	gAAAAABobf31nU9iCUPRtX86OeqrQybbz7aUutulkXZr-eeGGMR2MI8wIZ6FSviGB2LomXr_pELfSIhNJGCxth35fmQbTxrCB8-hnXBRaXQhceITwj_7WqQ=	gAAAAABobf31xQbwYvPfrus3l1VY890dlVupv7JHq_R2uPn2_A2JCIFVyLxf9oQuPy9asBKktGGzzCg3ADoe9htYdCpWvFnovg==	0	\N
85	ray41	pbkdf2:sha256:600000$PU2Esv6MuvgXbpxs$a8ed666c6e52627673ac2e0e6a94fd97904163994e2e3b931c9369bec5f7acaf	customer	t	raywong	gAAAAABoXmSORv7NSwQL9PIBpo-yN5Iz0qZ1IkrYthoyz4jegGN6jr5jFGYbZy-TLbxnc-IY33ADNAjAo0q_j7eamQ5pkir3H33pGxfB9MaurTGMjR7cZuc=	gAAAAABoXmSOTTAa_4yuA04GyEhcazUCz7i4xRL0nnkYJVWG-5f1QLqrHdQLg9cnkLGIKFA5wNxkyFd9xqGU5VtL0YbQqMgUtQ==	0	\N
97	ray81	pbkdf2:sha256:600000$vvVg6dMnz1rhMqf9$5766dda2f57342eb9b1bfa15c15768660a95f585e5b8ff7a0ecb0a7be8973dd6	customer	t	Ray	ykrw12@gmail.com	4567890	0	\N
108	ray110	pbkdf2:sha256:600000$qlfXWILu5wvBZx7n$904a159423d890c5c280ccbf0b5baa3154ce78e1952526c6c83946ccefde8561	customer	t	ray1	gAAAAABod3YrjR1InpqFBC6ipi2MLsEh27hwpWrNEUHf1A9dd_lU5Int6lx6UsU1Z_YmUkAXuWZVY53AoW7zn8nnTlYSDppfT0EsyLPR7Oeoc2SE6nfRbY4=	gAAAAABod3Yrae2ITP-beBAV7SUncSDYODw7MqMr1TP1fVD1bPsykogeVkA7mLFk_XCVso26Zuc81lxhVuRn7Wohw5YOXUhzKA==	0	\N
76	terryng	pbkdf2:sha256:600000$LFLfHNC6wHYf9z2q$54af9e7e2c4705ee30091878c976a1f29f5c07984a895d03fda623934957b744	staff	t	Smart Famous	gAAAAABoV9NCL0TinFBLHUFZrBaKVHdjSVT7FOGFcD43DIV25cK9j2Y-zmZTBzE_xIZYzqgYQyxp4oC7lifgLpCn5wbhRjVDdbGlZIMcTubIOmmCWLx-FWs=	gAAAAABoV9NCjA-wdEQ7WQ1ZibLfNwZzEYf-d54rwLm_s66NYPSiz81cR8FEZZB6e631eAdASg_zp6al2zt0Naiqf8GTAb2xxg==	1	\N
45	john	$2b$12$4b/3e26VGuFFPLYK0qvqC.zz8eOshDtjllXdtY1w/wc50KoXP3bdm	customer	t	john	johnwongjething@gmail.com	111	0	\N
106	ray91	pbkdf2:sha256:600000$VlYKxtmnfnjVgCOe$185f21597d08e42ee6120384e99254801a637437d6101cdc9f6f17307f6e21ed	customer	t	ray90	gAAAAABobf64_iENOhzZQx6-BwTWDmI-ULz7DnHTT3HNYkfLRpAbJfySp9__x-aJC2Y5yROudhy-S45IDjggYsLi246lKJ9rqrjgGyX_D_A4FimAzQWev1o=	gAAAAABobf64XRdUi71DVWkKGPM2MPfILQoNqLp-sDKnLzFsFVCjVh3oJOQwalouFmQgYzggyPc-mUkv_xLQ8vA2k5i7YeU2rw==	0	\N
109	ray112	pbkdf2:sha256:600000$0KpQRDkcCoc4CoUb$3fb52be5afc7254a2b3188e1fc0b9e776868131ae967320e0d4d055dcfd270b4	customer	t	ray112	gAAAAABofMCW145__Y3p50VMuNAsvMNC88nPR_KrIhYLaByh8zciYg30GtL_QBzJvzuo8WRXi1QL2cxUIsOhhdzHbAXfOXkZolRK0LQ2sDtTolnB4eWo7VQ=	gAAAAABofMCWFkbr_O3HLVBJGyOixPHLQ8iBp8dDVo4_GK6WrjS1TD_GfIQUF92eERH37oh_KLa2ZxNBwgmT1eZd1k9nAd0yLA==	0	\N
107	ray100	pbkdf2:sha256:600000$njO93uxLzxFUlIQR$f74075e2f4c65a5abb537f41ce2d37fd1fc223026f35035837fa5f818d83f5ba	staff	t	Sandy Kong	gAAAAABoc1j7xPfAwg4lX1tFytTeHbiVRovlr8C1j8YSFf2mJslUvg4IJ42qpRGRJ3bNig4Dxh0Oi5iZDxEDI57ORqjk_M0Xzcdu6WKwExlpLfBZvVz5X9U=	gAAAAABoc1j7ZI-yEfQ7PuPsHzeOeqiysVB1MrU3LdKAxKGTfmGjzGhy_mFDYRFBDS_uNW8y5Yn_NpR_g-Dc7jx4aDiZVsGGsA==	0	\N
110	ray401	pbkdf2:sha256:600000$UgUfvJ9iy96G1z7H$10d1f9825070cae317ae7483f937063923bfd8653334328f2d31c316d13ec1dd	customer	t	ray	gAAAAABoiaCblYvBJafcH1HbeuPBf6-YjMZ65Ij4d7WVr4pJwdxPPbqvv_dmFfTx56vE6SKjo_dqzsG_lM9nmK3YrkwbX3JCvwNxdGQk-r43QnA7y86D_0s=	gAAAAABoiaCbNm6ZIWIrhssJL8LbKV_GcE-QrTBmIoLHWzqfZNLgINIBgwYaqixniR2m8JYvLQIt1bnGAAnyj1SG8cLSm9TrYA==	0	\N
84	ray40	pbkdf2:sha256:600000$hIwLj4Br9vdp2kiW$1f3d23d0f330129794e49b04e7c3576b0e5610e6577214a3b9207b7d590ef2f0	staff	t	ray40	gAAAAABoXQ5rOSK0fJrhRRRSN3N68fi7_xVOFsvrs9pccAPz19jBGaxx5ogkNnUoK-Z0un8tqQoTKlnfGhUYgmSu59PoAYZucrwkdIaNp3qJd67aWOOC3ic=	gAAAAABoXQ5r1t3IASl91enfjjL7kCLjgjpmYerQhHNP1HzPyqodbiiGS1gSZ4DQ4EJqwUMdUC1pIfdvVaAl_a_bV5A_6FFNgg==	0	\N
\.


--
-- Name: ai_drafts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ai_drafts_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 175, true);


--
-- Name: bank_unmatched_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bank_unmatched_records_id_seq', 88, true);


--
-- Name: bill_of_lading_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bill_of_lading_id_seq', 75, true);


--
-- Name: customer_balance_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.customer_balance_transactions_id_seq', 73, true);


--
-- Name: customer_balances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.customer_balances_id_seq', 97, true);


--
-- Name: customer_email_replies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.customer_email_replies_id_seq', 827, true);


--
-- Name: customer_emails_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.customer_emails_id_seq', 112, true);


--
-- Name: email_editing_locks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_editing_locks_id_seq', 136, true);


--
-- Name: email_ingest_errors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_ingest_errors_id_seq', 28, true);


--
-- Name: email_processing_locks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_processing_locks_id_seq', 500, true);


--
-- Name: fcm_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fcm_notifications_id_seq', 47, true);


--
-- Name: fcm_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fcm_tokens_id_seq', 13, true);


--
-- Name: outlook_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.outlook_sessions_id_seq', 1, false);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 46, true);


--
-- Name: pricing_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pricing_config_id_seq', 5, true);


--
-- Name: pricing_overrides_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pricing_overrides_id_seq', 1, false);


--
-- Name: test123_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test123_id_seq', 1, false);


--
-- Name: unmatched_receipts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.unmatched_receipts_id_seq', 14, true);


--
-- Name: user_activity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_activity_id_seq', 293, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 110, true);


--
-- Name: ai_drafts ai_drafts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_drafts
    ADD CONSTRAINT ai_drafts_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: bank_unmatched_records bank_unmatched_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_unmatched_records
    ADD CONSTRAINT bank_unmatched_records_pkey PRIMARY KEY (id);


--
-- Name: bill_of_lading bill_of_lading_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_of_lading
    ADD CONSTRAINT bill_of_lading_pkey PRIMARY KEY (id);


--
-- Name: customer_balance_transactions customer_balance_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balance_transactions
    ADD CONSTRAINT customer_balance_transactions_pkey PRIMARY KEY (id);


--
-- Name: customer_balances customer_balances_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balances
    ADD CONSTRAINT customer_balances_pkey PRIMARY KEY (id);


--
-- Name: customer_balances customer_balances_username_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balances
    ADD CONSTRAINT customer_balances_username_unique UNIQUE (username);


--
-- Name: customer_email_replies customer_email_replies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_email_replies
    ADD CONSTRAINT customer_email_replies_pkey PRIMARY KEY (id);


--
-- Name: customer_emails customer_emails_message_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_emails
    ADD CONSTRAINT customer_emails_message_id_key UNIQUE (message_id);


--
-- Name: customer_emails customer_emails_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_emails
    ADD CONSTRAINT customer_emails_pkey PRIMARY KEY (id);


--
-- Name: email_editing_locks email_editing_locks_email_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_editing_locks
    ADD CONSTRAINT email_editing_locks_email_id_key UNIQUE (email_id);


--
-- Name: email_editing_locks email_editing_locks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_editing_locks
    ADD CONSTRAINT email_editing_locks_pkey PRIMARY KEY (id);


--
-- Name: email_ingest_errors email_ingest_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_ingest_errors
    ADD CONSTRAINT email_ingest_errors_pkey PRIMARY KEY (id);


--
-- Name: email_processing_locks email_processing_locks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_processing_locks
    ADD CONSTRAINT email_processing_locks_pkey PRIMARY KEY (id);


--
-- Name: email_prompt_locks email_prompt_locks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_prompt_locks
    ADD CONSTRAINT email_prompt_locks_pkey PRIMARY KEY (sender_id);


--
-- Name: fcm_notifications fcm_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_notifications
    ADD CONSTRAINT fcm_notifications_pkey PRIMARY KEY (id);


--
-- Name: fcm_tokens fcm_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_tokens
    ADD CONSTRAINT fcm_tokens_pkey PRIMARY KEY (id);


--
-- Name: fcm_tokens fcm_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_tokens
    ADD CONSTRAINT fcm_tokens_token_key UNIQUE (token);


--
-- Name: outlook_sessions outlook_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlook_sessions
    ADD CONSTRAINT outlook_sessions_pkey PRIMARY KEY (id);


--
-- Name: outlook_sessions outlook_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlook_sessions
    ADD CONSTRAINT outlook_sessions_session_token_key UNIQUE (session_token);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: pricing_config pricing_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_config
    ADD CONSTRAINT pricing_config_pkey PRIMARY KEY (id);


--
-- Name: pricing_overrides pricing_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_overrides
    ADD CONSTRAINT pricing_overrides_pkey PRIMARY KEY (id);


--
-- Name: test123 test123_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test123
    ADD CONSTRAINT test123_pkey PRIMARY KEY (id);


--
-- Name: unmatched_receipts unmatched_receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unmatched_receipts
    ADD CONSTRAINT unmatched_receipts_pkey PRIMARY KEY (id);


--
-- Name: user_activity user_activity_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_pkey PRIMARY KEY (id);


--
-- Name: user_activity user_activity_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_ai_drafts_email_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ai_drafts_email_id ON public.ai_drafts USING btree (email_id);


--
-- Name: idx_ai_drafts_sent_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ai_drafts_sent_at ON public.ai_drafts USING btree (sent_at);


--
-- Name: idx_audit_logs_operation; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_operation ON public.audit_logs USING btree (operation);


--
-- Name: idx_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp" DESC);


--
-- Name: idx_audit_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: idx_audit_logs_user_operation; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_user_operation ON public.audit_logs USING btree (user_id, operation);


--
-- Name: idx_bill_of_lading_balance_applied; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_balance_applied ON public.bill_of_lading USING btree (balance_applied);


--
-- Name: idx_bill_of_lading_container_20ft; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_container_20ft ON public.bill_of_lading USING btree (container_count_20ft);


--
-- Name: idx_bill_of_lading_container_40ft; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_container_40ft ON public.bill_of_lading USING btree (container_count_40ft);


--
-- Name: idx_bill_of_lading_container_40ft_hc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_container_40ft_hc ON public.bill_of_lading USING btree (container_count_40ft_hc);


--
-- Name: idx_bill_of_lading_container_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_container_type ON public.bill_of_lading USING btree (container_type);


--
-- Name: idx_bill_of_lading_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_created_at ON public.bill_of_lading USING btree (created_at DESC);


--
-- Name: idx_bill_of_lading_customer_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_customer_email ON public.bill_of_lading USING btree (customer_email);


--
-- Name: idx_bill_of_lading_customer_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_customer_status ON public.bill_of_lading USING btree (customer_email, status);


--
-- Name: idx_bill_of_lading_notify_party; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_notify_party ON public.bill_of_lading USING btree (notify_party);


--
-- Name: idx_bill_of_lading_payment_processed; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_payment_processed ON public.bill_of_lading USING btree (payment_processed_by, payment_processed_at);


--
-- Name: idx_bill_of_lading_pricing_method; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_pricing_method ON public.bill_of_lading USING btree (pricing_method);


--
-- Name: idx_bill_of_lading_shipment_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_shipment_type ON public.bill_of_lading USING btree (shipment_type);


--
-- Name: idx_bill_of_lading_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_status ON public.bill_of_lading USING btree (status);


--
-- Name: idx_bill_of_lading_updated_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bill_of_lading_updated_at ON public.bill_of_lading USING btree (updated_at DESC);


--
-- Name: idx_customer_balance_transactions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_balance_transactions_created_at ON public.customer_balance_transactions USING btree (created_at DESC);


--
-- Name: idx_customer_balance_transactions_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_balance_transactions_username ON public.customer_balance_transactions USING btree (username);


--
-- Name: idx_customer_balances_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_balances_username ON public.customer_balances USING btree (username);


--
-- Name: idx_customer_email_replies_auto_send; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_auto_send ON public.customer_email_replies USING btree (auto_send_recommended);


--
-- Name: idx_customer_email_replies_confidence; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_confidence ON public.customer_email_replies USING btree (confidence_score);


--
-- Name: idx_customer_email_replies_confidence_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_confidence_score ON public.customer_email_replies USING btree (confidence_score);


--
-- Name: idx_customer_email_replies_count; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_count ON public.customer_email_replies USING btree (customer_email_id, id);


--
-- Name: idx_customer_email_replies_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_created_at ON public.customer_email_replies USING btree (created_at DESC);


--
-- Name: idx_customer_email_replies_customer_email_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_customer_email_id ON public.customer_email_replies USING btree (customer_email_id);


--
-- Name: idx_customer_email_replies_email_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_email_id ON public.customer_email_replies USING btree (customer_email_id);


--
-- Name: idx_customer_email_replies_is_draft; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_email_replies_is_draft ON public.customer_email_replies USING btree (is_draft);


--
-- Name: idx_customer_emails_bcc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_bcc ON public.customer_emails USING gin (bcc);


--
-- Name: idx_customer_emails_bl_numbers; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_bl_numbers ON public.customer_emails USING gin (bl_numbers);


--
-- Name: idx_customer_emails_cc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_cc ON public.customer_emails USING gin (cc);


--
-- Name: idx_customer_emails_classification; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_classification ON public.customer_emails USING btree (classification);


--
-- Name: idx_customer_emails_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_created_at ON public.customer_emails USING btree (created_at);


--
-- Name: idx_customer_emails_created_at_desc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_created_at_desc ON public.customer_emails USING btree (created_at DESC, id DESC);


--
-- Name: idx_customer_emails_message_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_message_id ON public.customer_emails USING btree (message_id);


--
-- Name: idx_customer_emails_outlook_message_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_outlook_message_id ON public.customer_emails USING btree (outlook_message_id);


--
-- Name: idx_customer_emails_outlook_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_outlook_user_id ON public.customer_emails USING btree (outlook_user_id);


--
-- Name: idx_customer_emails_processed; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_processed ON public.customer_emails USING btree (processed_for_payments);


--
-- Name: idx_customer_emails_processed_for_payments; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_processed_for_payments ON public.customer_emails USING btree (processed_for_payments);


--
-- Name: idx_customer_emails_reply_to; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_reply_to ON public.customer_emails USING gin (reply_to);


--
-- Name: idx_customer_emails_sender; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_sender ON public.customer_emails USING btree (sender);


--
-- Name: idx_customer_emails_sender_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_sender_created ON public.customer_emails USING btree (sender, created_at DESC);


--
-- Name: idx_customer_emails_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_status ON public.customer_emails USING btree (status);


--
-- Name: idx_customer_emails_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_subject ON public.customer_emails USING btree (subject);


--
-- Name: idx_customer_emails_to; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_emails_to ON public.customer_emails USING gin ("to");


--
-- Name: idx_email_editing_locks_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_editing_locks_expires ON public.email_editing_locks USING btree (expires_at);


--
-- Name: idx_email_editing_locks_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_editing_locks_user ON public.email_editing_locks USING btree (user_id);


--
-- Name: idx_email_processing_locks_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_processing_locks_expires ON public.email_processing_locks USING btree (expires_at);


--
-- Name: idx_email_processing_locks_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_processing_locks_user ON public.email_processing_locks USING btree (user_id);


--
-- Name: idx_fcm_notifications_email_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fcm_notifications_email_type ON public.fcm_notifications USING btree (email_id, notification_type);


--
-- Name: idx_fcm_notifications_sent_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fcm_notifications_sent_at ON public.fcm_notifications USING btree (sent_at);


--
-- Name: idx_fcm_tokens_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fcm_tokens_active ON public.fcm_tokens USING btree (is_active);


--
-- Name: idx_fcm_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fcm_tokens_token ON public.fcm_tokens USING btree (token);


--
-- Name: idx_fcm_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fcm_tokens_user_id ON public.fcm_tokens USING btree (user_id);


--
-- Name: idx_outlook_sessions_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outlook_sessions_token ON public.outlook_sessions USING btree (session_token);


--
-- Name: idx_outlook_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outlook_sessions_user_id ON public.outlook_sessions USING btree (user_id);


--
-- Name: idx_password_reset_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_password_reset_tokens_expires_at ON public.password_reset_tokens USING btree (expires_at);


--
-- Name: idx_password_reset_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: idx_pricing_config_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_config_active ON public.pricing_config USING btree (is_active);


--
-- Name: idx_pricing_overrides_bill_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pricing_overrides_bill_id ON public.pricing_overrides USING btree (bill_of_lading_id);


--
-- Name: idx_user_activity_last_activity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_activity_last_activity ON public.user_activity USING btree (last_activity);


--
-- Name: idx_users_approved; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_approved ON public.users USING btree (approved);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: email_processing_locks email_locks_cleanup_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER email_locks_cleanup_trigger BEFORE INSERT ON public.email_processing_locks FOR EACH ROW EXECUTE FUNCTION public.auto_cleanup_email_locks();


--
-- Name: email_processing_locks single_lock_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER single_lock_trigger BEFORE INSERT ON public.email_processing_locks FOR EACH ROW EXECUTE FUNCTION public.check_single_lock();


--
-- Name: ai_drafts ai_drafts_email_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_drafts
    ADD CONSTRAINT ai_drafts_email_id_fkey FOREIGN KEY (email_id) REFERENCES public.customer_emails(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: customer_balance_transactions customer_balance_transactions_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balance_transactions
    ADD CONSTRAINT customer_balance_transactions_username_fkey FOREIGN KEY (username) REFERENCES public.users(username);


--
-- Name: customer_balances customer_balances_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_balances
    ADD CONSTRAINT customer_balances_username_fkey FOREIGN KEY (username) REFERENCES public.users(username);


--
-- Name: customer_email_replies customer_email_replies_customer_email_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_email_replies
    ADD CONSTRAINT customer_email_replies_customer_email_id_fkey FOREIGN KEY (customer_email_id) REFERENCES public.customer_emails(id) ON DELETE CASCADE;


--
-- Name: email_editing_locks fk_email_editing_locks_email; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_editing_locks
    ADD CONSTRAINT fk_email_editing_locks_email FOREIGN KEY (email_id) REFERENCES public.customer_emails(id) ON DELETE CASCADE;


--
-- Name: fcm_tokens fk_fcm_tokens_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fcm_tokens
    ADD CONSTRAINT fk_fcm_tokens_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_activity fk_user_activity_email; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT fk_user_activity_email FOREIGN KEY (current_email_id) REFERENCES public.customer_emails(id) ON DELETE SET NULL;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: pricing_overrides pricing_overrides_bill_of_lading_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pricing_overrides
    ADD CONSTRAINT pricing_overrides_bill_of_lading_id_fkey FOREIGN KEY (bill_of_lading_id) REFERENCES public.bill_of_lading(id);


--
-- PostgreSQL database dump complete
--

