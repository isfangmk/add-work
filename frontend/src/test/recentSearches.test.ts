import { describe, it, expect, beforeEach } from 'vitest'
import { rememberSearch, loadRecentSearches, forgetSearch } from '@/lib/recentSearches'

describe('recentSearches', () => {
  beforeEach(() => localStorage.clear())

  it('记录搜索并按用户隔离存储', () => {
    rememberSearch('alice', 'Alpha')
    rememberSearch('bob', 'Beta')
    expect(loadRecentSearches('alice')).toEqual(['Alpha'])
    expect(loadRecentSearches('bob')).toEqual(['Beta'])
    expect(loadRecentSearches('carol')).toEqual([])
  })

  it('去重、最近优先、最多3条', () => {
    rememberSearch('tester', 'a')
    rememberSearch('tester', 'b')
    rememberSearch('tester', 'c')
    rememberSearch('tester', 'a')
    expect(loadRecentSearches('tester')).toEqual(['a', 'c', 'b'])
    // 第 4 个不同关键字应淘汰最旧的
    rememberSearch('tester', 'd')
    expect(loadRecentSearches('tester')).toEqual(['d', 'a', 'c'])
  })

  it('空关键字不改变历史', () => {
    rememberSearch('tester', 'a')
    expect(rememberSearch('tester', '   ')).toEqual(['a'])
    expect(loadRecentSearches('tester')).toEqual(['a'])
  })

  it('删除指定历史项', () => {
    rememberSearch('tester', 'a')
    rememberSearch('tester', 'b')
    expect(forgetSearch('tester', 'a')).toEqual(['b'])
    expect(loadRecentSearches('tester')).toEqual(['b'])
  })

  it('存储内容损坏时返回空数组', () => {
    localStorage.setItem('add-work:recent-requirement-search:tester', '{bad json')
    expect(loadRecentSearches('tester')).toEqual([])
  })
})
