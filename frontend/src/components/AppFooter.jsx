import React, { useState } from 'react';
import { Modal } from 'antd';
import {
  BookOutlined,
  CodeOutlined,
  MessageOutlined
} from '@ant-design/icons';
import FeedbackModal from './FeedbackModal';

const REPO_URL = 'https://github.com/isfangmk/add-work';
const APP_VERSION = 'v2.0';

export default function AppFooter({ username }) {
  const [helpOpen, setHelpOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  return (
    <>
      <footer className="app-footer">
        <div className="app-footer-inner">
          <span className="footer-brand">添加工时工具</span>
          <span className="footer-sep" aria-hidden>
            ·
          </span>
          <a
            className="footer-link"
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            <CodeOutlined />
            源码
          </a>
          <span className="footer-sep" aria-hidden>
            ·
          </span>
          <button
            type="button"
            className="footer-link"
            onClick={() => setHelpOpen(true)}
          >
            <BookOutlined />
            使用说明
          </button>
          <span className="footer-sep" aria-hidden>
            ·
          </span>
          <span className="footer-version">{APP_VERSION}</span>
          <span className="footer-sep" aria-hidden>
            ·
          </span>
          <button
            type="button"
            className="footer-link"
            onClick={() => setFeedbackOpen(true)}
          >
            <MessageOutlined />
            问题反馈
          </button>
        </div>
      </footer>

      <Modal
        title="使用说明"
        open={helpOpen}
        onCancel={() => setHelpOpen(false)}
        footer={null}
        destroyOnHidden
      >
        <ol className="help-list">
          <li>浏览器登录 Gitee，复制 PRE-GW-SESSION Cookie 填入上方输入框。</li>
          <li>在「工时情况」日历中点击一项作为源事项（用于克隆字段模板）。</li>
          <li>在事项列表填写名称、迭代、工时、日期；可点「AI帮写」按本周 Git 提交生成草稿。</li>
          <li>点击「开始执行任务」，下方结果区会展示执行日志；完成后可跳转项目空间核对。</li>
          <li>Cookie 会本地缓存，并在服务端保活；失效后请重新粘贴。</li>
        </ol>
      </Modal>

      <FeedbackModal
        open={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        username={username}
      />
    </>
  );
}
