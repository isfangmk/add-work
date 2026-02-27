import React, { useEffect, useState } from 'react';
import { Alert, DatePicker, Form, Input, InputNumber, Modal, Select } from 'antd';
import dayjs from 'dayjs';
import { fetchSprints } from '../api';

export default function EditItemModal({ open, item, cookie, onClose, onSubmit }) {
  const [form] = Form.useForm();
  const [sprints, setSprints] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !item) return;
    form.setFieldsValue({
      name: item.name || '',
      sprintId: item.sprint_id,
      time: item.time != null ? Number(item.time) : undefined,
      date: item.date ? dayjs(item.date) : null
    });
    setError('');
  }, [open, item, form]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!open || !item?.workspace_name || !cookie?.trim()) {
        setSprints([]);
        return;
      }
      try {
        const data = await fetchSprints(cookie, item.workspace_name);
        if (cancelled || !data.success) return;
        const list = [...(data.data || [])].sort((a, b) => {
          if (a.object_id === item.sprint_id) return -1;
          if (b.object_id === item.sprint_id) return 1;
          return 0;
        });
        setSprints(list);
      } catch {
        if (!cancelled) setSprints([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, item, cookie]);

  const handleOk = async () => {
    setError('');
    try {
      const values = await form.validateFields();
      setLoading(true);
      const ok = await onSubmit({
        item,
        name: values.name.trim(),
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
        <Form.Item label="迭代" name="sprintId">
          <Select
            allowClear
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
