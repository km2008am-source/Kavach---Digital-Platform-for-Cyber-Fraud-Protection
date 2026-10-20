import { TACTICS } from '../constants.js'

export default function TacticChip({ code, lang = 'en' }) {
  const t = TACTICS[code]
  if (!t) return null
  return (
    <span className={`chip chip-${t.tone}`} title={t.hint}>
      {t[lang] ?? t.en}
    </span>
  )
}
