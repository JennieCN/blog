export type SectionKey = 'vps' | 'fsae' | 'rm' | 'ai' | 'resources';

export interface Section {
  key: SectionKey;
  name: string;
  description: string;
  color: string;
  icon: 'server' | 'flag' | 'cpu' | 'code' | 'feather';
}

export const SECTIONS: Section[] = [
  { key: 'vps', name: 'VPS 科普', description: '服务器、线路、代理与自建服务的入门笔记', color: '#2563eb', icon: 'server' },
  { key: 'fsae', name: '大学生方程式赛车', description: 'FSAE 车队的技术与比赛记录', color: '#b8461f', icon: 'flag' },
  { key: 'rm', name: 'RoboMaster', description: '机器人竞赛的机械、电控与算法', color: '#1d6e62', icon: 'cpu' },
  { key: 'ai', name: 'AI', description: '模型、工具与实践中的思考', color: '#6f42c1', icon: 'code' },
  { key: 'resources', name: '资源', description: '值得收藏的工具、文档与素材', color: '#8a5a00', icon: 'feather' },
];

export const SITE = {
  title: '融夕的书',
  description: 'VPS、赛车、机器人、AI 与资源笔记',
  author: '融夕',
  authorBio: '聚焦 VPS 网络基建、大学生方程式赛车（FSAE）、RoboMaster 机器人与 AI 工程实践。长文沉淀系统经验，社区讨论当下问题。',
  url: 'https://blog.mycampusmail.com',
  forumUrl: 'https://qa.mycampusmail.com',
  walineServerURL: 'https://blog-waline-snowy-psi.vercel.app',
};

export function getSection(key: string): Section | undefined {
  return SECTIONS.find((s) => s.key === key);
}
