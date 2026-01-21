/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { promises as fs } from 'node:fs';
import * as path from 'node:path';
import type { OAuthCredentials, TokenStorage } from './types';
import { logToFile } from '../../utils/logger';
import { ENCRYPTED_TOKEN_PATH } from '../../utils/paths';

export class FileTokenStorage implements TokenStorage {
  private readonly serviceName: string;
  private readonly tokenFilePath: string;

  private constructor(serviceName: string) {
    this.serviceName = serviceName;
    this.tokenFilePath = ENCRYPTED_TOKEN_PATH;
  }

  static async create(serviceName: string): Promise<FileTokenStorage> {
    return new FileTokenStorage(serviceName);
  }

  private validateCredentials(credentials: OAuthCredentials): void {
    if (!credentials.serverName) {
      throw new Error('Server name is required');
    }
    if (!credentials.token) {
      throw new Error('Token is required');
    }
    if (!credentials.token.accessToken && !credentials.token.refreshToken) {
      throw new Error('Access token or refresh token is required');
    }
    if (!credentials.token.tokenType) {
      throw new Error('Token type is required');
    }
  }

  private async ensureDirectoryExists(): Promise<void> {
    const dir = path.dirname(this.tokenFilePath);
    await fs.mkdir(dir, { recursive: true, mode: 0o700 });
  }

  private async loadTokens(): Promise<Map<string, OAuthCredentials>> {
    try {
      const data = await fs.readFile(this.tokenFilePath, 'utf-8');
      const tokens = JSON.parse(data) as Record<string, OAuthCredentials>;
      return new Map(Object.entries(tokens));
    } catch (error: unknown) {
      const err = error as NodeJS.ErrnoException & { message?: string };
      if (err.code === 'ENOENT') {
        logToFile('Token file does not exist');
        return new Map<string, OAuthCredentials>();
      }
      if (
        err instanceof SyntaxError ||
        err.message?.includes('Unexpected token') ||
        err.message?.includes('Invalid encrypted data format') // Legacy compat
      ) {
        logToFile('Token file corrupted or invalid JSON');
        return new Map<string, OAuthCredentials>();
      }
      throw error;
    }
  }

  private async saveTokens(
    tokens: Map<string, OAuthCredentials>,
  ): Promise<void> {
    await this.ensureDirectoryExists();

    const data = Object.fromEntries(tokens);
    const json = JSON.stringify(data, null, 2);

    // Save as plain JSON with restrictive permissions
    await fs.writeFile(this.tokenFilePath, json, { mode: 0o600 });
  }

  async getCredentials(serverName: string): Promise<OAuthCredentials | null> {
    const tokens = await this.loadTokens();
    const credentials = tokens.get(serverName);

    if (!credentials) {
      return null;
    }

    return credentials;
  }

  async setCredentials(credentials: OAuthCredentials): Promise<void> {
    this.validateCredentials(credentials);

    const tokens = await this.loadTokens();
    const updatedCredentials: OAuthCredentials = {
      ...credentials,
      updatedAt: Date.now(),
    };

    tokens.set(credentials.serverName, updatedCredentials);
    await this.saveTokens(tokens);
  }

  async deleteCredentials(serverName: string): Promise<void> {
    const tokens = await this.loadTokens();

    if (!tokens.has(serverName)) {
      throw new Error(`No credentials found for ${serverName}`);
    }

    tokens.delete(serverName);

    if (tokens.size === 0) {
      try {
        await fs.unlink(this.tokenFilePath);
      } catch (error: unknown) {
        const err = error as NodeJS.ErrnoException;
        if (err.code !== 'ENOENT') {
          throw error;
        }
      }
    } else {
      await this.saveTokens(tokens);
    }
  }

  async listServers(): Promise<string[]> {
    const tokens = await this.loadTokens();
    return Array.from(tokens.keys());
  }

  async getAllCredentials(): Promise<Map<string, OAuthCredentials>> {
    const tokens = await this.loadTokens();
    const result = new Map<string, OAuthCredentials>();

    for (const [serverName, credentials] of tokens) {
      try {
        this.validateCredentials(credentials);
        result.set(serverName, credentials);
      } catch (error) {
        console.error(`Skipping invalid credentials for ${serverName}:`, error);
      }
    }

    return result;
  }

  async clearAll(): Promise<void> {
    try {
      await fs.unlink(this.tokenFilePath);
    } catch (error: unknown) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'ENOENT') {
        throw error;
      }
    }
  }
}