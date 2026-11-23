import React from 'react';
import { orderWorkspacesByFavorites } from './workspaces';

/** 工作空间下拉选项，收藏项带黄色星标（两处表单共用）。 */
export function buildWorkspaceOptions(workspaces, favorites) {
  return orderWorkspacesByFavorites(workspaces, favorites).map((ws) => ({
    value: ws.workspace_name,
    label: ws.isFavorite ? (
      <span>
        <span style={{ color: '#f5a623' }}>★</span> {ws.workspace_name}
      </span>
    ) : (
      ws.workspace_name
    )
  }));
}

/** 迭代列表：默认空间的源迭代置顶（两处表单共用）。 */
export function sortSprintsWithPreferred(list, preferredId) {
  const result = [...(list || [])];
  if (!preferredId) return result;
  return result.sort((a, b) => {
    if (a.object_id === preferredId) return -1;
    if (b.object_id === preferredId) return 1;
    return 0;
  });
}
