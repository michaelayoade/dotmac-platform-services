"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
export interface PartnerDashboardStats {
  total_customers: number;
  active_customers: number;
  total_revenue_generated: number;
  total_commissions_earned: number;
  total_commissions_paid: number;
  pending_commissions: number;
  total_referrals: number;
  converted_referrals: number;
  pending_referrals: number;
  conversion_rate: number;
  current_tier: string;
  commission_model: string;
  default_commission_rate: number;
}

export interface PartnerProfile {
  id: string;
  partner_number: string;
  company_name: string;
  legal_name?: string;
  website?: string;
  status: string;
  tier: string;
  commission_model: string;
  default_commission_rate?: number;
  primary_email: string;
  billing_email?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface PartnerReferral {
  id: string;
  partner_id: string;
  lead_name: string;
  lead_email: string;
  lead_phone?: string;
  company_name?: string;
  status: "new" | "contacted" | "qualified" | "converted" | "lost";
  estimated_value?: number;
  actual_value?: number;
  converted_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PartnerCommission {
  id: string;
  partner_id: string;
  customer_id: string;
  invoice_id?: string;
  amount: number;
  commission_rate: number;
  commission_amount: number;
  status: "pending" | "approved" | "paid" | "disputed" | "cancelled";
  event_date: string;
  payment_date?: string;
  notes?: string;
  created_at: string;
}

export interface PartnerCustomer {
  id: string;
  customer_id: string;
  customer_name: string;
  engagement_type: "direct" | "referral" | "reseller" | "affiliate";
  custom_commission_rate?: number;
  total_revenue: number;
  total_commissions: number;
  start_date: string;
  end_date?: string;
  is_active: boolean;
}

// API Functions
async function fetchPartnerDashboard(): Promise<PartnerDashboardStats> {
  const response = await fetch(`${API_BASE}/api/v1/partners/portal/dashboard`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard data");
  }

  return response.json();
}

async function fetchPartnerProfile(): Promise<PartnerProfile> {
  const response = await fetch(`${API_BASE}/api/v1/partners/portal/profile`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch profile");
  }

  return response.json();
}

async function updatePartnerProfile(
  data: Partial<PartnerProfile>
): Promise<PartnerProfile> {
  const response = await fetch(`${API_BASE}/api/v1/partners/portal/profile`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update profile");
  }

  return response.json();
}

async function fetchPartnerReferrals(): Promise<PartnerReferral[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/partners/portal/referrals`,
    {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch referrals");
  }

  return response.json();
}

async function submitReferral(data: {
  lead_name: string;
  lead_email: string;
  lead_phone?: string;
  company_name?: string;
  estimated_value?: number;
  notes?: string;
}): Promise<PartnerReferral> {
  const response = await fetch(
    `${API_BASE}/api/v1/partners/portal/referrals`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to submit referral");
  }

  return response.json();
}

async function fetchPartnerCommissions(): Promise<PartnerCommission[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/partners/portal/commissions`,
    {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch commissions");
  }

  return response.json();
}

async function fetchPartnerCustomers(): Promise<PartnerCustomer[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/partners/portal/customers`,
    {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch customers");
  }

  return response.json();
}

// Hooks
export function usePartnerDashboard() {
  return useQuery({
    queryKey: ["partner-portal-dashboard"],
    queryFn: fetchPartnerDashboard,
  });
}

export function usePartnerProfile() {
  return useQuery({
    queryKey: ["partner-portal-profile"],
    queryFn: fetchPartnerProfile,
  });
}

export function useUpdatePartnerProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updatePartnerProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-portal-profile"] });
      queryClient.invalidateQueries({ queryKey: ["partner-portal-dashboard"] });
    },
  });
}

export function usePartnerReferrals() {
  return useQuery({
    queryKey: ["partner-portal-referrals"],
    queryFn: fetchPartnerReferrals,
  });
}

export function useSubmitReferral() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitReferral,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-portal-referrals"] });
      queryClient.invalidateQueries({ queryKey: ["partner-portal-dashboard"] });
    },
  });
}

export function usePartnerCommissions() {
  return useQuery({
    queryKey: ["partner-portal-commissions"],
    queryFn: fetchPartnerCommissions,
  });
}

export function usePartnerCustomers() {
  return useQuery({
    queryKey: ["partner-portal-customers"],
    queryFn: fetchPartnerCustomers,
  });
}
