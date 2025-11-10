-- ============================================================================
-- Setup Script: Create Tables from CSV Files
-- ============================================================================
-- This script creates the base tables needed for correlation analysis.
-- Run this BEFORE running mrr_chat_correlation_analysis.sql
-- ============================================================================

-- PostgreSQL Version
-- ============================================================================

-- Drop tables if they exist (for re-running)
DROP TABLE IF EXISTS mrr_data CASCADE;
DROP TABLE IF EXISTS conversations_data CASCADE;

-- Create MRR data table
CREATE TABLE mrr_data (
    "Mrr Id" VARCHAR(255),
    "Revenue Calendar Month" DATE,
    "Revenue Fiscal Quarter End Month" DATE,
    "Revenue Fiscal Quarter" VARCHAR(50),
    "Revenue Fiscal Year" VARCHAR(50),
    "Account Guid" VARCHAR(255),
    "Account Name" VARCHAR(500),
    "Account Owner User Guid" VARCHAR(255),
    "Account Owner User Name" VARCHAR(255),
    "Sales Level 4 Manager Name" VARCHAR(255),
    "Sales Level 3 Manager Name" VARCHAR(255),
    "Sales Level 2 Manager Name" VARCHAR(255),
    "Historical Account Owner User Guid" VARCHAR(255),
    "Historical Account Owner User Name" VARCHAR(255),
    "Historical Sales Level 4 Manager Name" VARCHAR(255),
    "Historical Sales Level 3 Manager Name" VARCHAR(255),
    "Historical Sales Level 2 Manager Name" VARCHAR(255),
    "Account Csm User Guid" VARCHAR(255),
    "Account Csm User Name" VARCHAR(255),
    "Account Segment" VARCHAR(255),
    "Account Sub Segment" VARCHAR(255),
    "Account Region" VARCHAR(255),
    "Account Geo" VARCHAR(255),
    "Account Industry" VARCHAR(255),
    "Account Risk Status" VARCHAR(255),
    "Account Primary Cloud Data Warehouse" VARCHAR(255),
    "Organization Uuid" VARCHAR(255),
    "Product All Current Cloud Data Warehouses" TEXT,
    "Connection Types in Use" INTEGER,
    "Primary Connection" VARCHAR(255),
    "Primary Connection Queries" INTEGER,
    "Secondary Connection" VARCHAR(255),
    "Secondary Connection Queries" INTEGER,
    "Tertiary Connection" VARCHAR(255),
    "Tertiary Connection Queries" INTEGER,
    "Total Queries in Month" INTEGER,
    "Customer Is Active" INTEGER,
    "Prev Month Customer Is Active" INTEGER,
    "Prev 3 Month Customer Is Active" INTEGER,
    "Prev 12 Month Customer Is Active" INTEGER,
    "Customer Is New" INTEGER,
    "Customer Is Returning" INTEGER,
    "Customer Is Churned" INTEGER,
    "Subscription Start Date" TIMESTAMP,
    "Subscription End Date" TIMESTAMP,
    "Expected Renewal Date" TIMESTAMP,
    "Expected Renewal Fiscal Quarter" VARCHAR(50),
    "Expected Renewal Fiscal Year" VARCHAR(50),
    "Customer Start Month" DATE,
    "Customer Start Fiscal Quarter" VARCHAR(50),
    "Num Active Years" INTEGER,
    "Number of Free Months" INTEGER,
    "Mrr" NUMERIC(15, 2),
    "Arr" NUMERIC(15, 2),
    "Expected Mrr" NUMERIC(15, 2),
    "Expected Arr" NUMERIC(15, 2),
    "Gut Forecast Mrr" NUMERIC(15, 2),
    "Gut Forecast Arr" NUMERIC(15, 2),
    "Potential Mrr" NUMERIC(15, 2),
    "Potential Arr" NUMERIC(15, 2),
    "In Pipeline Mrr" NUMERIC(15, 2),
    "In Pipeline Arr" NUMERIC(15, 2),
    "Renewal Commit Forecast Arr" NUMERIC(15, 2),
    "Upsell Commit Forecast Arr" NUMERIC(15, 2),
    "Forecast Best Case" NUMERIC(15, 2),
    "Forecast Renewal Best Case" NUMERIC(15, 2),
    "Forecast Upsell Best Case" NUMERIC(15, 2),
    "Forecast Notes" TEXT,
    "Is Churn Forecast" INTEGER,
    "Prev Mrr" NUMERIC(15, 2),
    "Prev Arr" NUMERIC(15, 2),
    "Prev 12 Month Mrr" NUMERIC(15, 2),
    "Prev 12 Month Arr" NUMERIC(15, 2),
    "Mrr Change" NUMERIC(15, 2),
    "Arr Change" NUMERIC(15, 2),
    "Change Category" VARCHAR(255),
    "Account Is Starter Pack" INTEGER,
    "Number of Active Subscriptions" INTEGER,
    "Active Subscription Guids" TEXT,
    "Active Subscription Names" TEXT,
    "Platform Fee Arr" NUMERIC(15, 2),
    "Embed Platform Fee Arr" NUMERIC(15, 2),
    "Enterprise Licenses Arr" NUMERIC(15, 2),
    "Paid Licenses Arr" NUMERIC(15, 2),
    "Pro Licenses Arr" NUMERIC(15, 2),
    "Sigma View Licenses Arr" NUMERIC(15, 2),
    "Sigma Act Licenses Arr" NUMERIC(15, 2),
    "Sigma Analyze Licenses Arr" NUMERIC(15, 2),
    "Sigma Build Licenses Arr" NUMERIC(15, 2),
    "Explorer Licenses Arr" NUMERIC(15, 2),
    "Essentials Licenses Arr" NUMERIC(15, 2),
    "Free Licenses Arr" NUMERIC(15, 2),
    "Viewer Plus Arr" NUMERIC(15, 2),
    "Embed Licenses Arr" NUMERIC(15, 2),
    "Misc Licenses Arr" NUMERIC(15, 2),
    "Platform Fee Mrr" NUMERIC(15, 2),
    "Embed Platform Fee Mrr" NUMERIC(15, 2),
    "Enterprise Licenses Mrr" NUMERIC(15, 2),
    "Paid Licenses Mrr" NUMERIC(15, 2),
    "Pro Licenses Mrr" NUMERIC(15, 2),
    "Explorer Licenses Mrr" NUMERIC(15, 2),
    "Essentials Licenses Mrr" NUMERIC(15, 2),
    "Free Licenses Mrr" NUMERIC(15, 2),
    "Sigma View Licenses Mrr" NUMERIC(15, 2),
    "Sigma Act Licenses Mrr" NUMERIC(15, 2),
    "Sigma Analyze Licenses Mrr" NUMERIC(15, 2),
    "Sigma Build Licenses Mrr" NUMERIC(15, 2),
    "Viewer Plus Mrr" NUMERIC(15, 2),
    "Embed Licenses Mrr" NUMERIC(15, 2),
    "Misc Licenses Mrr" NUMERIC(15, 2)
);

