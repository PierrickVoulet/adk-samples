/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { google, Auth } from 'googleapis';
import * as http from 'node:http';
import * as net from 'node:net';
import * as url from 'node:url';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { logToFile } from '../utils/logger';
import open from '../utils/open-wrapper';
import { OAuthCredentialStorage } from './token-storage/oauth-credential-storage';
import { PROJECT_ROOT } from '../utils/paths';

const CREDENTIALS_PATH = path.join(PROJECT_ROOT, 'credentials.json');
const TOKEN_EXPIRY_BUFFER_MS = 5 * 60 * 1000; // 5 minutes

/**
 * An Authentication URL for updating the credentials of a Oauth2Client
 * as well as a promise that will resolve when the credentials have
 * been refreshed (or which throws error when refreshing credentials failed).
 */
interface OauthWebLogin {
    authUrl: string;
    loginCompletePromise: Promise<void>;
}

export class AuthManager {
    private client: Auth.OAuth2Client | null = null;
    private scopes: string[];

    constructor(scopes: string[]) {
        this.scopes = scopes;
    }

    private loadClientCredentials(): { client_id: string; client_secret: string } {
        if (!fs.existsSync(CREDENTIALS_PATH)) {
            throw new Error(
                `Could not find credentials.json at ${CREDENTIALS_PATH}. ` +
                'Please download the OAuth 2.0 Client ID JSON for a Desktop App from the Google Cloud Console ' +
                'and save it as "credentials.json" in this directory.'
            );
        }

        try {
            const content = fs.readFileSync(CREDENTIALS_PATH, 'utf-8');
            const json = JSON.parse(content);
            const installed = json.installed || json.web; // Accept both, though installed is standard for desktop

            if (!installed || !installed.client_id || !installed.client_secret) {
                throw new Error('Invalid credentials.json format. Missing client_id or client_secret in "installed" or "web" property.');
            }

            return {
                client_id: installed.client_id,
                client_secret: installed.client_secret
            };
        } catch (error) {
            throw new Error(`Failed to parse credentials.json: ${error}`);
        }
    }

    private isTokenExpiringSoon(credentials: Auth.Credentials): boolean {
        return !!(credentials.expiry_date &&
            credentials.expiry_date < Date.now() + TOKEN_EXPIRY_BUFFER_MS);
    }

    private async loadCachedCredentials(client: Auth.OAuth2Client): Promise<boolean> {
        const credentials = await OAuthCredentialStorage.loadCredentials();

        if (credentials) {
            // Check if saved token has required scopes
            const savedScopes = new Set(credentials.scope?.split(' ') ?? []);
            logToFile(`Cached token has scopes: ${[...savedScopes].join(', ')}`);

            // Note: We don't strictly enforce scope matching on load because scopes might come back in different order or format.
            // But if we clearly miss critical scopes, we might want to re-auth. 
            // For now, simpler check: if we have credentials, try to use them. 
            // If they fail later, we can handle it.
            // Actually, let's keep the check but make it robust.

            const missingScopes = this.scopes.filter(scope => !savedScopes.has(scope));

            if (missingScopes.length > 0) {
                logToFile(`Token cache *might* be missing scopes (strict check): ${missingScopes.join(', ')}`);
                // Proceeding cautiously - sometimes scopes are returned differently (e.g. without https://).
                // If it fails seriously, user can clear auth.
            }

            client.setCredentials(credentials);
            return true;
        }

        return false;
    }

