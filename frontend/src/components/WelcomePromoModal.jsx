import React, { useState } from 'react';
import { Button, Modal, message } from 'antd';
import {
  CheckCircleOutlined,
  CopyOutlined,
  ShareAltOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { hideWelcomePromo, shouldShowWelcomePromo } from '../utils/storage';

const SHARE_URL = 'https://github.com/isfangmk/add-work';
const APP_SHARE_LINK = 'http://192.168.4.232:3000/add-work';
const SHARE_TEXT =
  '推荐一个添加工时工具：周历选源事项一键克隆，还支持 AI 帮写，省去重复填报。';

const HIGHLIGHTS = [
  { icon: <ThunderboltOutlined />, text: '一次填写一周的工时' },
  { icon: <CheckCircleOutlined />, text: 'AI 帮写按 Git 提交生成工时草稿' },
  { icon: <ShareAltOutlined />, text: '转发给同事，一起少花时间在填报上' }
];

export default function WelcomePromoModal() {
  const [open, setOpen] = useState(() => shouldShowWelcomePromo());

  const close = () => setOpen(false);

  const handleConfirm = () => close();

  const handleDontShow = () => {
    hideWelcomePromo();
    close();
  };

  const handleCopy = async () => {
    const payload = `${SHARE_TEXT}\n${APP_SHARE_LINK}\n源码：${SHARE_URL}`;
    try {
      await navigator.clipboard.writeText(payload);
      message.success('分享文案已复制，可直接发给同事');
    } catch {
      message.error('复制失败，请手动分享页面链接');
    }
  };

  return (
    <Modal
      open={open}
      onCancel={handleConfirm}
      footer={null}
      centered
      width={440}
      destroyOnHidden
      className="welcome-promo-modal"
      title={null}
      closable
    >
      <div className="welcome-promo">
        <div className="welcome-promo-hero">
          <div className="welcome-promo-badge">欢迎使用</div>
          <h2 className="welcome-promo-title">添加工时工具</h2>
          <p className="welcome-promo-lead">
            写给需要经常填报工时的同学。用得顺手的话，欢迎转给同事一起用。
          </p>
        </div>

        <ul className="welcome-promo-list">
          {HIGHLIGHTS.map((item) => (
            <li key={item.text}>
              <span className="welcome-promo-list-icon">{item.icon}</span>
              <span>{item.text}</span>
            </li>
          ))}
        </ul>

        <div className="welcome-promo-actions">
          <Button icon={<CopyOutlined />} onClick={handleCopy} block>
            复制分享文案
          </Button>
          <div className="welcome-promo-footer">
            <Button type="text" onClick={handleDontShow}>
              不再显示
            </Button>
            <Button type="primary" className="welcome-promo-ok" onClick={handleConfirm}>
              确定
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
