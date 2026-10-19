import React, { useEffect, useState } from 'react';
import { Alert, DatePicker, Form, Input, InputNumber, Modal, Select } from 'antd';
import dayjs from 'dayjs';
import { fetchSprints, fetchWorkspaces } from '../api';

export default function EditItemModal({ open, item, cookie, onClose, onSubmit }) {
  const [form] = Form.useForm();
  const [workspaces, setWorkspaces] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const workspaceName = Form.useWatch('workspace_name', form);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchWorkspaces();
        if (cancelled || !data.success) return;
        setWorkspaces(data.data || []);
      } catch {
        if (!cancelled) setWorkspaces([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!open || !item) return;
    form.setFieldsValue({
      name: item.name || '',
      workspace_name: item.workspace_name || undefined,
      sprintId: item.sprint_id,
      time: item.time != null ? Number(item.time) : undefined,
      date: item.date ? dayjs(item.date) : null
    });
    setError('');
  }, [open, item, form]);

  useEffect(() => {
    let cancelled = false;
    const workspace = (workspaceName || item?.workspace_name || '').trim();
    const preferredSprint = item?.sprint_id;
    (async () => {
      if (!open || !workspace || !cookie?.trim()) {
        setSprints([]);
        return;
      }
      try {
        const data = await fetchSprints(cookie, workspace);
        if (cancelled || !data.success) return;
        const list = [...(data.data || [])];
        if (workspace === item?.workspace_name && preferredSprint) {
          list.sort((a, b) => {
            if (a.object_id === preferredSprint) return -1;
            if (b.object_id === preferredSprint) return 1;
            return 0;
          });
        }
        setSprints(list);
        const ids = new Set(list.map((s) => s.object_id));
        const current = form.getFieldValue('sprintId');
        if (current && !ids.has(current)) {
          form.setFieldValue('sprintId', undefined);
        }
      } catch {
        if (!cancelled) setSprints([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, workspaceName, item?.workspace_name, item?.sprint_id, cookie, form, item]);

  const handleWorkspaceChange = (value) => {
    form.setFieldsValue({
      workspace_name: value,
      sprintId: undefined
    });
  };

  const handleOk = async () => {
    setError('');
    try {
      const values = await form.validateFields();
      setLoading(true);
      const ok = await onSubmit({
        item,
        name: values.name.trim(),
        workspaceName: values.workspace_name || item.workspace_name,
        sprintId: values.sprintId || item.sprint_id,
        time: values.time,
        date: values.date.format('YYYY-MM-DD')
      });
      if (ok) onClose();
      else setError('任务启动失败，请查看下方执行结果');
    } catch (err) {
      if (!err?.errorFields) setError(err.message || '提交失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="更新事项"
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      confirmLoading={loading}
      okText="提交修改"
      cancelText="取消"
      destroyOnHidden
    >
      <Form form={form} layout="vertical">
        <Form.Item
          label="事项名称"
          name="name"
          rules={[{ required: true, message: '请填写事项名称' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          label="工作空间"
          name="workspace_name"
          rules={[{ required: true, message: '请选择工作空间' }]}
        >
          <Select
            placeholder="请选择工作空间"
            options={workspaces.map((ws) => ({
              value: ws.workspace_name,
              label: ws.workspace_name
            }))}
            onChange={handleWorkspaceChange}
          />
        </Form.Item>
        <Form.Item label="迭代" name="sprintId">
          <Select
            allowClear
            placeholder={workspaceName ? '请选择迭代' : '请先选择工作空间'}
            disabled={!workspaceName}
            options={sprints.map((s) => ({ value: s.object_id, label: s.name }))}
          />
        </Form.Item>
        <Form.Item
          label="工时（小时）"
          name="time"
          rules={[{ required: true, message: '请填写工时' }]}
        >
          <InputNumber style={{ width: '100%' }} min={0.1} step={0.1} precision={1} />
        </Form.Item>
        <Form.Item
          label="日期"
          name="date"
          rules={[{ required: true, message: '请选择日期' }]}
        >
          <DatePicker style={{ width: '100%' }} allowClear={false} />
        </Form.Item>
      </Form>
      {error && <Alert type="error" showIcon message={error} />}
    </Modal>
  );
}
