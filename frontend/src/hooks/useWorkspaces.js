import { useEffect, useState } from 'react';
import { fetchWorkspaces } from '../api';

/** 拉取当前 cookie 可见的工作空间，卸载后自动取消状态更新。enabled 可控制是否请求。 */
export function useWorkspaces(cookie, enabled = true) {
  const [workspaces, setWorkspaces] = useState([]);

  useEffect(() => {
    let cancelled = false;
    if (!enabled || !cookie?.trim()) {
      setWorkspaces([]);
      return undefined;
    }
    (async () => {
      try {
        const data = await fetchWorkspaces(cookie);
        if (cancelled || !data.success) return;
        setWorkspaces(data.data || []);
      } catch (err) {
        console.error(err);
        if (!cancelled) setWorkspaces([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [cookie, enabled]);

  return workspaces;
}
