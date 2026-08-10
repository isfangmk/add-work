import React from 'react';
import { Button, Card, Space } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import { useWorkHoursApp } from './hooks/useWorkHoursApp';
import WeekCalendar from './components/WeekCalendar';
import WorkItemForm from './components/WorkItemForm';
import EditItemModal from './components/EditItemModal';
import TaskLogPanel from './components/TaskLogPanel';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import Section from './components/Section';
import CookiePanel from './components/CookiePanel';
import WelcomePromoModal from './components/WelcomePromoModal';

export default function App() {
  const app = useWorkHoursApp();

  return (
    <div className="app-page">
      <WelcomePromoModal />
      <Card className="app-shell">
        <AppHeader />

        <div className="app-sections">
          <Section
            step={1}
            title="凭证"
            description="粘贴 Gitee PRE-GW-SESSION，用于读取与提交工时"
          >
            <CookiePanel
              cookie={app.cookie}
              onChange={app.onCookieChange}
              username={app.username}
            />
          </Section>

          <Section
            step={2}
            title={`${app.weekRange.weekLabel}工时情况`}
            description="点击一项作为源事项（用于克隆字段模板）"
            extra={
              <Space size={8}>
                <Button
                  type="primary"
                  size="small"
                  className="week-nav-btn"
                  icon={<LeftOutlined />}
                  disabled={app.weekOffset <= -4}
                  onClick={() => app.setWeekOffset((v) => v - 1)}
                />
                <Button
                  type="primary"
                  size="small"
                  className="week-nav-btn"
                  icon={<RightOutlined />}
                  disabled={app.weekOffset >= 0}
                  onClick={() => app.setWeekOffset((v) => v + 1)}
                />
              </Space>
            }
          >
            <WeekCalendar
              ref={app.calendarRef}
              calendarData={app.calendarData}
              monday={app.weekRange.monday}
              sourceItem={app.sourceItem}
              onSelect={app.setSourceItem}
              onEdit={(item) => {
                app.setSourceItem(item);
                app.setEditOpen(true);
              }}
              loading={app.loading}
              error={app.error}
            />
          </Section>

          <Section
            step={3}
            title="填写事项"
            description="填写名称、迭代、工时与日期，可使用 AI 帮写草稿"
          >
            <WorkItemForm
              workItems={app.workItems}
              sourceItem={app.sourceItem}
              cookie={app.cookie}
              username={app.username}
              taskRunning={app.taskRunning}
              aiWriting={app.aiWriting}
              onAdd={app.addItem}
              onRemove={app.removeItem}
              onChange={app.updateItem}
              onAiWrite={app.aiWrite}
              onSubmit={app.submitCreate}
            />
          </Section>

          <Section
            step={4}
            title="执行结果"
            description="任务日志与跳转链接会显示在这里"
          >
            <TaskLogPanel taskLog={app.taskLog} />
          </Section>
        </div>

        <EditItemModal
          open={app.editOpen}
          item={app.sourceItem}
          cookie={app.cookie}
          onClose={() => app.setEditOpen(false)}
          onSubmit={app.submitUpdate}
        />

        <AppFooter username={app.username} />
      </Card>
    </div>
  );
}
