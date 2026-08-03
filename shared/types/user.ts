export type Role = 'patient' | 'doctor' | 'researcher' | 'administrator'

export interface IUser {
  id: string // UUID
  email: string
  fullName?: string
  roles: Role[]
  createdAt: string // ISO timestamp
  updatedAt?: string
  deletedAt?: string | null
}
