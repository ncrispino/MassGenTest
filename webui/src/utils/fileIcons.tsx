/**
 * File Icons Utility
 *
 * Maps file extensions to lucide-react icons with appropriate colors.
 * Used in the workspace file tree for visual file type identification.
 */

import {
  Globe,
  Braces,
  FileCode,
  Palette,
  FileJson,
  FileText,
  Image,
  Film,
  FileSpreadsheet,
  Presentation,
  File,
  FileArchive,
  Database,
  Terminal,
  Settings,
  Lock,
  BookOpen,
  type LucideIcon,
} from 'lucide-react';

export interface FileIconConfig {
  icon: LucideIcon;
  className: string; // Tailwind color class
}

// Extension to icon mapping
const FILE_ICON_MAP: Record<string, FileIconConfig> = {
  // Web
  html: { icon: Globe, className: 'text-orange-400' },
  htm: { icon: Globe, className: 'text-orange-400' },

  // JavaScript
  js: { icon: Braces, className: 'text-yellow-400' },
  jsx: { icon: Braces, className: 'text-yellow-400' },
  mjs: { icon: Braces, className: 'text-yellow-400' },
  cjs: { icon: Braces, className: 'text-yellow-400' },

  // TypeScript
  ts: { icon: FileCode, className: 'text-blue-400' },
  tsx: { icon: FileCode, className: 'text-blue-400' },

  // Python
  py: { icon: FileCode, className: 'text-green-400' },
  pyw: { icon: FileCode, className: 'text-green-400' },
  pyx: { icon: FileCode, className: 'text-green-400' },
  ipynb: { icon: BookOpen, className: 'text-orange-400' },

  // Styles
  css: { icon: Palette, className: 'text-purple-400' },
  scss: { icon: Palette, className: 'text-pink-400' },
  sass: { icon: Palette, className: 'text-pink-400' },
  less: { icon: Palette, className: 'text-purple-400' },

  // Data formats
  json: { icon: FileJson, className: 'text-amber-400' },
  jsonc: { icon: FileJson, className: 'text-amber-400' },
  yaml: { icon: FileJson, className: 'text-red-400' },
  yml: { icon: FileJson, className: 'text-red-400' },
  xml: { icon: FileJson, className: 'text-orange-400' },
  toml: { icon: FileJson, className: 'text-gray-400' },

  // Markdown & Text
  md: { icon: FileText, className: 'text-gray-400' },
  mdx: { icon: FileText, className: 'text-gray-400' },
  txt: { icon: FileText, className: 'text-gray-500' },
  rst: { icon: FileText, className: 'text-gray-400' },

  // Images
  png: { icon: Image, className: 'text-pink-400' },
  jpg: { icon: Image, className: 'text-pink-400' },
  jpeg: { icon: Image, className: 'text-pink-400' },
  gif: { icon: Image, className: 'text-pink-400' },
  svg: { icon: Image, className: 'text-orange-400' },
  webp: { icon: Image, className: 'text-pink-400' },
  ico: { icon: Image, className: 'text-pink-400' },
  bmp: { icon: Image, className: 'text-pink-400' },

  // Video
  mp4: { icon: Film, className: 'text-red-400' },
  webm: { icon: Film, className: 'text-red-400' },
  mov: { icon: Film, className: 'text-red-400' },
  avi: { icon: Film, className: 'text-red-400' },
  mkv: { icon: Film, className: 'text-red-400' },

  // Office Documents
  pdf: { icon: FileText, className: 'text-red-500' },
  doc: { icon: FileText, className: 'text-blue-500' },
  docx: { icon: FileText, className: 'text-blue-500' },
  xls: { icon: FileSpreadsheet, className: 'text-green-500' },
  xlsx: { icon: FileSpreadsheet, className: 'text-green-500' },
  csv: { icon: FileSpreadsheet, className: 'text-green-400' },
  ppt: { icon: Presentation, className: 'text-orange-500' },
  pptx: { icon: Presentation, className: 'text-orange-500' },

  // Archives
  zip: { icon: FileArchive, className: 'text-amber-500' },
  tar: { icon: FileArchive, className: 'text-amber-500' },
  gz: { icon: FileArchive, className: 'text-amber-500' },
  rar: { icon: FileArchive, className: 'text-amber-500' },
  '7z': { icon: FileArchive, className: 'text-amber-500' },

  // Database
  sql: { icon: Database, className: 'text-blue-400' },
  db: { icon: Database, className: 'text-blue-400' },
  sqlite: { icon: Database, className: 'text-blue-400' },

  // Shell/Scripts
  sh: { icon: Terminal, className: 'text-green-400' },
  bash: { icon: Terminal, className: 'text-green-400' },
  zsh: { icon: Terminal, className: 'text-green-400' },
  fish: { icon: Terminal, className: 'text-green-400' },
  ps1: { icon: Terminal, className: 'text-blue-400' },
  bat: { icon: Terminal, className: 'text-gray-400' },
  cmd: { icon: Terminal, className: 'text-gray-400' },

  // Config
  ini: { icon: Settings, className: 'text-gray-400' },
  conf: { icon: Settings, className: 'text-gray-400' },
  config: { icon: Settings, className: 'text-gray-400' },
  env: { icon: Lock, className: 'text-yellow-500' },

  // Other languages
  java: { icon: FileCode, className: 'text-red-400' },
  kt: { icon: FileCode, className: 'text-purple-400' },
  go: { icon: FileCode, className: 'text-cyan-400' },
  rs: { icon: FileCode, className: 'text-orange-400' },
  rb: { icon: FileCode, className: 'text-red-500' },
  php: { icon: FileCode, className: 'text-indigo-400' },
  c: { icon: FileCode, className: 'text-blue-400' },
  cpp: { icon: FileCode, className: 'text-blue-500' },
  h: { icon: FileCode, className: 'text-purple-400' },
  hpp: { icon: FileCode, className: 'text-purple-400' },
  cs: { icon: FileCode, className: 'text-green-500' },
  swift: { icon: FileCode, className: 'text-orange-500' },
  r: { icon: FileCode, className: 'text-blue-400' },
  R: { icon: FileCode, className: 'text-blue-400' },
  lua: { icon: FileCode, className: 'text-blue-500' },
  pl: { icon: FileCode, className: 'text-purple-400' },
  scala: { icon: FileCode, className: 'text-red-400' },
};

