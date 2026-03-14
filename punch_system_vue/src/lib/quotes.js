const STORAGE_KEY_QUOTE_INDEX = 'punch_quote_index'

export const QUOTES = [
  { text: '种一棵树最好的时间是十年前，其次是现在。', from: '非洲谚语' },
  { text: '不积跬步，无以至千里。', from: '荀子' },
  { text: '今天的努力，是明天的底气。', from: '佚名' },
  { text: '微小的习惯，会在时间里长成伟大的力量。', from: '佚名' },
  { text: '不要等待灵感，先开始，灵感就会来。', from: '佚名' },
  { text: '你所热爱的，会带你去到想去的地方。', from: '佚名' },
  { text: '把目标拆小，把行动做实。', from: '佚名' },
  { text: '慢慢来，比较快。', from: '佚名' },
  { text: '自律不是限制，而是选择。', from: '佚名' },
  { text: '坚持的意义，就是把平凡的日子过成光。', from: '佚名' }
]

export function getNextQuote() {
  if (!QUOTES.length) return { text: '', from: '' }
  const raw = localStorage.getItem(STORAGE_KEY_QUOTE_INDEX)
  const prevIndex = Number.isFinite(Number(raw)) ? Number(raw) : -1
  const nextIndex = (prevIndex + 1) % QUOTES.length
  localStorage.setItem(STORAGE_KEY_QUOTE_INDEX, String(nextIndex))
  return QUOTES[nextIndex]
}

