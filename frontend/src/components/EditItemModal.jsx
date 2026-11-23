import React, { useEffect, useState } from 'react';
import { Alert, DatePicker, Form, Input, InputNumber, Modal, Select } from 'antd';
import dayjs from 'dayjs';
import { useWorkspaces } from '../hooks/useWorkspaces';
import RequirementSelect from './RequirementSelect';
import SprintSelect from './SprintSelect';
import { buildWorkspaceOptions } from '../utils/workspaceOptions';

export default function EditItemModal({ open, item, cookie, favorites, onClose, onSubmit }) {
  const [form] = Form.useForm();
  const workspaces = useWorkspaces(cookie, open);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const workspaceName = Form.useWatch('workspace_name', form);

  useEffect(() => {
    if (!open || !item) return;
    form.setFieldsValue({
      name: item.name || '',
      workspace_name: item.workspace_name || undefined,
      sprintId: item.sprint_id,
      requirementId: item.requirement_id || undefined,
      time: item.time != null ? Number(item.time) : undefined,
      date: item.date ? dayjs(item.date) : null
    });
    setError('');
  }, [open, item, form]);

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
        requirementId: values.requirementId || '',
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
            showSearch
            optionFilterProp="label"
            placeholder="请选择工作空间"
            options={buildWorkspaceOptions(workspaces, favorites)}
            onChange={handleWorkspaceChange}
          />
        </Form.Item>
        <Form.Item label="迭代" name="sprintId">
          <SprintSelect
            cookie={cookie}
            workspaceName={workspaceName || item?.workspace_name || ''}
            preferredSprint={item?.sprint_id}
            disabled={!workspaceName}
          />
        </Form.Item>
        <Form.Item
          label="关联需求"
          name="requirementId"
          rules={[{ required: true, message: '请选择关联需求' }]}
        >
          <RequirementSelect
            cookie={cookie}
            placeholder="请选择关联需求"
            initialLabel={
              item?.requirement_name
                ? `${item.requirement_key ? item.requirement_key + '  ' : ''}${item.requirement_name}`
                : undefined
            }
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