// Special filenames that override extension-based icons
const SPECIAL_FILES: Record<string, FileIconConfig> = {
  'package.json': { icon: FileJson, className: 'text-green-400' },
  'package-lock.json': { icon: Lock, className: 'text-amber-400' },
  'tsconfig.json': { icon: Settings, className: 'text-blue-400' },
  'vite.config.ts': { icon: Settings, className: 'text-purple-400' },
  'vite.config.js': { icon: Settings, className: 'text-purple-400' },
  '.gitignore': { icon: Settings, className: 'text-orange-400' },
  '.env': { icon: Lock, className: 'text-yellow-500' },
  '.env.local': { icon: Lock, className: 'text-yellow-500' },
  '.env.example': { icon: Lock, className: 'text-yellow-400' },
  'Dockerfile': { icon: FileCode, className: 'text-blue-400' },
  'docker-compose.yml': { icon: Settings, className: 'text-blue-400' },
  'Makefile': { icon: Terminal, className: 'text-gray-400' },
  'README.md': { icon: BookOpen, className: 'text-blue-400' },
  'LICENSE': { icon: FileText, className: 'text-gray-500' },
  'requirements.txt': { icon: FileText, className: 'text-green-400' },
  'pyproject.toml': { icon: Settings, className: 'text-blue-400' },
};

// Default icon for unknown file types
const DEFAULT_ICON: FileIconConfig = {
  icon: File,
  className: 'text-gray-400',
};

/**
 * Get the icon configuration for a file based on its name/extension
 */
export function getFileIcon(filename: string): FileIconConfig {
  // Check special filenames first
  const lowerFilename = filename.toLowerCase();
  if (SPECIAL_FILES[filename] || SPECIAL_FILES[lowerFilename]) {
    return SPECIAL_FILES[filename] || SPECIAL_FILES[lowerFilename];
  }

  // Extract extension
  const parts = filename.split('.');
  if (parts.length > 1) {
    const ext = parts[parts.length - 1].toLowerCase();
    if (FILE_ICON_MAP[ext]) {
      return FILE_ICON_MAP[ext];
    }
  }

  return DEFAULT_ICON;
}

/**
 * Check if a file extension is recognized
 */
export function isKnownFileType(filename: string): boolean {
  const lowerFilename = filename.toLowerCase();
  if (SPECIAL_FILES[filename] || SPECIAL_FILES[lowerFilename]) {
    return true;
  }

  const parts = filename.split('.');
  if (parts.length > 1) {
    const ext = parts[parts.length - 1].toLowerCase();
    return ext in FILE_ICON_MAP;
  }

  return false;
}