    public async getAuthenticatedClient(): Promise<Auth.OAuth2Client> {
        logToFile('getAuthenticatedClient called');

        // 1. If we already have an in-memory client, check it.
        if (this.client) {
            // Let the client library handle simple access token expiration if refresh_token is present.
            // We can check if we want to force a refresh or save updates.
            return this.refreshClientIfNeeded(this.client);
        }

        // 2. Load credentials from file
        const { client_id, client_secret } = this.loadClientCredentials();

        const oAuth2Client = new google.auth.OAuth2(
            client_id,
            client_secret,
            'http://localhost' // Temporary redirect URI, will be overridden in generateAuthUrl/getToken
        );

        // Listen for new tokens to save them
        oAuth2Client.on('tokens', async (tokens) => {
            logToFile('Tokens refreshed event received');
            await this.saveCredentials(tokens);
        });

        // 3. Try key storage
        if (await this.loadCachedCredentials(oAuth2Client)) {
            logToFile('Loaded credentials from storage');
            this.client = oAuth2Client;
            return this.refreshClientIfNeeded(this.client);
        }

        // 4. Start new Auth Flow
        const webLogin = await this.authWithWeb(oAuth2Client);
        await open(webLogin.authUrl);
        console.error('Waiting for authentication...');

        // Add timeout
        const authTimeout = 5 * 60 * 1000;
        const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => {
                reject(new Error('Authentication timed out after 5 minutes.'));
            }, authTimeout);
        });

        await Promise.race([webLogin.loginCompletePromise, timeoutPromise]);

        this.client = oAuth2Client;
        return this.client;
    }

    private async refreshClientIfNeeded(client: Auth.OAuth2Client): Promise<Auth.OAuth2Client> {
        // Check expiry
        if (!client.credentials || !client.credentials.expiry_date) {
            return client;
        }

        if (this.isTokenExpiringSoon(client.credentials)) {
            logToFile('Token expiring soon, refreshing...');
            try {
                // This method automatically refreshes if refresh_token is present
                // and updates the client credentials.
                // The 'tokens' event listener should catch the new tokens and save them.
                await client.getAccessToken();
                logToFile('Token check/refresh complete');
            } catch (e) {
                logToFile(`Error refreshing token: ${e}`);
                // If refresh fails, we might need to re-auth, but let's throw for now or return existing
                // and let the caller fail.
                // Better to clear credentials if refresh token is invalid.
                // throw e; 
            }
        }
        return client;
    }

    private async saveCredentials(tokens: Auth.Credentials) {
        try {
            const current = await OAuthCredentialStorage.loadCredentials() || {};
            const merged = {
                ...tokens,
                refresh_token: tokens.refresh_token || current.refresh_token
            };
            await OAuthCredentialStorage.saveCredentials(merged);
            logToFile('Credentials saved.');
        } catch (e) {
            logToFile(`Error saving credentials: ${e}`);
        }
    }

    public async clearAuth(): Promise<void> {
        logToFile('Clearing authentication...');
        this.client = null;
        await OAuthCredentialStorage.clearCredentials();
        logToFile('Authentication cleared.');
    }

    // Explicit refresh if needed manually
    public async refreshToken(): Promise<void> {
        if (this.client) {
            await this.client.getAccessToken();
        }
    }

    private async getAvailablePort(): Promise<number> {
        return new Promise((resolve, reject) => {
            const server = net.createServer();
            server.listen(0, () => {
                const address = server.address()! as net.AddressInfo;
                server.close(() => resolve(address.port));
            });
            server.on('error', reject);
        });
    }

    private async authWithWeb(client: Auth.OAuth2Client): Promise<OauthWebLogin> {
        logToFile(`Starting OAuth flow.`);
        const port = await this.getAvailablePort();
        const redirectUri = `http://localhost:${port}/oauth2callback`;

        // Update client redirect URI for this flow
        (client as any).redirectUri = redirectUri;

        const authUrl = client.generateAuthUrl({
            redirect_uri: redirectUri,
            access_type: 'offline', // Essential for refresh_token
            scope: this.scopes,
            prompt: 'consent', // Force consent logic to ensure refresh_token
        });

        const loginCompletePromise = new Promise<void>((resolve, reject) => {
            const server = http.createServer(async (req, res) => {
                try {
                    if (!req.url) return;

                    const requestUrl = new url.URL(req.url, `http://localhost:${port}`);

                    if (requestUrl.pathname !== '/oauth2callback') {
                        res.statusCode = 404;
                        res.end('Not found');
                        return;
                    }

                    const code = requestUrl.searchParams.get('code');
                    const error = requestUrl.searchParams.get('error');

                    if (error) {
                        res.end('Authentication failed.');
                        reject(new Error(`Authentication failed: ${error}`));
                        return;
                    }

                    if (code) {
                        const { tokens } = await client.getToken(code);
                        client.setCredentials(tokens);
                        await this.saveCredentials(tokens);

                        res.end('Authentication successful! You can close this tab.');
                        resolve();
                    }
                } catch (e) {
                    reject(e);
                } finally {
                    server.close();
                }
            });

            server.listen(port, () => {
                logToFile(`Listening on port ${port} for OAuth callback...`);
            });

            server.on('error', reject);
        });

        return {
            authUrl,
            loginCompletePromise
        };
    }
}
