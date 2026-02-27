import React, { useEffect, useRef } from 'react';
import { Typography } from 'antd';

const TYPE = {
  success: 'success',
  error: 'danger',
  info: undefined,
  default: undefined
};

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
            <span dangerouslySetInnerHTML={{ __html: line.message }} />
          </Typography.Text>
        ))
      )}
    </div>
  );
}
