import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  DatePicker,
  Input,
  InputNumber,
  Select,
  Space,
  Typography,
  message
} from 'antd';
import { MinusOutlined, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { fetchSprints, fetchWorkspaces } from '../api';

export default function WorkItemForm({
  workItems,
  sourceItem,
  cookie,
  username,
  taskRunning,
  aiWriting,
  onAdd,
  onRemove,
  onChange,
  onAiWrite,
  onSubmit
}) {
  const [workspaces, setWorkspaces] = useState([]);
  const [sprintsByWs, setSprintsByWs] = useState({});

  const defaultWorkspace = sourceItem?.workspace_name || '';
  const preferredSprint = sourceItem?.sprint_id || '';

  const usedWorkspaces = useMemo(() => {
    const names = new Set();
    workItems.forEach((item) => {
      const name = item.workspace_name || defaultWorkspace;
      if (name) names.add(name);
    });
    if (defaultWorkspace) names.add(defaultWorkspace);
    return Array.from(names);
  }, [workItems, defaultWorkspace]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchWorkspaces();
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
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (!cookie?.trim() || !usedWorkspaces.length) {
      setSprintsByWs({});
      return undefined;
    }
    (async () => {
      const next = {};
      await Promise.all(
        usedWorkspaces.map(async (workspace) => {
          try {
            const data = await fetchSprints(cookie, workspace);
            if (!data.success) {
              next[workspace] = [];
              return;
            }
            const list = [...(data.data || [])].sort((a, b) => {
              if (a.object_id === preferredSprint) return -1;
              if (b.object_id === preferredSprint) return 1;
              return 0;
            });
            next[workspace] = list;
          } catch (err) {
            console.error(err);
            next[workspace] = [];
          }
        })
      );
      if (!cancelled) setSprintsByWs(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [usedWorkspaces, preferredSprint, cookie]);

  const handleWorkspaceChange = (index, workspace) => {
    onChange(index, {
      workspace_name: workspace || '',
      sprint_id: ''
    });
  };

  const handleSubmit = () => {
    const invalid = workItems.some((item) => {
      const t = Number(item.time);
      return !item.time || !Number.isFinite(t) || t <= 0;
    });
    if (invalid) {
      message.warning('工时必须输入大于 0 的有效数字');
      return;
    }
    onSubmit();
  };

  const workspaceOptions = workspaces.map((ws) => ({
    value: ws.workspace_name,
    label: ws.workspace_name
  }));

  return (
    <div className="work-item-form">
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {workItems.map((item, index) => {
          const workspace = item.workspace_name || defaultWorkspace || undefined;
          const sprints = (workspace && sprintsByWs[workspace]) || [];
          return (
            <div key={index} className="work-item-row">
              <Input
                size="large"
                className="work-item-name"
                placeholder="事项名称"
                value={item.name}
                onChange={(e) => onChange(index, 'name', e.target.value)}
              />
              <Select
                size="large"
                className="work-item-workspace"
                placeholder="工作空间"
                value={workspace}
                options={workspaceOptions}
                onChange={(v) => handleWorkspaceChange(index, v)}
              />
              <Select
                size="large"
                className="work-item-sprint"
                placeholder="请选择迭代"
                allowClear
                value={item.sprint_id || (workspace === defaultWorkspace ? preferredSprint : undefined) || undefined}
                options={sprints.map((s) => ({ value: s.object_id, label: s.name }))}
                onChange={(v) => onChange(index, 'sprint_id', v || '')}
              />
              <InputNumber
                size="large"
                className="work-item-time"
                min={0.1}
                step={0.1}
                precision={1}
                placeholder="工时"
                value={item.time === '' || item.time == null ? null : Number(item.time)}
                onChange={(v) => onChange(index, 'time', v == null ? '' : v)}
              />
              <DatePicker
                size="large"
                className="work-item-date"
                value={item.date ? dayjs(item.date) : null}
                onChange={(_, str) => onChange(index, 'date', str || '')}
                allowClear={false}
                placeholder="请选择日期"
              />
              <Button
                danger
                type="primary"
                size="large"
                className="work-item-remove"
                icon={<MinusOutlined />}
                onClick={() => onRemove(index)}
              />
            </div>
          );
        })}
      </Space>

      <div className="action-btn-row">
        <Button
          type="primary"
          className="btn-success"
          icon={<PlusOutlined />}
          onClick={onAdd}
        >
          添加事项
        </Button>
        <Button
          type="primary"
          className="btn-success"
          loading={aiWriting}
          disabled={!cookie?.trim() || !username}
          onClick={onAiWrite}
        >
          AI帮写
        </Button>
      </div>

      <Typography.Paragraph type="secondary" className="work-item-hint">
        每个事项包含名称、工作空间、迭代、工时和日期；基于Git提交AI帮写将自动填充当前周未填写的事项内容
      </Typography.Paragraph>

      <div className="form-action-bar">
        <Button
          type="primary"
          size="large"
          className="start-task-btn"
          loading={taskRunning}
          disabled={!sourceItem || taskRunning}
          onClick={handleSubmit}
        >
          {taskRunning
            ? '任务执行中...'
            : sourceItem
              ? '开始执行任务'
              : '请先选择源事项'}
        </Button>
      </div>
    </div>
  );
}
