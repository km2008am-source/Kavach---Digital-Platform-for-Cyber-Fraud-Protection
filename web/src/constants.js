// Shared labels and lookups for the web pages.

export const TACTICS = {
  urgency: { en: 'Urgency', ta: 'அவசரம்', tone: 'amber', hint: 'Rushing you so you cannot think' },
  authority: { en: 'Authority', ta: 'அதிகாரம்', tone: 'blue', hint: 'Official-sounding title to make you obey' },
  isolation: { en: 'Isolation', ta: 'தனிமைப்படுத்தல்', tone: 'purple', hint: 'Keeping you away from people who could help' },
  fear: { en: 'Fear', ta: 'பயம்', tone: 'red', hint: 'Threats of arrest or punishment' },
  secrecy: { en: 'Secrecy', ta: 'ரகசியம்', tone: 'purple', hint: 'Telling you to tell nobody' },
  payment_push: { en: 'Payment push', ta: 'பணம் கேட்பு', tone: 'red', hint: 'Asking for money to "fix" the problem' },
}

export const SCAM_TYPES = {
  digital_arrest: 'Digital arrest', kyc_update: 'KYC update', upi_collect: 'UPI collect request',
  job_offer: 'Fake job offer', courier_customs: 'Courier / customs', investment: 'Investment scheme',
  fake_scheme: 'Fake government scheme', lottery_prize: 'Lottery / prize', loan_app: 'Loan app',
  malicious_apk: 'Malicious app (APK)', phishing_link: 'Phishing link', unknown: 'Unclear', not_scam: 'Looks safe',
}

export const ACTIONS = {
  ignore: 'Ignore it.',
  report_chakshu: 'Report it on Chakshu (Sanchar Saathi).',
  call_1930: 'Dial 1930 now.',
  do_not_install: 'Do not install it.',
  verify_official: 'Check with the official number yourself.',
  none: 'No action needed.',
}

export const SITUATIONS = [
  ['lost_money', 'I lost money'],
  ['suspicious', 'I got a suspicious call or message'],
  ['lost_phone', 'I lost my phone'],
  ['id_misuse', 'Someone is using my ID'],
  ['investment', 'An investment scheme looks illegal'],
]

// Fixed coordinates for the heatmap (section 8-G): the API only ever sends district names.
export const DISTRICTS = {
  Chennai: [13.0827, 80.2707], Coimbatore: [11.0168, 76.9558], Madurai: [9.9252, 78.1198],
  Tiruchirappalli: [10.7905, 78.7047], Salem: [11.6643, 78.146], Tirunelveli: [8.7139, 77.7567],
  Erode: [11.341, 77.7172], Vellore: [12.9165, 79.1325], Thanjavur: [10.787, 79.1378],
  Tiruppur: [11.1085, 77.3411], Thoothukudi: [8.7642, 78.1348], Kanyakumari: [8.0883, 77.5385],
  Ramanathapuram: [9.3639, 78.8395], Dindigul: [10.3673, 77.9803], Kancheepuram: [12.8342, 79.7036],
}

export const districtPos = (name) => DISTRICTS[name] ?? null

export const riskTone = (level) => ({ high: 'red', medium: 'amber', low: 'green' })[level] ?? 'amber'

export const RISK_TEXT = {
  high: 'High risk: very likely a scam',
  medium: 'Medium risk: be careful',
  low: 'Low risk: nothing obviously wrong',
}

// Circle radius for a heatmap marker: grows with reports but stays readable.
export const alertRadius = (count) => Math.min(60, 12 + Math.sqrt(Math.max(0, count)) * 6)

export const SAMPLE_KYC =
  'Dear customer, your SBI account will be blocked today. Update KYC immediately at http://sbi-kyc-update.example and share the OTP you receive.'

// Person 1's /api/services sends { name, situation (sentence), description, official_url };
// the demo file uses { situation (key), what, when, link }. Accept both shapes.
const SITUATION_WORDS = [
  ['lost_money', /lost money|paid|fraud|scam/i],
  ['lost_phone', /phone was lost|lost my phone|stolen/i],
  ['id_misuse', /identity|my id|aadhaar|pan/i],
  ['investment', /investment|deposit|scheme/i],
  ['suspicious', /suspicious|call|sms|message/i],
]

export function normalizeService(item) {
  if (!item || typeof item !== 'object') return null
  const known = SITUATIONS.some(([k]) => k === item.situation)
  const situation = known
    ? item.situation
    : (SITUATION_WORDS.find(([, re]) => re.test(item.situation || ''))?.[0] ?? 'other')
  return {
    ...item,
    situation,
    what: item.what ?? item.description ?? '',
    when: item.when ?? (known ? '' : item.situation ?? ''),
    link: item.link ?? item.official_url,
  }
}
