export const isLatinQuery = (text: string) => {
  const letters = text.normalize('NFKC').match(/\p{Letter}/gu)

  return Boolean(letters?.length && letters.every((letter) => /\p{Script=Latin}/u.test(letter)))
}

export const normalizeLatinQuery = (text: string) =>
  text
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s,-]/gu, '')
