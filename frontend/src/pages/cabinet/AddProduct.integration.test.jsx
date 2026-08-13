// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

vi.mock('../../api/coreApi.js', () => ({
  coreApi: {
    getCategories: vi.fn().mockResolvedValue(['护肤', '彩妆', '身体护理']),
    createProduct: vi.fn().mockResolvedValue({ id: 1 }),
    updateProduct: vi.fn().mockResolvedValue({ id: 1 }),
    uploadImage: vi.fn().mockResolvedValue({ url: '/uploads/x.jpg' })
  },
  resolveUploadUrl: vi.fn((u) => u)
}));

vi.mock('../../api/openBeautyFacts.js', () => ({
  searchOpenBeautyFacts: vi.fn(),
  matchKnownIngredients: vi.fn((text) => ((text || '').toLowerCase().includes('niacinamide') ? ['烟酰胺'] : [])),
  getProductByBarcode: vi.fn()
}));

// Simulates an instantly-successful scan so the downstream apply-to-form
// logic can be tested without a real camera/video pipeline.
vi.mock('./BarcodeScanner.jsx', () => ({
  default: ({ onDetected }) => {
    React.useEffect(() => {
      onDetected('6111234567890');
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    return <div data-testid="mock-scanner" />;
  }
}));

import AddProduct from './AddProduct.jsx';
import { coreApi } from '../../api/coreApi.js';
import { getProductByBarcode } from '../../api/openBeautyFacts.js';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('AddProduct — barcode scan', () => {
  it('applies product name/brand/ingredients to the form once a scanned barcode resolves', async () => {
    getProductByBarcode.mockResolvedValue({
      product_name: 'COSRX Snail Cream',
      brands: 'COSRX',
      ingredients_text: 'Niacinamide, Aqua',
      ingredients_text_zh: ''
    });

    render(<AddProduct onSaved={vi.fn()} onProductAdded={vi.fn()} />);

    fireEvent.click(screen.getByText('📷 扫外包装条码'));

    await waitFor(() => expect(screen.getByLabelText('产品名称').value).toBe('COSRX Snail Cream'));
    expect(screen.getByLabelText('品牌').value).toBe('COSRX');
    expect(screen.getByText(/条码精确匹配到/)).toBeInTheDocument();
    expect(getProductByBarcode).toHaveBeenCalledWith('6111234567890');
  });

  it('shows a not-found message when the barcode has no match', async () => {
    getProductByBarcode.mockResolvedValue(null);

    render(<AddProduct onSaved={vi.fn()} onProductAdded={vi.fn()} />);
    fireEvent.click(screen.getByText('📷 扫外包装条码'));

    await waitFor(() => expect(screen.getByText(/没有在 Open Beauty Facts 数据库里找到/)).toBeInTheDocument());
  });

  it("doesn't overwrite a name the user already typed", async () => {
    getProductByBarcode.mockResolvedValue({
      product_name: 'COSRX Snail Cream',
      brands: 'COSRX',
      ingredients_text: '',
      ingredients_text_zh: ''
    });

    render(<AddProduct onSaved={vi.fn()} onProductAdded={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('产品名称'), { target: { value: '我自己填的名字' } });
    fireEvent.click(screen.getByText('📷 扫外包装条码'));

    await waitFor(() => expect(screen.getByText(/条码精确匹配到/)).toBeInTheDocument());
    expect(screen.getByLabelText('产品名称').value).toBe('我自己填的名字');
  });
});

describe('AddProduct — continuous entry mode', () => {
  it('stays on the form after creating, tracks a running count, and only navigates away via 完成', async () => {
    const onSaved = vi.fn();
    const onProductAdded = vi.fn();
    window.scrollTo = vi.fn();

    render(<AddProduct onSaved={onSaved} onProductAdded={onProductAdded} />);

    await waitFor(() => expect(screen.getByLabelText('分类').value).toBe('护肤'));
    fireEvent.change(screen.getByLabelText('产品名称'), { target: { value: '测试产品' } });
    fireEvent.click(screen.getByText('保存产品'));

    await waitFor(() => expect(coreApi.createProduct).toHaveBeenCalledTimes(1));
    expect(onSaved).not.toHaveBeenCalled();
    expect(onProductAdded).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByText(/已连续添加 1 件/)).toBeInTheDocument());
    expect(screen.getByLabelText('产品名称').value).toBe('');

    fireEvent.click(screen.getByText('完成 →'));
    expect(onSaved).toHaveBeenCalledTimes(1);
  });

  it('edit mode still navigates away immediately via onSaved (no continuous banner)', async () => {
    const onSaved = vi.fn();
    render(
      <AddProduct
        editingProduct={{ id: 5, name: '旧名字', category: '护肤', openedDate: '2026-01-01', paoMonths: 12, ingredientTags: [], costCNY: 0 }}
        onSaved={onSaved}
        onCancel={vi.fn()}
      />
    );

    await waitFor(() => expect(screen.getByLabelText('产品名称').value).toBe('旧名字'));
    fireEvent.click(screen.getByText('保存修改'));

    await waitFor(() => expect(coreApi.updateProduct).toHaveBeenCalledWith(5, expect.any(Object)));
    expect(onSaved).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/已连续添加/)).not.toBeInTheDocument();
  });
});
