export const useSettingsDialog = () => {
  const open = useState('settings-dialog-open', () => false)
  const targetSection = useState('settings-dialog-target-section', () => '')

  const openDialog = (section = '') => {
    if (typeof section === 'string') {
      targetSection.value = section
    } else if (section && typeof section === 'object') {
      targetSection.value = String(section.section || section.targetSection || '')
    } else {
      targetSection.value = ''
    }
    open.value = true
  }

  const closeDialog = () => {
    open.value = false
  }

  return {
    open,
    targetSection,
    openDialog,
    closeDialog,
  }
}
