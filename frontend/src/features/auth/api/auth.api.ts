/**
 * DTOs here mirror the backend's wire format (snake_case, per its Pydantic
 * schemas) on purpose, kept separate from the camelCase domain types in
 * ../types.ts — the mapping functions are the one place that boundary is
 * allowed to leak.
 */

import { httpClient } from "@/services/http";

import type { AuthTokens, LoginPayload, RegisterPayload, User, UserRole } from "../types";

interface TokenResponseDto {
  access_token: string;
  refresh_token: string;
}

interface UserDto {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

function mapTokens(dto: TokenResponseDto): AuthTokens {
  return {
    accessToken: dto.access_token,
    refreshToken: dto.refresh_token,
  };
}

function mapUser(dto: UserDto): User {
  return {
    id: dto.id,
    email: dto.email,
    fullName: dto.full_name,
    role: dto.role,
    isActive: dto.is_active,
  };
}

export const authApi = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await httpClient.post<UserDto>("/auth/register", {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
    });
    return mapUser(data);
  },

  async login(payload: LoginPayload): Promise<AuthTokens> {
    const { data } = await httpClient.post<TokenResponseDto>("/auth/login", payload);
    return mapTokens(data);
  },

  async logout(refreshToken: string): Promise<void> {
    await httpClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  async me(): Promise<User> {
    const { data } = await httpClient.get<UserDto>("/auth/me");
    return mapUser(data);
  },
};