-- Create Conversations data table
CREATE TABLE conversations_data (
    "Conversation Id" VARCHAR(255),
    "Conversation Created PT" VARCHAR(255),
    "TSE Assigned to" VARCHAR(255),
    "TSE Rated" VARCHAR(255),
    "TSE Geo Team" VARCHAR(255),
    "Rating" INTEGER,
    "Rating Remark" TEXT,
    "User Name" VARCHAR(255),
    "Intercom User Email" VARCHAR(255),
    "License" VARCHAR(255),
    "User City" VARCHAR(255),
    "User Country" VARCHAR(255),
    "User Geo" VARCHAR(255),
    "Org Segment" VARCHAR(255),
    "User Org" VARCHAR(255),
    "ARR" NUMERIC(15, 2),
    "Account Geo" VARCHAR(255),
    "CSM" VARCHAR(255),
    "AE" VARCHAR(255),
    "AE Manager" VARCHAR(255),
    "IR (s)" NUMERIC(10, 2),
    "Adjusted IR (s)" NUMERIC(10, 2),
    "Waiting Time (s)" NUMERIC(10, 2),
    "Waiting Time (min)" NUMERIC(10, 2),
    "TTCA" INTEGER,
    "TTCU" INTEGER,
    "Week of Conversation" VARCHAR(255),
    "Assigned At" VARCHAR(255),
    "Adjusted Assigned At" VARCHAR(255),
    "TSE First Response At" VARCHAR(255),
    "TSE First Closed At" VARCHAR(255),
    "TSE Last Closed At" VARCHAR(255),
    "First TSE to Close" VARCHAR(255),
    "Last Closed By" VARCHAR(255),
    "Issue Type" VARCHAR(255),
    "Product Category" VARCHAR(255),
    "Root Cause" VARCHAR(255),
    "User Sentiment" VARCHAR(255),
    "Resolution Method" VARCHAR(255),
    "Org Created" VARCHAR(255),
    "User Created" VARCHAR(255),
    "Closed Same Day?" VARCHAR(10),
    "Reopened" VARCHAR(10),
    "Role" VARCHAR(255),
    "TSE Is Active" VARCHAR(10),
    "Zoom" VARCHAR(10),
    "Same TSE to Rate" VARCHAR(10),
    "Intercom Chat Status" VARCHAR(50),
    "Fiscal Q" VARCHAR(50),
    "Fiscal Quarter Month" VARCHAR(50)
);

-- Create indexes for better performance
CREATE INDEX idx_mrr_revenue_month ON mrr_data("Revenue Calendar Month");
CREATE INDEX idx_mrr_account_guid ON mrr_data("Account Guid");
CREATE INDEX idx_mrr_mrr_value ON mrr_data("Mrr") WHERE "Mrr" > 0;

CREATE INDEX idx_conv_created_pt ON conversations_data("Conversation Created PT");
CREATE INDEX idx_conv_status ON conversations_data("Intercom Chat Status");


-- ============================================================================
-- PostgreSQL COPY Command to Load CSV Data
-- ============================================================================
-- Run these commands after creating the tables:

-- COPY mrr_data FROM '/path/to/MONTHLY_RECURRING_REVENUE.csv' 
-- WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

-- COPY conversations_data FROM '/path/to/Intercom Conversations - Master Table - Sheet1.csv'
-- WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

-- ============================================================================
-- Alternative: Using psql \copy command (works from client machine)
-- ============================================================================
-- \copy mrr_data FROM 'MONTHLY_RECURRING_REVENUE.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');
-- \copy conversations_data FROM 'Intercom Conversations - Master Table - Sheet1.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

