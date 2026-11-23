import React, { useEffect, useRef, useState } from 'react';
import { Select } from 'antd';
import { searchRequirements } from '../api';

/**
 * 关联需求下拉：输入关键字后按回车才向服务端搜索（IQL 服务端匹配，不拉全量）。
 * 输入过程不自动请求；回车只触发搜索、不选中高亮项（在捕获阶段拦截，阻止 antd 的选中行为）。
 * 已选中项始终保留在选项里，避免回显丢失。
 */
export default function RequirementSelect({ cookie, value, onChange, disabled, initialLabel, placeholder = '请选择关联需求' }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
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
      loadRef.current?.(keyword.current.trim());
    };
    el.addEventListener('keydown', onKeyDownCapture, true);
    return () => el.removeEventListener('keydown', onKeyDownCapture, true);
  }, []);

  const merged = options.slice();
  if (value && !merged.some((o) => o.value === value)) {
    merged.unshift({ value, label: initialLabel || value, name: initialLabel || value });
  }

  return (
    <div ref={wrapRef} style={{ width: '100%' }}>
      <Select
        size="large"
        showSearch
        disabled={disabled}
        loading={loading}
        value={value || undefined}
        placeholder={placeholder}
        options={merged}
        filterOption={false}
        onSearch={(input) => {
          keyword.current = input;
          if (timer.current) clearTimeout(timer.current);
          timer.current = setTimeout(() => loadRef.current?.(input.trim()), 300);
        }}
        onChange={(id) => {
          const found = merged.find((o) => o.value === id);
          onChange(id || '', found?.name || '');
        }}
        style={{ width: '100%' }}
      />
    </div>
  );
}
