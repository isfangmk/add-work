import { useCallback, useEffect, useRef, useState } from 'react';
import { App } from 'antd';
import {
  fetchLlmSummary,
  fetchWorkItems,
  pollTaskStatus,
  startTask
} from '../api';
import { formatDate, getWeekRange, isInCurrentWeek, isWeekend } from '../utils/date';
import {
  classifyLogLine,
  collectFilledDates,
  hasValidDays,
  loadCookie,
  saveCookie
} from '../utils/storage';

const EMPTY_ITEM = { name: '', time: '', date: '', sprint_id: '' };

export function useWorkHoursApp() {
  const { message } = App.useApp();
  const calendarRef = useRef(null);
  const pollRef = useRef(null);

  const [cookie, setCookie] = useState('');
  const [username, setUsername] = useState(null);
  const [gitEmail, setGitEmail] = useState(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [calendarData, setCalendarData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sourceItem, setSourceItem] = useState(null);
  const [autoSelected, setAutoSelected] = useState(false);
  const [workItems, setWorkItems] = useState([{ ...EMPTY_ITEM }]);
  const [editOpen, setEditOpen] = useState(false);
  const [taskLog, setTaskLog] = useState([]);
  const [taskRunning, setTaskRunning] = useState(false);
  const [aiWriting, setAiWriting] = useState(false);

  const filledDates = collectFilledDates(calendarData);
  const weekRange = getWeekRange(weekOffset);

  useEffect(() => {
    const saved = loadCookie();
    if (saved) setCookie(saved);
  }, []);

  useEffect(
    () => () => {
      if (pollRef.current) clearInterval(pollRef.current);
    },
    []
  );

  const onCookieChange = useCallback((value) => {
    setCookie(value);
    saveCookie(value);
  }, []);

  const loadWeek = useCallback(async () => {
    if (!cookie.trim()) return null;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWorkItems({
        cookie,
        startDate: formatDate(weekRange.monday),
        endDate: formatDate(weekRange.sunday),
        username: username || '',
        gitEmail: gitEmail || ''
      });
      if (!data.success) {
        setError(data.msg || '获取工时数据失败');
        setCalendarData({});
        return null;
      }
      setCalendarData(hasValidDays(data.data) ? data.data : {});
      if (data.username) setUsername(data.username);
      if (data.gitEmail) setGitEmail(data.gitEmail);
      return data;
    } catch {
      setError('网络错误');
      setCalendarData({});
      return null;
    } finally {
      setLoading(false);
    }
  }, [cookie, weekRange.monday, weekRange.sunday, username, gitEmail]);

  useEffect(() => {
    if (cookie.trim()) loadWeek();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cookie, weekOffset]);

  useEffect(() => {
    if (!cookie.trim() || sourceItem || autoSelected) return;

    (async () => {
      for (let offset = 0; offset >= -3; offset -= 1) {
        const { monday, sunday } = getWeekRange(offset);
        try {
          const data = await fetchWorkItems({
            cookie,
            startDate: formatDate(monday),
            endDate: formatDate(sunday),
            username: username || '',
            gitEmail: gitEmail || ''
          });
          if (!data.success || !hasValidDays(data.data)) continue;

          const dates = Object.entries(data.data)
            .filter(([, items]) => Array.isArray(items) && items.length > 0)
            .map(([d]) => d)
            .sort();
          if (!dates.length) continue;

          const items = data.data[dates[dates.length - 1]] || [];
          if (!items.length) continue;

          setSourceItem(items[items.length - 1]);
          setAutoSelected(true);
          return;
        } catch {
          break;
        }
      }
      setAutoSelected(true);
    })();
  }, [cookie, username, gitEmail, sourceItem, autoSelected]);

  const beginPoll = useCallback(
    (taskId, onDone) => {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollTaskStatus(taskId);
          setTaskLog((status.log || []).map(classifyLogLine));
          if (!status.running) {
            clearInterval(pollRef.current);
            pollRef.current = null;
            setTaskRunning(false);
            onDone?.();
          }
        } catch (err) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setTaskRunning(false);
          setTaskLog((prev) => [
            ...prev,
            { message: `❌ 获取任务状态失败：${err.message}`, type: 'error' }
          ]);
        }
      }, 1500);
    },
    []
  );

  const refreshAfterTask = useCallback(
    ({ jumpCurrentWeek = false, scrollWeekend = false } = {}) => {
      if (jumpCurrentWeek && weekOffset !== 0) setWeekOffset(0);
      else loadWeek();
      if (scrollWeekend) calendarRef.current?.scrollToRight?.();
    },
    [weekOffset, loadWeek]
  );

  const submitCreate = useCallback(async () => {
    if (!sourceItem) {
      message.warning('请从日历中选择一个源事项！');
      return false;
    }
    const valid = workItems.filter((i) => i.name && i.time && i.date);
    if (!valid.length) {
      message.warning('请至少填写一个完整的事项！');
      return false;
    }

    const defaultSprint = sourceItem.sprint_id || '';
    setTaskRunning(true);
    setTaskLog([{ message: '📅 任务已提交，正在执行...', type: 'info' }]);

    try {
      const data = await startTask({
        username,
        cookie,
        sourceObjectId: sourceItem.object_id,
        workspace_name: sourceItem.workspace_name,
        names: valid.map((i) => i.name),
        times: valid.map((i) => parseFloat(Number(i.time).toFixed(1))),
        dates: valid.map((i) => i.date),
        sprintIds: valid.map((i) => i.sprint_id || defaultSprint)
      });
      if (!data.success) throw new Error(data.msg || '任务启动失败');
      const taskId = data.data?.taskId;
      if (!taskId) throw new Error('未获取到任务ID');

      beginPoll(taskId, () =>
        refreshAfterTask({
          jumpCurrentWeek: valid.some((i) => isInCurrentWeek(i.date)),
          scrollWeekend: valid.some((i) => isWeekend(i.date))
        })
      );
      return true;
    } catch (err) {
      setTaskRunning(false);
      setTaskLog([{ message: `❌ 任务启动失败：${err.message}`, type: 'error' }]);
      return false;
    }
  }, [
    sourceItem,
    workItems,
    username,
    cookie,
    message,
    beginPoll,
    refreshAfterTask
  ]);

  const submitUpdate = useCallback(
    async ({ item, name, sprintId, time, date }) => {
      if (!item || !username || !cookie) return false;
      setTaskRunning(true);
      setTaskLog([{ message: '📅 更新任务已提交，正在执行...', type: 'info' }]);
      try {
        const data = await startTask({
          username,
          cookie,
          workspace_name: item.workspace_name,
          is_update: true,
          sourceObjectId: item.object_id,
          names: [name.trim()],
          sprintIds: [sprintId || item.sprint_id],
          times: [parseFloat(Number(time).toFixed(1))],
          dates: [date]
        });
        if (!data.success) throw new Error(data.msg || '提交失败');
        const taskId = data.data?.taskId;
        if (!taskId) throw new Error('未获取到任务ID');
        beginPoll(taskId, () => refreshAfterTask());
        return true;
      } catch (err) {
        setTaskRunning(false);
        setTaskLog([
          { message: `❌ 更新任务启动失败：${err.message}`, type: 'error' }
        ]);
        return false;
      }
    },
    [username, cookie, beginPoll, refreshAfterTask]
  );

  const aiWrite = useCallback(async () => {
    if (!cookie.trim()) {
      message.warning('请先填写有效的Cookie！');
      return;
    }
    if (!username) {
      message.warning('请先等待日历数据加载完成！');
      return;
    }
    setAiWriting(true);
    try {
      const { monday, sunday } = getWeekRange(weekOffset);
      const data = await fetchLlmSummary({
        gitEmail,
        startDate: formatDate(monday),
        endDate: formatDate(sunday),
        excludeDates: Array.from(filledDates)
      });
      if (!data.success) {
        message.error(data.msg || 'AI生成事项失败');
        return;
      }
      const entries = Object.entries(data.data || {});
      if (!entries.length) {
        message.info(data.msg || '当前日期范围内无生成的事项内容');
        return;
      }
      setWorkItems(entries.map(([date, name]) => ({ ...EMPTY_ITEM, name, date })));
      message.success(`已生成 ${entries.length} 条事项`);
    } catch (err) {
      message.error(`AI生成失败：${err.message}`);
    } finally {
      setAiWriting(false);
    }
  }, [cookie, username, gitEmail, weekOffset, filledDates, message]);

  return {
    calendarRef,
    cookie,
    onCookieChange,
    username,
    weekOffset,
    setWeekOffset,
    weekRange,
    calendarData,
    loading,
    error,
    sourceItem,
    setSourceItem,
    workItems,
    setWorkItems,
    editOpen,
    setEditOpen,
    taskLog,
    taskRunning,
    aiWriting,
    submitCreate,
    submitUpdate,
    aiWrite,
    addItem: () => setWorkItems((prev) => [...prev, { ...EMPTY_ITEM }]),
    removeItem: (index) => {
      setWorkItems((prev) => {
        if (prev.length <= 1) {
          message.warning('至少需要保留一个事项');
          return prev;
        }
        return prev.filter((_, i) => i !== index);
      });
    },
    updateItem: (index, field, value) => {
      setWorkItems((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], [field]: value };
        return next;
      });
    }
  };
}
