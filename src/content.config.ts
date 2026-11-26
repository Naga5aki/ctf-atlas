import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const tag = z.enum(['文件格式', '编码', '压缩包', '流量', '时间线', 'Docker', '日志', '文件系统', '容器', 'Git', 'RSA', '程序校验']);

const articleSchema = z.object({
  title: z.string(),
  summary: z.string(),
  module: z.enum(['Web', 'Misc', 'Reverse', 'Crypto', 'Forensics']),
  topic: z.string().optional(),
  track: z.string().optional(),
  tags: z.array(tag).max(3),
  status: z.enum(['已整理', '待验证']),
  sourceIds: z.array(z.string()).default([]),
  challengeIds: z.array(z.string()).default([]),
  relatedIds: z.array(z.string()).default([]),
  updated: z.coerce.date(),
});

const toolSchema = z.object({
  title: z.string(),
  summary: z.string(),
  module: z.enum(['Web', 'Misc', 'Reverse', 'Crypto', 'Forensics']),
  topic: z.string(),
  locationPaths: z.array(z.string()),
  sourceIds: z.array(z.string()),
  updated: z.coerce.date(),
});

const knowledge = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/knowledge' }),
  schema: articleSchema,
});
const writeups = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/writeups' }),
  schema: articleSchema,
});

const tools = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/tools' }),
  schema: toolSchema,
});

export const collections = { knowledge, writeups, tools };
