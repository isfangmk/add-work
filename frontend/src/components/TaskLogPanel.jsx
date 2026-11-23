import React, { useEffect, useRef } from 'react';
import { Typography } from 'antd';

const TYPE = {
  success: 'success',
  error: 'danger',
  info: undefined,
  default: undefined
};

// 仅把 http(s) URL 渲染成安全链接；其余文本由 React 自动转义
function renderMessage(message) {
  const parts = String(message).split(/(https?:\/\/[^\s]+)/g);
  return parts.map((part, i) =>
    /^https?:\/\//.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer">
        {part}
      </a>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

export default function TaskLogPanel({ taskLog }) {
  const ref = useRef(null);
  const empty = !taskLog.length;

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [taskLog]);

  return (
    <div
      ref={ref}
      className={`task-log${empty ? ' task-log-empty' : ''}`}
    >
      {empty ? (
        <Typography.Text type="secondary">
          选择源事项并填写表单后，点击「开始执行任务」，结果将显示在此处
        </Typography.Text>
      ) : (
        taskLog.map((line, i) => (
          <Typography.Text
            key={i}
            type={TYPE[line.type]}
            style={{ display: 'block', marginBottom: 4, whiteSpace: 'pre-wrap' }}
          >
            {renderMessage(line.message)}
          </Typography.Text>
        ))
      )}
    </div>
  );
}
