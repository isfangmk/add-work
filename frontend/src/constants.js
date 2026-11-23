// 应用级常量，集中管理避免散落重复

export const APP_VERSION = 'v2.0';
export const REPO_URL = 'https://github.com/isfangmk/add-work';

// 分享链接用当前站点地址，避免硬编码内网 IP/端口
export const SHARE_URL = typeof window !== 'undefined'
  ? `${window.location.origin}/add-work/`
  : '/add-work/';
