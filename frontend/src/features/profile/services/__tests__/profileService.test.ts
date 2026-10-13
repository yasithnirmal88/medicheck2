import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createDefaultState } from '../../state/defaults'

const { post } = vi.hoisted(() => ({ post: vi.fn() }))

vi.mock('@/lib/api', () => ({
  default: { post },
}))

import { saveProfileData } from '../profileService'

describe('saveProfileData', () => {
  beforeEach(() => {
    post.mockReset().mockResolvedValue({ data: {} })
  })

  it('submits personal details through the authenticated profile API route', async () => {
    const state = createDefaultState()
    state.personal.first_name = 'Ada'
    state.personal.last_name = 'Patient'

    await saveProfileData(state)

    expect(post).toHaveBeenCalledWith('/profiles/me/personal', expect.objectContaining({
      full_name: 'Ada Patient',
    }))
  })
})
