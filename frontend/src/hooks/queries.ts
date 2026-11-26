import { useQuery } from '@tanstack/react-query'
import {
  fetchCurrentUser,
  fetchFavoriteWorkspaces,
  fetchSprints,
  fetchWorkItems,
  fetchWorkspaces,
  searchRequirements,
} from '@/lib/api'

export function useCurrentUser(cookie: string) {
  return useQuery({
    queryKey: ['currentUser', cookie],
    queryFn: () => fetchCurrentUser(cookie).then((r) => r.data),
    enabled: !!cookie.trim(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useWorkspaces(cookie: string, enabled = true) {
  return useQuery({
    queryKey: ['workspaces', cookie],
    queryFn: () => fetchWorkspaces(cookie).then((r) => (r.data ?? [])),
    enabled: enabled && !!cookie.trim(),
    staleTime: 10 * 60 * 1000,
  })
}

export function useSprints(cookie: string, workspaceName: string, allWorkspaces: boolean, keyword: string, enabled = true) {
  return useQuery({
    queryKey: ['sprints', cookie, workspaceName, allWorkspaces, keyword],
    queryFn: () => fetchSprints(cookie, workspaceName, allWorkspaces, keyword).then((r) => (r.data ?? [])),
    enabled: enabled && !!cookie.trim() && (!allWorkspaces || !!workspaceName.trim()),
    staleTime: 5 * 60 * 1000,
  })
}

export function useRequirements(cookie: string, keyword: string, enabled = true) {
  return useQuery({
    queryKey: ['requirements', cookie, keyword],
    queryFn: () => searchRequirements(cookie, keyword).then((r) => (r.data ?? [])),
    enabled: enabled && !!cookie.trim(),
    staleTime: 30 * 1000,
  })
}

export function useWorkItems(payload: {
  cookie: string
  start_date: string
  end_date: string
  username: string
  git_email: string
}) {
  return useQuery({
    queryKey: ['workItems', payload],
    queryFn: () => fetchWorkItems(payload).then((r) => (r.data ?? {})),
    enabled: !!payload.cookie.trim() && !!payload.username,
    staleTime: 30 * 1000,
  })
}

export function useFavorites(username: string | null) {
  return useQuery({
    queryKey: ['favorites', username],
    queryFn: () => fetchFavoriteWorkspaces(username!.trim()).then((r) => (r.data ?? [])),
    enabled: !!username?.trim(),
  })
}
