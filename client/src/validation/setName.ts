export const getSetNameError = (value: string, showRequired: boolean) => {
  const name = value.trim()

  if (showRequired && !name) return 'required'
  if ([...name].length > 255) return 'tooLong'
}
