import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import {
  Alert,
  Button,
  Card,
  Empty,
  Spin,
  Tag,
  Typography
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { formatDate } from '../utils/date';

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

const WeekCalendar = forwardRef(function WeekCalendar(
  {
    calendarData,
    monday,
    sourceItem,
    onSelect,
    onEdit,
    loading,
    error
  },
  ref
) {
  const scroller = useRef(null);

  useImperativeHandle(ref, () => ({
    scrollToRight() {
      const el = scroller.current;
      if (!el) return;
      el.scrollLeft = el.scrollWidth - el.clientWidth;
    }
  }));

  useEffect(() => {
    if (scroller.current) scroller.current.scrollLeft = 0;
  }, []);

  return (
    <div className="week-calendar-body">
      {loading && (
        <div style={{ marginBottom: 12 }}>
          <Spin size="small" /> 加载工时数据...
        </div>
      )}
      {error && (
        <Alert type="error" showIcon message={error} style={{ marginBottom: 12 }} />
      )}

      <div className="week-scroll" ref={scroller}>
        {WEEKDAYS.map((label, i) => {
          const day = new Date(monday);
          day.setDate(monday.getDate() + i);
          const dateStr = formatDate(day);
          const items = calendarData[dateStr] || [];
          let hours = items.reduce((s, it) => s + (parseFloat(it.time) || 0), 0);
          hours = Number.isInteger(hours) ? hours : Number(hours.toFixed(1));

          return (
            <Card
              key={dateStr}
              className="day-card"
              size="small"
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <Typography.Text ellipsis style={{ fontSize: 13 }}>
                    {label} {dateStr}
                  </Typography.Text>
                  <Tag color="blue">{hours}小时</Tag>
                </div>
              }
            >
              <div className="day-items">
                {items.length ? (
                  items.map((item) => (
                    <div
                      key={item.object_id}
                      className={`work-item${
                        sourceItem?.object_id === item.object_id ? ' selected' : ''
                      }`}
                      onClick={() => onSelect(item)}
                    >
                      <div style={{ display: 'flex', gap: 4 }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div>
                            <Typography.Text type="danger" strong>
                              {item.time}h
                            </Typography.Text>{' '}
                            {item.name}
                          </div>
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            迭代: {item.sprint}
                          </Typography.Text>
                        </div>
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            onEdit(item);
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无工时记录" />
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
});

export default WeekCalendar;
