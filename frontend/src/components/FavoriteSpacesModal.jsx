import React, { useEffect, useMemo, useState } from 'react';
import { Button, Checkbox, Empty, Input, List, Modal, Space, Typography } from 'antd';
import { StarFilled } from '@ant-design/icons';
import { fetchWorkspaces } from '../api';

const { Text, Paragraph } = Typography;

export default function FavoriteSpacesModal({
  open,
  username,
  cookie,
  favorites,
  onClose,
  onSave,
}) {
  const [allWorkspaces, setAllWorkspaces] = useState([]);
  const [selected, setSelected] = useState([]); // [{workspace_key, workspace_name}]
  const [favSearch, setFavSearch] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [allSearch, setAllSearch] = useState('');
  const [saving, setSaving] = useState(false);

  // 打开时用当前收藏初始化选中态
  useEffect(() => {
    if (!open) return;
    setSelected((favorites || []).map((w) => ({ ...w })));
    setFavSearch('');
    setAllSearch('');
    setAddOpen(false);
  }, [open, favorites]);

  // 加载全部空间（下拉用同一份全量数据）
  useEffect(() => {
    if (!open || !cookie?.trim()) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchWorkspaces(cookie);
        if (cancelled || !data.success) return;
        setAllWorkspaces(data.data || []);
      } catch {
        if (!cancelled) setAllWorkspaces([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, cookie]);

  const selectedKeys = useMemo(
    () => new Set(selected.map((w) => w.workspace_key)),
    [selected]
  );

  const shownFavorites = selected.filter(
    (w) =>
      (w.workspace_name || '').toLowerCase().includes(favSearch.trim().toLowerCase()) ||
      (w.workspace_key || '').includes(favSearch.trim())
  );

  const shownAll = allWorkspaces.filter(
    (w) =>
      (w.workspace_name || '').toLowerCase().includes(allSearch.trim().toLowerCase()) ||
      (w.workspace_key || '').includes(allSearch.trim())
  );

  const toggle = (ws) => {
    setSelected((prev) => {
      const exists = prev.some((f) => f.workspace_key === ws.workspace_key);
      if (exists) return prev.filter((f) => f.workspace_key !== ws.workspace_key);
      return [...prev, { workspace_key: ws.workspace_key, workspace_name: ws.workspace_name }];
    });
  };

  const removeOne = (key) => {
    setSelected((prev) => prev.filter((f) => f.workspace_key !== key));
  };

  const handleOk = async () => {
    setSaving(true);
    try {
      await onSave(selected);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      title={
        <div>
          <div>关注空间</div>
          <Paragraph type="secondary" style={{ margin: '2px 0 0', fontSize: 12, fontWeight: 400 }}>
            只从关注的空间读取工时，避免加载无关空间
          </Paragraph>
        </div>
      }
      onCancel={onClose}
      onOk={handleOk}
      okText="确定"
      cancelText="取消"
      confirmLoading={saving}
      destroyOnHidden
      width={620}
    >
      <div
        style={{
          padding: '10px 12px',
          marginBottom: 16,
          borderRadius: 8,
          background: '#fff8e6',
          border: '1px solid #ffe7a8',
          fontSize: 12,
          lineHeight: 1.6,
          color: '#8a6d1f',
        }}
      >
        💡 关注的空间会出现在日历拉取范围内。工作空间下拉列表仍显示全部空间，不影响填报时换空间。
      </div>

      <div style={{ fontWeight: 600, marginBottom: 10 }}>
        已关注 <span style={{ color: '#1e8449' }}>({selected.length})</span>
      </div>
      <Input
        allowClear
        placeholder="搜索已关注的空间…"
        value={favSearch}
        onChange={(e) => setFavSearch(e.target.value)}
        style={{ marginBottom: 12 }}
      />
      {shownFavorites.length ? (
        <List
          size="small"
          dataSource={shownFavorites}
          renderItem={(ws) => (
            <List.Item
              actions={[
                <Button type="link" danger size="small" onClick={() => removeOne(ws.workspace_key)}>
                  移除
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={<StarFilled style={{ color: '#f5a623', fontSize: 16 }} />}
                title={ws.workspace_name}
                description={<Text type="secondary">{ws.workspace_key}</Text>}
              />
            </List.Item>
          )}
          style={{ marginBottom: 8, maxHeight: 220, overflowY: 'auto' }}
        />
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={selected.length ? '没有匹配的空间' : '还没有关注任何空间，点下方添加'}
          style={{ margin: '12px 0' }}
        />
      )}

      <Button
        block
        onClick={() => setAddOpen((v) => !v)}
        style={{ borderColor: '#27ae60', color: '#1e8449' }}
      >
        {addOpen ? '－ 收起添加面板' : '＋ 添加空间'}
      </Button>

      {addOpen && (
        <div style={{ marginTop: 16, borderTop: '1px dashed #e5e5e5', paddingTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontWeight: 600 }}>
              全部空间 <span style={{ color: '#1e8449' }}>({allWorkspaces.length})</span>
            </span>
            <Text type="secondary" style={{ fontSize: 12 }}>勾选后点确定</Text>
          </div>
          <Input
            allowClear
            placeholder="搜索全部空间名称或编号…"
            value={allSearch}
            onChange={(e) => setAllSearch(e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <div style={{ maxHeight: 260, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: 8 }}>
            {shownAll.length ? (
              shownAll.map((ws) => (
                <div
                  key={ws.workspace_key}
                  onClick={() => toggle(ws)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '9px 12px',
                    cursor: 'pointer',
                    background: selectedKeys.has(ws.workspace_key) ? '#f0faf4' : 'transparent',
                    borderTop: '1px solid #f7f7f7',
                  }}
                >
                  <Checkbox checked={selectedKeys.has(ws.workspace_key)} onChange={() => {}} tabIndex={-1} />
                  <span style={{ flex: 1, fontSize: 13 }}>{ws.workspace_name}</span>
                  <Text type="secondary" style={{ fontSize: 11 }}>{ws.workspace_key}</Text>
                </div>
              ))
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的空间" style={{ margin: 16 }} />
            )}
          </div>
        </div>
      )}

      <Space style={{ marginTop: 12 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          username: {username || '-'}
        </Text>
      </Space>
    </Modal>
  );
}
