// Shared labels and lookups for the web pages.

export const TACTICS = {
  urgency: { en: 'Urgency', hi: 'जल्दबाज़ी', tone: 'amber', hint: 'Rushing you so you cannot think' },
  authority: { en: 'Authority', hi: 'अफ़सरी रौब', tone: 'blue', hint: 'Official-sounding title to make you obey' },
  isolation: { en: 'Isolation', hi: 'अकेला करना', tone: 'purple', hint: 'Keeping you away from people who could help' },
  fear: { en: 'Fear', hi: 'डर', tone: 'red', hint: 'Threats of arrest or punishment' },
  secrecy: { en: 'Secrecy', hi: 'गोपनीयता', tone: 'purple', hint: 'Telling you to tell nobody' },
  payment_push: { en: 'Payment push', hi: 'पैसे का दबाव', tone: 'red', hint: 'Asking for money to "fix" the problem' },
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

// Hindi text for the result card, keyed by the codes the API already sends (no API change).
// A code missing here falls back to the English text from the API.
export const HI = {
  risk: {
    high: 'ज़्यादा खतरा: यह लगभग पक्का धोखाधड़ी है',
    medium: 'मध्यम खतरा: सावधान रहें',
    low: 'कम खतरा: कुछ गड़बड़ नहीं दिखी',
  },
  types: {
    digital_arrest: 'डिजिटल अरेस्ट', kyc_update: 'केवाईसी अपडेट', upi_collect: 'यूपीआई कलेक्ट रिक्वेस्ट',
    job_offer: 'फर्जी नौकरी का ऑफर', courier_customs: 'कूरियर / कस्टम्स', investment: 'निवेश योजना',
    fake_scheme: 'फर्जी सरकारी योजना', lottery_prize: 'लॉटरी / इनाम', loan_app: 'लोन ऐप',
    malicious_apk: 'खतरनाक ऐप (APK)', phishing_link: 'फ़िशिंग लिंक', unknown: 'साफ़ नहीं', not_scam: 'सुरक्षित लगता है',
  },
  actions: {
    ignore: 'इसे अनदेखा करें।',
    report_chakshu: 'चक्षु (संचार साथी) पर इसकी शिकायत करें।',
    call_1930: 'अभी 1930 पर कॉल करें।',
    do_not_install: 'इसे इंस्टॉल न करें।',
    verify_official: 'खुद आधिकारिक नंबर पर कॉल करके पुष्टि करें।',
    none: 'कुछ करने की ज़रूरत नहीं।',
  },
  flags: {
    otp_request: 'यह आपका ओटीपी या यूपीआई पिन माँगता है। कोई बैंक, पुलिस या कंपनी ये कभी नहीं माँगती।',
    threat_arrest: 'यह आपको गिरफ़्तारी या पुलिस केस की धमकी देता है। असली पुलिस कॉल या मैसेज पर ऐसा कभी नहीं करती।',
    isolation: 'यह आपको बात छिपाने या कॉल पर बने रहने को कहता है, ताकि कोई आपको सावधान न कर सके।',
    urgency: 'यह आपको जल्दबाज़ी में डालता है, ताकि आप सोचने या जाँचने से पहले कदम उठा लें।',
    payment_request: 'यह आपसे पैसे भेजने या ट्रांसफर करने को कहता है।',
    kyc: 'बैंक कभी भी मैसेज या लिंक से केवाईसी या पैन अपडेट करने को नहीं कहते।',
    too_good: 'यह ऑफर सच होने के लिए बहुत अच्छा है: आसान कमाई, इनाम या पक्का मुनाफ़ा।',
    authority_claim: 'यह डराने के लिए पुलिस, कस्टम्स या किसी सरकारी दफ़्तर से होने का दावा करता है।',
    personal_data: 'यह आधार, बैंक या कार्ड की जानकारी माँगता है।',
    collect_request: 'पैसे पाने के लिए कभी पिन डालना या क्यूआर कोड स्कैन करना नहीं पड़ता। यह रिक्वेस्ट आपके पैसे ले लेगी।',
    apk_link: 'यह आपसे लिंक से ऐप इंस्टॉल करवाना चाहता है। ऐप सिर्फ़ प्ले स्टोर से इंस्टॉल करें।',
    shame_threat: 'यह आपको आपके कॉन्टैक्ट्स के सामने बदनाम करने की धमकी देता है। यह ब्लैकमेल है, इसकी शिकायत करें।',
    contraband_claim: 'यह दावा करता है कि आपके नाम के पार्सल या खाते में ड्रग्स या अवैध सामान मिला है। कस्टम्स और पुलिस इसके लिए फ़ोन नहीं करते।',
    parcel_seized: 'यह कहता है कि आपके नाम का पार्सल रोका या ज़ब्त किया गया है। नकली "कस्टम्स" कॉल ऐसे ही शुरू होती हैं।',
    prompt_injection: 'इसमें छिपे निर्देश हैं जो स्कैम जाँचने वाले सिस्टम को धोखा देने के लिए हैं। असली मैसेज में ऐसा नहीं होता।',
    press_key: 'रिकॉर्डेड कॉल जो "अधिकारी" से बात करने के लिए कोई बटन दबाने को कहे, आम धोखाधड़ी की शुरुआत है।',
    blocklisted_link: 'यह लिंक धोखाधड़ी वाली वेबसाइटों की सूची में है।',
    lookalike_domain: 'यह लिंक किसी असली वेबसाइट की नकल है।',
    new_domain: 'यह वेबसाइट हाल ही में बनी है। धोखेबाज़ अक्सर नई वेबसाइटें इस्तेमाल करते हैं।',
    suspicious_domain: 'इस लिंक का पता संदिग्ध है।',
    scam_pattern: 'यह जाने-पहचाने धोखाधड़ी के तरीके से मेल खाता है।',
    apk_dangerous_combo: 'यह ऐप ऐसी अनुमतियाँ माँगता है जिनसे वह आपके ओटीपी पढ़ सकता है।',
    apk_sms_permission: 'यह ऐप आपके एसएमएस पढ़ना चाहता है।',
    apk_name_mismatch: 'इस ऐप का नाम किसी असली ऐप जैसा है, पर यह वह ऐप नहीं है।',
    apk_unknown_source: 'यह ऐप प्ले स्टोर से नहीं है।',
    apk_virustotal: 'सुरक्षा स्कैनरों ने इस ऐप को खतरनाक बताया है।',
    apk_unreadable: 'यह फ़ाइल पढ़ी नहीं जा सकी। इसे इंस्टॉल न करें।',
    unreadable_image: 'इस स्क्रीनशॉट का टेक्स्ट पढ़ा नहीं जा सका, इसलिए इसकी जाँच नहीं हो पाई।',
    ask_click: 'यह आपसे लिंक पर क्लिक करवाना चाहता है।',
    ask_pay: 'यह फ़ायदा देने के बदले पैसे माँगता है।',
    ask_register: 'यह किसी अनाधिकारिक वेबसाइट पर रजिस्टर करने को कहता है।',
    ask_otp: 'यह ओटीपी माँगता है। सरकारी योजनाओं में कभी ओटीपी नहीं चाहिए।',
    ask_aadhaar: 'यह आधार या बैंक की जानकारी माँगता है।',
    ask_share: 'यह इसे दूसरों को फ़ॉरवर्ड करने को कहता है: फर्जी ख़बर का आम संकेत।',
  },
  ui: {
    scoreOf: 'खतरा स्कोर, 100 में से',
    lower: 'सिर्फ़ जल्दी जाँच: पूरी एआई जाँच उपलब्ध नहीं थी, इसलिए ज़्यादा सावधानी रखें।',
    why: 'क्यों',
    found: 'हमें क्या मिला',
    todo: 'क्या करें:',
    report: 'संचार साथी पर शिकायत करें',
    dial: '1930 डायल करें',
    paid: 'अगर आप पैसे दे चुके हैं या कोई कोड बता चुके हैं, तो अभी 1930 पर कॉल करें।',
  },
}

// Circle radius for a heatmap marker: grows with reports but stays readable.
export const alertRadius = (count) => Math.min(60, 12 + Math.sqrt(Math.max(0, count)) * 6)

export const SAMPLE_KYC =
  'Dear customer, your SBI account will be blocked today. Update KYC immediately at http://sbi-kyc-update.example and share the OTP you receive.'

export const SAMPLE_HI =
  'प्रिय ग्राहक, आपका एसबीआई खाता आज ही ब्लॉक हो जाएगा। केवाईसी अपडेट करने के लिए http://sbi-kyc-update.example पर जाएं और तुरंत अपना ओटीपी बताएं।'

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
