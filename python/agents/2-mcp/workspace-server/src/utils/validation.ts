/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

/**
 * Email validation schema
 * Validates email format according to RFC 5322
 */
export const emailSchema = z.string().email('Invalid email format');

/**
 * Validates multiple email addresses (for CC/BCC fields)
 */
export const emailArraySchema = z.union([
    emailSchema,
    z.array(emailSchema)
]);

/**
 * ISO 8601 datetime validation schema
 * Accepts formats like:
 * - 2024-01-15T10:30:00Z
 * - 2024-01-15T10:30:00-05:00
 * - 2024-01-15T10:30:00.000Z
 */
export const iso8601DateTimeSchema = z.string().refine(
    (val) => {
        const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})$/;
        if (!iso8601Regex.test(val)) return false;

        // Additional check: ensure it's a valid date
        const date = new Date(val);
        return !isNaN(date.getTime());
    },
    {
        message: 'Invalid ISO 8601 datetime format. Expected format: YYYY-MM-DDTHH:mm:ss[.sss][Z|±HH:mm]'
    }
);

/**
 * Google Drive document/file ID validation
 * Google IDs are typically alphanumeric strings with hyphens and underscores
 */
export const googleDocumentIdSchema = z.string().regex(
    /^[a-zA-Z0-9_-]+$/,
    'Invalid document ID format. Document IDs should only contain letters, numbers, hyphens, and underscores'
);

/**
 * Helper function to extract document ID from URL or return the ID if already valid
 */
export function extractDocumentId(urlOrId: string): string {
    // First check if it's already a valid ID
    if (googleDocumentIdSchema.safeParse(urlOrId).success) {
        return urlOrId;
    }

    // Try to extract from URL
    const urlMatch = urlOrId.match(/\/d\/([a-zA-Z0-9_-]+)/);
    if (urlMatch && urlMatch[1]) {
        return urlMatch[1];
    }

    throw new Error('Invalid document ID or URL');
}

/**
 * Validation error class for consistent error handling
 */
export class ValidationError extends Error {
    constructor(
        message: string,
        public field: string,
        public value: unknown
    ) {
        super(message);
        this.name = 'ValidationError';
    }
}