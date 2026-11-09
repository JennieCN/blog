export type SectionKey = 'vps' | 'fsae' | 'rm' | 'ai' | 'resources';

export interface Section {
  key: SectionKey;
  name: string;
  description: string;
}

export const SECTIONS: Section[] = [
  { key: 'vps', name: 'VPS 科普', description: '服务器、线路、代理与自建服务的入门笔记' },
  { key: 'fsae', name: '大学生方程式赛车', description: 'FSAE 车队的技术与比赛记录' },
  { key: 'rm', name: 'RoboMaster', description: '机器人竞赛的机械、电控与算法' },
  { key: 'ai', name: 'AI', description: '模型、工具与实践中的思考' },
  { key: 'resources', name: '资源', description: '值得收藏的工具、文档与素材' },
];

export const SITE = {
  title: '我的博客',
  description: '记录技术、竞赛与思考',
  author: 'JennieCN',
  url: 'https://blog.mycampusmail.com',
  walineServerURL: 'https://blog-waline-snowy-psi.vercel.app',
};

export function getSection(key: string): Section | undefined {
  return SECTIONS.find((s) => s.key === key);
}
