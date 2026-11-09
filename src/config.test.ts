import { describe, it, expect } from 'vitest';
import { SECTIONS, getSection, SITE } from './config';

describe('SECTIONS', () => {
  it('包含五个分区且顺序固定', () => {
    expect(SECTIONS.map((s) => s.key)).toEqual(['vps', 'fsae', 'rm', 'ai', 'resources']);
  });

  it('每个分区都有中文名称和描述', () => {
    for (const s of SECTIONS) {
      expect(s.name.length).toBeGreaterThan(0);
      expect(s.description.length).toBeGreaterThan(0);
    }
  });
});

describe('getSection', () => {
  it('已知 key 返回分区', () => {
    expect(getSection('fsae')?.name).toBe('大学生方程式赛车');
  });

  it('未知 key 返回 undefined', () => {
    expect(getSection('unknown')).toBeUndefined();
  });
});

describe('SITE', () => {
  it('站点 URL 不带末尾斜杠', () => {
    expect(SITE.url.endsWith('/')).toBe(false);
  });
});
