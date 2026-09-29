export function getSavedAnswerTimestamp(item) {
  if (!item) return 0;

  if (item.savedAt && item.savedAt !== '') {
    const parsed = new Date(item.savedAt);
    if (!Number.isNaN(parsed.getTime())) return parsed.getTime();
  }

  if (!item.savedDate || item.savedDate === '') return 0;

  const source = String(item.savedDate).trim();
  const lower = source.toLowerCase();
  const now = new Date();
  const year = now.getFullYear();
  const monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

  const matchTime = source.match(/(\d{1,2}):(\d{2})\s*(am|pm)/i);
  let hours = 0;
  let minutes = 0;

  if (matchTime) {
    hours = Number(matchTime[1]);
    minutes = Number(matchTime[2]);
    const meridiem = matchTime[3].toLowerCase();
    if (meridiem === 'pm' && hours < 12) hours += 12;
    if (meridiem === 'am' && hours === 12) hours = 0;
  }

  if (lower.startsWith('today')) {
    const date = new Date(now);
    date.setHours(hours, minutes, 0, 0);
    return date.getTime();
  }

  if (lower.startsWith('yesterday')) {
    const date = new Date(now);
    date.setDate(date.getDate() - 1);
    date.setHours(hours, minutes, 0, 0);
    return date.getTime();
  }

  const monthMatch = source.match(/(\d{1,2})\s+([A-Za-z]{3,9})(?:,\s*(\d{1,2}):(\d{2})\s*(am|pm))?/i);
  if (monthMatch) {
    const day = Number(monthMatch[1]);
    const monthIndex = monthNames.indexOf(monthMatch[2].slice(0, 3).toLowerCase());
    const date = new Date(year, monthIndex >= 0 ? monthIndex : now.getMonth(), day, hours, minutes, 0, 0);
    return date.getTime();
  }

  const dayMonthMatch = source.match(/([A-Za-z]{3,9})\s+(\d{1,2})(?:,\s*(\d{1,2}):(\d{2})\s*(am|pm))?/i);
  if (dayMonthMatch) {
    const monthIndex = monthNames.indexOf(dayMonthMatch[1].slice(0, 3).toLowerCase());
    const day = Number(dayMonthMatch[2]);
    const date = new Date(year, monthIndex >= 0 ? monthIndex : now.getMonth(), day, hours, minutes, 0, 0);
    return date.getTime();
  }

  return 0;
}

export function sortSavedAnswers(items, order = 'newest') {
  const nextItems = [...items];

  nextItems.sort((a, b) => {
    const timestampA = getSavedAnswerTimestamp(a);
    const timestampB = getSavedAnswerTimestamp(b);
    return timestampB - timestampA;
  });

  if (order === 'oldest') {
    return nextItems.reverse();
  }

  if (order === 'document') {
    return nextItems.sort((a, b) => {
      const nameA = (a.sourceDocument ?? a.question ?? '').toLowerCase();
      const nameB = (b.sourceDocument ?? b.question ?? '').toLowerCase();
      return nameA.localeCompare(nameB);
    });
  }

  return nextItems;
}
