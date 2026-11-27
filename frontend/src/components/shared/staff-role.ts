export const staffRoleName = (role?: string) => ({ interviewer: 'Responsable entretiens et rendez-vous', admin: 'Administrateur' } as Record<string, string>)[role || ''] || 'Staff'
