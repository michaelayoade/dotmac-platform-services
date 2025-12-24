/**
 * NextAuth Configuration
 *
 * Handles authentication with the DotMac Platform API
 */

import { type NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const API_URL = process.env.API_URL || "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Authenticate with backend API
          const response = await fetch(`${API_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data = await response.json();
          const accessToken = data.access_token ?? data.accessToken;
          const refreshToken = data.refresh_token ?? data.refreshToken;

          if (!accessToken) {
            return null;
          }

          let userData = data.user;
          if (!userData) {
            const profileResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
              headers: { Authorization: `Bearer ${accessToken}` },
            });
            if (profileResponse.ok) {
              userData = await profileResponse.json();
            }
          }

          if (!userData) {
            return null;
          }

          const userId = userData.id ?? userData.user_id ?? userData.userId;
          if (!userId) {
            return null;
          }

          const roles = userData.roles ?? [];
          const primaryRole = userData.role ?? roles[0] ?? "viewer";

          return {
            id: userId,
            email: userData.email ?? credentials.email,
            name:
              userData.full_name ??
              userData.name ??
              userData.username ??
              userData.email ??
              credentials.email,
            role: primaryRole,
            roles,
            permissions: userData.permissions ?? [],
            tenants: userData.tenants ?? [],
            tenantId: userData.tenant_id ?? userData.tenantId ?? null,
            partnerId: userData.partner_id ?? userData.partnerId ?? null,
            isPlatformAdmin:
              userData.is_platform_admin ?? userData.isPlatformAdmin ?? false,
            accessToken,
            refreshToken,
          };
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user, trigger, session }) {
      // Initial sign in
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.role = user.role;
        token.roles = user.roles;
        token.permissions = user.permissions;
        token.tenants = user.tenants;
        token.tenantId = user.tenantId;
        token.partnerId = user.partnerId;
        token.isPlatformAdmin = user.isPlatformAdmin;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
      }

      // Handle session update
      if (trigger === "update" && session) {
        return { ...token, ...session };
      }

      // Token refresh logic would go here
      // Check if access token is expired and refresh if needed

      return token;
    },

    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.role = token.role as string;
        session.user.roles = token.roles as string[];
        session.user.permissions = token.permissions as string[];
        session.user.tenants = token.tenants as unknown[];
        session.user.tenantId = token.tenantId as string | null;
        session.user.partnerId = token.partnerId as string | null;
        session.user.isPlatformAdmin = token.isPlatformAdmin as boolean;
        session.accessToken = token.accessToken as string;
      }
      return session;
    },
  },

  pages: {
    signIn: "/login",
    signOut: "/login",
    error: "/login",
  },

  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },

  secret: process.env.NEXTAUTH_SECRET,

  debug: process.env.NODE_ENV === "development",
};

// Type augmentation for NextAuth
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      email: string;
      name: string;
      role: string;
      roles: string[];
      permissions: string[];
      tenants: unknown[];
      tenantId: string | null;
      partnerId: string | null;
      isPlatformAdmin: boolean;
    };
    accessToken: string;
  }

  interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    roles: string[];
    permissions: string[];
    tenants: unknown[];
    tenantId: string | null;
    partnerId: string | null;
    isPlatformAdmin: boolean;
    accessToken: string;
    refreshToken: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    email: string;
    name: string;
    role: string;
    roles: string[];
    permissions: string[];
    tenants: unknown[];
    tenantId: string | null;
    partnerId: string | null;
    isPlatformAdmin: boolean;
    accessToken: string;
    refreshToken: string;
  }
}
