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

  it('rejects lines dominated by OCR noise symbols (real garbled output from a curved-jar photo)', () => {
    const text = '" " = : > 志 : - \\ ve\n张：鉴 was ty\nee = 一 A 『 ll 盛';
    expect(guessNameFromText(text)).toBe('');
  });

  it('rejects a noise-symbol line even when a clean line is also present, picking the clean one', () => {
    const text = 'ee = 一 A 『 ll 盛\n真实产品名称测试';
    expect(guessNameFromText(text)).toBe('真实产品名称测试');
  });

  it('rejects very short fragments even if they contain no noise symbols', () => {
    expect(guessNameFromText('a LL\nva')).toBe('');
  });

  it('rejects lines that are mostly whitespace relative to their content', () => {
    const text = 'yr 院 , M ron';
    expect(guessNameFromText(text)).toBe('');
  });
});
