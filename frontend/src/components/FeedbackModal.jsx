import React, { useEffect, useState } from 'react';
import { Form, Input, Modal, message } from 'antd';
import { submitFeedback } from '../api';

export default function FeedbackModal({ open, onClose, username }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      form.setFieldsValue({
        contact: '',
        content: ''
      });
    }
  }, [open, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      const data = await submitFeedback({
        content: values.content.trim(),
        username: (username || '').trim() || undefined,
        contact: (values.contact || '').trim() || undefined
      });
      if (!data.success) {
        message.error(data.msg || '提交失败');
        return;
      }
      message.success(data.msg || '反馈已提交');
      onClose();
    } catch (err) {
      if (!err?.errorFields) {
        message.error(err.message || '提交失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="问题反馈"
      open={open}
      onCancel={onClose}
      onOk={handleOk}
      confirmLoading={loading}
      okText="提交"
      cancelText="取消"
      destroyOnHidden
    >
      <Form form={form} layout="vertical">
        <Form.Item label="联系方式" name="contact">
          <Input placeholder="可选，企业微信 / 邮箱 / 手机号" maxLength={200} />
        </Form.Item>
        <Form.Item
          label="反馈内容"
          name="content"
          rules={[
            { required: true, message: '请填写反馈内容' },
            { min: 5, message: '请至少填写 5 个字' }
          ]}
        >
          <Input.TextArea
            rows={5}
            placeholder="描述遇到的问题、期望的功能或改进建议"
            maxLength={2000}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
