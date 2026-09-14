import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

export interface WoolItem {
  id: string;
  title: string;
  category: string;
  platform: string;
  summary: string;
  link: string;
  coupon: string;
  originalPrice: number | null;
  finalPrice: number | null;
  expireAt: string;
  isHot: boolean;
}

export interface DayData {
  date: string;
  items: WoolItem[];
}

const DATA_DIR = join(process.cwd(), 'src', 'data');

/** 全部可用日期，新→旧排序 */
export function listDates(): string[] {
  if (!existsSync(DATA_DIR)) return [];
  return readdirSync(DATA_DIR)
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace('.json', ''))
    .sort()
    .reverse();
}

export function loadDay(date: string): DayData | null {
  const file = join(DATA_DIR, `${date}.json`);
  if (!existsSync(file)) return null;
  return JSON.parse(readFileSync(file, 'utf-8')) as DayData;
}

/** 最新一天的数据 */
export function loadLatest(): DayData | null {
  const dates = listDates();
  return dates.length ? loadDay(dates[0]) : null;
}

export const CATEGORIES = ['电商券', '外卖红包', '签到福利', '白嫖活动'] as const;

export const CATEGORY_SLUGS: Record<string, string> = {
  电商券: 'dianshang',
  外卖红包: 'waimai',
  签到福利: 'qiandao',
  白嫖活动: 'baipiao',
};

export const SLUG_TO_CATEGORY: Record<string, string> = Object.fromEntries(
  Object.entries(CATEGORY_SLUGS).map(([k, v]) => [v, k]),
);

/**
 * 比价分组：按 title 关键词归并同商品，跨平台取最低价标注。
 * 简单规则：finalPrice 非空的条目按 title 去平台差异后分组。
 */
export function groupCompareItems(items: WoolItem[]): Map<string, WoolItem[]> {
  const groups = new Map<string, WoolItem[]>();
  for (const item of items) {
    if (item.finalPrice == null) continue;
    // 归并键：标题去掉平台词与空格，取前 10 字
    const key = item.title.replace(/多平台比价|\s/g, '').slice(0, 10);
    const list = groups.get(key) ?? [];
    list.push(item);
    groups.set(key, list);
  }
  return groups;
}

export function lowestPrice(group: WoolItem[]): number {
  return Math.min(...group.map((i) => i.finalPrice ?? Infinity));
}
