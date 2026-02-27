import React, { useEffect, useState } from 'react';
import { Button, Input, Tag, Typography } from 'antd';
import {
  CheckCircleFilled,
  DownOutlined,
  KeyOutlined,
  UpOutlined,
  WarningFilled
} from '@ant-design/icons';

export default function CookiePanel({ cookie, onChange, username }) {
  const filled = Boolean(cookie?.trim());
  const [expanded, setExpanded] = useState(!filled);

  useEffect(() => {
    if (!filled) setExpanded(true);
  }, [filled]);

  return (
    <div className="cookie-panel">
      <div className="cookie-panel-bar">
        <div className="cookie-panel-status">
          <KeyOutlined className="cookie-panel-icon" />
          {filled ? (
            <Tag icon={<CheckCircleFilled />} color="success">
              Cookie 已填写
            </Tag>
          ) : (
            <Tag icon={<WarningFilled />} color="warning">
              Cookie 未填写
            </Tag>
          )}
          {username ? (
            <Typography.Text type="secondary" className="cookie-panel-user">
              当前用户：{username}
            </Typography.Text>
          ) : null}
        </div>
        <Button
          type="link"
          size="small"
          className="cookie-panel-toggle"
          icon={expanded ? <UpOutlined /> : <DownOutlined />}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? '收起' : '展开编辑'}
        </Button>
      </div>

      {expanded ? (
        <div className="cookie-panel-editor">
          <Input.TextArea
            rows={3}
            value={cookie}
            onChange={(e) => onChange(e.target.value)}
            placeholder="请粘贴 Gitee 的 PRE-GW-SESSION Cookie 值"
          />
          <Typography.Paragraph type="secondary" className="cookie-panel-hint">
            获取方式：浏览器登录 https://gitee.ibr.net.cn → F12 → 存储 → Cookie → 找到
            PRE-GW-SESSION → 复制值
          </Typography.Paragraph>
        </div>
      ) : null}
    </div>
  );
}
