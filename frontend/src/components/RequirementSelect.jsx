import React, { useEffect, useRef, useState } from 'react';
import { Select } from 'antd';
import { searchRequirements } from '../api';

/**
 * 关联需求下拉：输入关键字走后端 IQL 服务端搜索（标题模糊/编号精确），不拉全量。
 * 用防抖减少请求；已选中项始终保留在选项里，避免回显丢失。
 */
export default function RequirementSelect({ cookie, value, onChange, disabled, placeholder = '关联需求（可选）' }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const timer = useRef(null);
  const latest = useRef(0);

  const load = (keyword) => {
    if (!cookie) return;
    const seq = ++latest.current;
    setLoading(true);
    searchRequirements(cookie, keyword)
      .then((res) => {
        if (seq !== latest.current) return;
        const payload = res?.data;
        const rows = Array.isArray(payload) ? payload : [];
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

  // 初次加载最新需求（空关键字）
  useEffect(() => {
    load('');
    return () => {
      latest.current += 1;
      if (timer.current) clearTimeout(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cookie]);

  const handleSearch = (input) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => load(input.trim()), 300);
  };

  // 已选中的值若不在当前结果里，补一个选项保证回显
  const merged = options.slice();
  if (value && !merged.some((o) => o.value === value)) {
    merged.unshift({ value, label: value, name: value });
  }

  return (
    <Select
      size="large"
      showSearch
      allowClear
      disabled={disabled}
      loading={loading}
      value={value || undefined}
      placeholder={placeholder}
      options={merged}
      filterOption={false}
      onSearch={handleSearch}
      onChange={(id) => {
        const found = merged.find((o) => o.value === id);
        onChange(id || '', found?.name || '');
      }}
      style={{ width: '100%' }}
    />
  );
}
