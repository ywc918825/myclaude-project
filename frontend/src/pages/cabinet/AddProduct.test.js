import { describe, it, expect } from 'vitest';
import { guessNameFromText } from './AddProduct.jsx';

describe('guessNameFromText', () => {
  it('picks the longest substantial line as the name candidate', () => {
    const text = 'COSRX Snail Cream\n蜗牛精华面霜\n100ml Net Wt.';
    expect(guessNameFromText(text)).toBe('COSRX Snail Cream');
  });

  it('ignores lines that are just digits/punctuation', () => {
    const text = '12345\n---\n真正的产品名称在这里';
    expect(guessNameFromText(text)).toBe('真正的产品名称在这里');
  });

  it('returns an empty string when nothing usable was recognized', () => {
    expect(guessNameFromText('123\n...\n%%')).toBe('');
    expect(guessNameFromText('')).toBe('');
  });

  it('handles a single-line result', () => {
    expect(guessNameFromText('温和洁面乳')).toBe('温和洁面乳');
  });
});
