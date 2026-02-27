import React from 'react';
import { FieldTimeOutlined } from '@ant-design/icons';

const APP_VERSION = 'v2.0';

export default function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header-main">
        <div className="app-header-icon" aria-hidden>
          <FieldTimeOutlined />
        </div>
        <div className="app-header-text">
          <div className="app-header-title-row">
            <h1 className="app-header-title">添加工时工具</h1>
            <span className="app-header-version">{APP_VERSION}</span>
          </div>
          <p className="app-header-desc">批量填报工时，支持 AI 帮写</p>
        </div>
      </div>
    </header>
  );
}
