export interface FavoriteWorkspace {
  workspace_key: string;
  workspace_name: string;
}

export interface OrderedWorkspace extends FavoriteWorkspace {
  isFavorite: boolean;
  [key: string]: unknown;
}

/**
 * 按收藏状态排序工作空间：收藏的排前面（保持收藏顺序），其余保持原顺序。
 * 返回带 isFavorite 标记的新数组，不修改入参。
 */
export function orderWorkspacesByFavorites(
  workspaces?: FavoriteWorkspace[] | null,
  favorites: FavoriteWorkspace[] = [],
): OrderedWorkspace[] {
  const favKeys = new Set(favorites.map((f) => f.workspace_key));
  const favOrder = new Map(favorites.map((f, i) => [f.workspace_key, i]));

  return [...(workspaces || [])]
    .sort((a, b) => {
      const aFav = favKeys.has(a.workspace_key);
      const bFav = favKeys.has(b.workspace_key);
      if (aFav && bFav) {
        return (favOrder.get(a.workspace_key) ?? 0) - (favOrder.get(b.workspace_key) ?? 0);
      }
      if (aFav) return -1;
      if (bFav) return 1;
      return 0;
    })
    .map((ws) => ({
      ...ws,
      isFavorite: favKeys.has(ws.workspace_key),
    }));
}
