import React, { useEffect, useRef, useState } from 'react';
import { Select, Tag } from 'antd';
import { searchRequirements } from '../api';
import { forgetSearch, loadRecentSearches, rememberSearch } from '../utils/storage';

/**
 * 关联需求下拉：输入关键字后按回车才向服务端搜索（IQL 服务端匹配，不拉全量）。
 * 输入过程不自动请求；回车只触发搜索、不选中高亮项（在捕获阶段拦截，阻止 antd 的选中行为）。
 * 已选中项始终保留在选项里，避免回显丢失。
 * 下拉顶部显示「最近搜索」历史（按用户持久化，最多 3 条），点击即填入并搜索。
 */
export default function RequirementSelect({ cookie, username, value, onChange, disabled, initialLabel, placeholder = '请选择关联需求' }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState(() => loadRecentSearches(username));
  const [searchValue, setSearchValue] = useState('');
  const keyword = useRef('');
  const latest = useRef(0);
  const timer = useRef(null);
  const wrapRef = useRef(null);
  const loadRef = useRef(null);

  const load = (text) => {
    if (!cookie) return;
    const seq = ++latest.current;
    setLoading(true);
    searchRequirements(cookie, text)
      .then((res) => {
        if (seq !== latest.current) return;
        const rows = Array.isArray(res?.data) ? res.data : [];
        setOptions(
          rows.map((r) => ({
            value: r.id,
            label: r.key ? `${r.key}  ${r.name}` : r.name,
            name: r.name || ''
          }))
        );
      })
      .catch(() => {
        if (seq === latest.current) setOptions([]);
      })
      .finally(() => {
        if (seq === latest.current) setLoading(false);
      });
  };
  loadRef.current = load;

  // 用户名变化时重新读取该用户的最近搜索
  useEffect(() => {
    setRecent(loadRecentSearches(username));
  }, [username]);

  // 初次加载最新需求，提供默认可选项（仅一次）
  useEffect(() => {
    load('');
    return () => {
      latest.current += 1;
      if (timer.current) clearTimeout(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cookie]);

  // 回车立即搜索：清掉未触发的防抖，阻止 antd 把回车当作「选中高亮项」
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const onKeyDownCapture = (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      e.stopPropagation();
      if (timer.current) clearTimeout(timer.current);
      const text = keyword.current.trim();
      if (text) setRecent(rememberSearch(username, text));
      loadRef.current?.(text);
    };
    el.addEventListener('keydown', onKeyDownCapture, true);
    return () => el.removeEventListener('keydown', onKeyDownCapture, true);
  }, [username]);

  const merged = options.slice();
  if (value && !merged.some((o) => o.value === value)) {
    merged.unshift({ value, label: initialLabel || value, name: initialLabel || value });
  }

  // 点击历史 chip：填入搜索框 + 立即搜索，下拉保持展开
  const applyHistory = (text) => {
    keyword.current = text;
    setSearchValue(text);
    if (timer.current) clearTimeout(timer.current);
    setRecent(rememberSearch(username, text)); // 置顶
    loadRef.current?.(text);
  };

  const dropdownRender = (menu) => (
    <div>
      {recent.length > 0 && (
        <div
          style={{
            padding: '6px 12px',
            borderBottom: '1px solid #f0f0f0',
            whiteSpace: 'nowrap',
            overflow: 'hidden'
          }}
        >
          <span style={{ color: '#999', fontSize: 12, marginRight: 6, verticalAlign: 'middle', whiteSpace: 'nowrap' }}>最近</span>
          {recent.map((text) => (
            <Tag
              key={text}
              closable
              closeIcon={<span style={{ fontSize: 11 }}>×</span>}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => applyHistory(text)}
              onClose={(e) => {
                e?.preventDefault?.();
                setRecent(forgetSearch(username, text));
              }}
              style={{ cursor: 'pointer', verticalAlign: 'middle', marginBottom: 0, marginRight: 10, paddingInlineEnd: 4 }}
              title={text}
            >
              <span style={{ display: 'inline-block', maxWidth: 40, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', verticalAlign: 'middle' }}>
                {text}
              </span>
            </Tag>
          ))}
        </div>
      )}
      {menu}
    </div>
  );

  return (
    <div ref={wrapRef} style={{ width: '100%' }}>
      <Select
        size="large"
        showSearch
        disabled={disabled}
        loading={loading}
        value={value || undefined}
        searchValue={searchValue}
        placeholder={placeholder}
        options={merged}
        filterOption={false}
        onSearch={(input) => {
          keyword.current = input;
          setSearchValue(input);
          if (timer.current) clearTimeout(timer.current);
          timer.current = setTimeout(() => {
            loadRef.current?.(input.trim());
          }, 300);
        }}
        onChange={(id) => {
          const found = merged.find((o) => o.value === id);
          setSearchValue('');
          onChange(id || '', found?.name || '');
        }}
        dropdownRender={dropdownRender}
        style={{ width: '100%' }}
      />
    </div>
  );
}
