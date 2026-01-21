/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import path from 'node:path';
import * as fs from 'node:fs';

function findProjectRoot(): string {
  let dir = __dirname;
  while (dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, 'package.json'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  // Fallback to process.cwd() if not found (e.g. running from a different context)
  // or just throw if strictly required. For now, try fallback or just throw with better message.
  // Actually, package.json should always be found if built/packaged correctly.

  // Try one more check at cwd in case __dirname is weird in some environments
  if (fs.existsSync(path.join(process.cwd(), 'package.json'))) {
    return process.cwd();
  }

  throw new Error(
    `Could not find project root containing package.json. Traversed up from ${__dirname}.`,
  );
}

// Construct an absolute path to the project root.
export const PROJECT_ROOT = findProjectRoot();
export const ENCRYPTED_TOKEN_PATH = path.join(
  PROJECT_ROOT,
  'token.json',
);

