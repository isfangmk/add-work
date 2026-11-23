import React, { useEffect, useRef, useState } from 'react';
import { Checkbox, Select } from 'antd';
import { fetchSprints } from '../api';
import { sortSprintsWithPreferred } from '../utils/workspaceOptions';

/**
 * 迭代下拉：
 * - 默认「只显示当前空间的迭代」勾选，走当前空间过滤
 * - 取消勾选时拉全部空间最近100条，支持输入关键字服务端搜索（防抖）
 * - 勾选框放在下拉浮层顶部（dropdownRender），不展开时不占位
 * - 全量结果缓存：展开时用缓存恢复，避免重复请求，也不残留上次搜索结果
 */
export default function SprintSelect({
  cookie,
  workspaceName,
  value,
  onChange,
  preferredSprint,
  disabled,
  placeholder
}) {
  const [onlyCurrent, setOnlyCurrent] = useState(true);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const keyword = useRef('');
  const timer = useRef(null);
  const latest = useRef(0);
  const fullOptions = useRef([]); // 缓存全量选项，展开时直接恢复，不重复请求

  const load = (kw) => {
    if (!cookie?.trim() || !workspaceName?.trim()) {
      setOptions([]);
      fullOptions.current = [];
      return;
    }
    const seq = ++latest.current;
    setOptions([]); // 先清空，避免上次搜索结果残留到新请求返回
    setLoading(true);
    fetchSprints(cookie, workspaceName, !onlyCurrent, kw)
      .then((res) => {
        if (seq !== latest.current) return;
        let list = Array.isArray(res?.data) ? res.data : [];
        if (onlyCurrent && preferredSprint) list = sortSprintsWithPreferred(list, preferredSprint);
        const opts = list.map((s) => ({ value: s.object_id, label: s.name }));
        if (!kw.trim()) fullOptions.current = opts; // 仅全量结果进缓存
        setOptions(opts);
      })
      .catch(() => {
        if (seq === latest.current) setOptions([]);
      })
      .finally(() => {
        if (seq === latest.current) setLoading(false);
      });
  };

  // 勾选状态 / 工作空间 / cookie 变化时重新加载
  useEffect(() => {
    keyword.current = '';
    setSearchValue('');
    load('');
    return () => {
      latest.current += 1;
      if (timer.current) clearTimeout(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cookie, workspaceName, onlyCurrent]);

  const handleSearch = (input) => {
    setSearchValue(input);
    if (onlyCurrent) return; // 当前空间模式用本地 label 过滤，无需服务端搜索
    if (timer.current) clearTimeout(timer.current);
    if (!input.trim()) {
      // 清空搜索框（含展开时重置）→ 用缓存恢复全量，不再请求
      setOptions(fullOptions.current);
      return;
    }
    keyword.current = input;
    timer.current = setTimeout(() => load(input.trim()), 300);
  };

  // 展开时重置搜索框并用缓存恢复全量，避免重复请求，也不残留上次搜索结果
  const handleOpenChange = (open) => {
    if (!open) return;
    keyword.current = '';
    setSearchValue('');
    if (timer.current) clearTimeout(timer.current);
    setOptions(fullOptions.current);
  };

  // 勾选框放进下拉浮层顶部；阻止 mousedown 默认行为，避免点击时收起下拉
  const dropdownRender = (menu) => (
    <div>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0', whiteSpace: 'nowrap', minWidth: 180 }}>
        <Checkbox
          style={{ whiteSpace: 'nowrap' }}
          checked={onlyCurrent}
          onMouseDown={(e) => e.preventDefault()}
          onChange={(e) => setOnlyCurrent(e.target.checked)}
        >
          只显示当前空间的迭代
        </Checkbox>
      </div>
      {menu}
    </div>
  );

  return (
    <Select
      size="large"
      showSearch
      allowClear
      disabled={disabled || !workspaceName}
      loading={loading}
      value={value || undefined}
      searchValue={searchValue}
      placeholder={placeholder || (workspaceName ? '请选择迭代' : '请先选择工作空间')}
      options={options}
      optionFilterProp="label"
      filterOption={onlyCurrent}
      onSearch={handleSearch}
      onOpenChange={handleOpenChange}
      onChange={(v) => {
        onChange(v || '');
        setSearchValue('');
      }}
      dropdownRender={dropdownRender}
      style={{ width: '100%' }}
    />
  );
}
