type ScoreInputItem = {
  label?: string
  value?: string
  item_name?: string
  calc_mode?: string | null
}

const includesAny = (text: string, keywords: string[]) => keywords.some((keyword) => text.includes(keyword))

const getItemName = (item?: ScoreInputItem | null) => String(item?.item_name || item?.label || '').trim()

export const getScoreInputPlaceholder = (item?: ScoreInputItem | null) => {
  if (!item) return '成绩'

  const code = String(item.value || '').toLowerCase()
  const name = getItemName(item)
  const signature = `${code} ${name}`.toLowerCase()

  if (code === 'height' || includesAny(signature, ['身高'])) {
    return 'cm'
  }
  if (code === 'weight' || includesAny(signature, ['体重'])) {
    return 'kg'
  }
  if (code === 'bmi' || includesAny(signature, ['bmi'])) {
    return 'BMI'
  }
  if (code === 'lung' || includesAny(signature, ['肺活量'])) {
    return 'ml'
  }
  if (code === 'sit' || includesAny(signature, ['坐位体前屈'])) {
    return 'cm，可负数'
  }
  if (includesAny(signature, ['跳绳', '引体向上', '仰卧起坐']) || includesAny(code, ['rope', 'pull_up', 'sit_up'])) {
    return '次'
  }
  if (includesAny(signature, ['跳远', '实心球', '掷实心球']) || includesAny(code, ['jump', 'ball'])) {
    return '米'
  }
  if (
    includesAny(signature, ['跑', '游泳', '50米', '100米', '800米', '1000米']) ||
    includesAny(code, ['run', '50m', '100m', '800m', '1000m', 'swim'])
  ) {
    return '秒/分秒'
  }
  if (String(item.calc_mode || '').toLowerCase() === 'record') {
    return '原始值'
  }
  return '原始成绩'
}
