const levels: Record<string, string> = {
  prepa: 'Préparatoire', licence: 'Licence', ingenieur: 'Ingénieur',
  mastere: 'Mastère', mba: 'MBA', architecture: 'Architecture',
}
const languages: Record<string, string> = { fr: 'Français', en: 'Anglais', ar: 'Arabe' }

export const programLevelName = (value: string) => levels[value] || value
export const teachingLanguageName = (value: string) => languages[value] || value
