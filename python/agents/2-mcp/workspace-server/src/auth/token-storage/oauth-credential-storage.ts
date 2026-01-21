/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type Credentials } from 'google-auth-library';
import { FileTokenStorage } from './file-token-storage';
import type { OAuthCredentials } from './types';

const MAIN_ACCOUNT_KEY = 'main-account';

export class OAuthCredentialStorage {
  // Use a lazy-initialized singleton promise pattern to handle async creation
  private static storagePromise: Promise<FileTokenStorage> | null = null;

  private static async getStorage(): Promise<FileTokenStorage> {
    if (!this.storagePromise) {
      this.storagePromise = FileTokenStorage.create(MAIN_ACCOUNT_KEY);
    }
    return this.storagePromise;
  }

  /**
   * Load cached OAuth credentials
   */
  static async loadCredentials(): Promise<Credentials | null> {
    try {
      const storage = await this.getStorage();
      const credentials = await storage.getCredentials(MAIN_ACCOUNT_KEY);

      if (credentials?.token) {
        const { accessToken, refreshToken, expiresAt, tokenType, scope } =
          credentials.token;
        // Convert from OAuthCredentials format to Google Credentials format
        const googleCreds: Credentials = {
          access_token: accessToken,
          refresh_token: refreshToken || undefined,
          token_type: tokenType || undefined,
          scope: scope || undefined,
        };

        if (expiresAt) {
          googleCreds.expiry_date = expiresAt;
        }

        return googleCreds;
      }

      return null;
    } catch (error: unknown) {
      throw error;
    }
  }

  /**
   * Save OAuth credentials
   */
  static async saveCredentials(credentials: Credentials): Promise<void> {
    // Convert Google Credentials to OAuthCredentials format
    const mcpCredentials: OAuthCredentials = {
      serverName: MAIN_ACCOUNT_KEY,
      token: {
        accessToken: credentials.access_token || undefined,
        refreshToken: credentials.refresh_token || undefined,
        tokenType: credentials.token_type || 'Bearer',
        scope: credentials.scope || undefined,
        expiresAt: credentials.expiry_date || undefined,
      },
      updatedAt: Date.now(),
    };

    const storage = await this.getStorage();
    await storage.setCredentials(mcpCredentials);
  }

  /**
   * Clear cached OAuth credentials
   */
  static async clearCredentials(): Promise<void> {
    try {
      const storage = await this.getStorage();
      await storage.deleteCredentials(MAIN_ACCOUNT_KEY);
    } catch (error: unknown) {
      throw error;
    }
  }
}