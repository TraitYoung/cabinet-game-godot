import fs from 'node:fs';
import path from 'node:path';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

const ROOT_DIR = import.meta.dirname;

const ASSET_ROOTS: Record<string, string> = {
  '/game-assets/palace/': path.resolve(ROOT_DIR, 'assets/palace'),
  '/game-assets/characters/': path.resolve(ROOT_DIR, 'assets/characters'),
};

function createGameAssetsMiddleware(): (
  req: IncomingMessage,
  res: ServerResponse,
  next: () => void,
) => void {
  return (req, res, next) => {
    const rawUrl = req.url ?? '';
    const cleanUrl = rawUrl.split('?')[0] ?? '';

    for (const [prefix, dirRoot] of Object.entries(ASSET_ROOTS)) {
      if (!cleanUrl.startsWith(prefix)) {
        continue;
      }
      const relRaw = decodeURIComponent(cleanUrl.slice(prefix.length));
      if (relRaw.includes('..') || relRaw.includes('\0')) {
        res.statusCode = 403;
        res.end('Forbidden');
        return;
      }
      const resolved = path.resolve(dirRoot, relRaw);
      const normalizedRoot = dirRoot.endsWith(path.sep) ? dirRoot : `${dirRoot}${path.sep}`;
      if (!resolved.startsWith(normalizedRoot)) {
        res.statusCode = 403;
        res.end('Forbidden');
        return;
      }
      if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
        res.statusCode = 404;
        res.end('Not found');
        return;
      }
      const ext = path.extname(resolved).toLowerCase();
      res.setHeader('Content-Type', ext === '.png' ? 'image/png' : 'application/octet-stream');
      fs.createReadStream(resolved).pipe(res);
      return;
    }

    next();
  };
}

function copyPngTree(srcDir: string, dstDir: string): void {
  if (!fs.existsSync(srcDir)) {
    return;
  }
  const entries = fs.readdirSync(srcDir, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(srcDir, entry.name);
    const dstPath = path.join(dstDir, entry.name);
    if (entry.isDirectory()) {
      copyPngTree(srcPath, dstPath);
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.png')) {
      fs.mkdirSync(dstDir, { recursive: true });
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

function serveGameAssetsPlugin(): Plugin {
  return {
    name: 'serve-game-assets',
    configureServer(server) {
      server.middlewares.use(createGameAssetsMiddleware());
    },
    configurePreviewServer(server) {
      server.middlewares.use(createGameAssetsMiddleware());
    },
    closeBundle() {
      const distRoot = path.resolve(ROOT_DIR, 'dist/game-assets');
      copyPngTree(path.resolve(ROOT_DIR, 'assets/palace'), path.join(distRoot, 'palace'));
      copyPngTree(path.resolve(ROOT_DIR, 'assets/characters'), path.join(distRoot, 'characters'));
    },
  };
}

export default defineConfig({
  plugins: [react(), serveGameAssetsPlugin()],
  server: {
    host: true,
    port: 5173,
  },
  preview: {
    host: true,
    port: 4173,
  },
});
