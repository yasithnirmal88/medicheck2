import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ContentEditorRoute from '../ContentEditorRoute'

const { createAsync, updateAsync, contentItem } = vi.hoisted(() => ({
  createAsync: vi.fn(),
  updateAsync: vi.fn(),
  contentItem: vi.fn(),
}))

vi.mock('../../hooks/useCmsQueries', () => ({
  useContentItem: contentItem,
  useCreateContent: () => ({ mutateAsync: createAsync, isPending: false }),
  useUpdateContent: () => ({ mutateAsync: updateAsync, isPending: false }),
}))

describe('ContentEditorRoute', () => {
  beforeEach(() => {
    createAsync.mockReset().mockResolvedValue({})
    updateAsync.mockReset().mockResolvedValue({})
    contentItem.mockReset().mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    })
  })

  it('creates content through the CMS mutation and returns to its list', async () => {
    render(
      <MemoryRouter initialEntries={['/cms/content/disease/new']}>
        <Routes>
          <Route path="/cms/content/:entityType/new" element={<ContentEditorRoute />} />
          <Route path="/cms/diseases" element={<p>Disease list</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: '{"name":"Test disease","code":"test-disease"}' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(createAsync).toHaveBeenCalledWith({
        name: 'Test disease',
        code: 'test-disease',
      })
    })
    expect(await screen.findByText('Disease list')).toBeInTheDocument()
  })
})
