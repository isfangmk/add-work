import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
import App from './App';

dayjs.locale('zh-cn');

const path = window.location.pathname.replace(/\/$/, '') || '/';
if (path === '/') {
  window.location.replace('/add-work/');
} else {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#2c3e50',
            colorSuccess: '#27ae60',
            colorError: '#e74c3c',
            borderRadius: 6,
            fontFamily: '"Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif'
          }
        }}
      >
        <AntApp>
          <App />
        </AntApp>
      </ConfigProvider>
    </React.StrictMode>
  );
}
