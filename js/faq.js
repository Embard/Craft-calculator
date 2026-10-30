/* The questions remain readable through native details without JavaScript. */
(() => {
  const faq = document.getElementById('faq');
  if (!faq) return;
  const trigger = faq.querySelector('.faq-trigger');
  const search = faq.querySelector('#faq-search');
  const clear = faq.querySelector('.faq-clear');
  const close = faq.querySelector('.faq-close');
  const status = faq.querySelector('.faq-status');
  const list = faq.querySelector('.faq-list');
  const empty = faq.querySelector('.faq-empty');
  const normalize = text => text.toLocaleLowerCase('ru').replace(/ё/g, 'е').trim();
  const categories = [...faq.querySelectorAll('.faq-category')].map(element => ({
    element,
    title: normalize(element.querySelector('summary > span').textContent),
    count: element.querySelector('.faq-count'),
    questions: [...element.querySelectorAll('.faq-question')].map(question => ({
      element: question,
      text: normalize(question.textContent)
    }))
  }));
  const initialStatus = status.textContent;
  let savedOpenState = null;

  function filter() {
    const tokens = normalize(search.value).split(/\s+/).filter(Boolean);
    if (tokens.length && !savedOpenState) {
      savedOpenState = categories.map(category => category.element.open);
    }
    let matches = 0;
    let groups = 0;
    categories.forEach((category, index) => {
      let count = 0;
      category.questions.forEach(question => {
        const haystack = category.title + ' ' + question.text;
        const match = tokens.every(token => haystack.includes(token));
        question.element.hidden = !match;
        if (match) count++;
      });
      category.element.hidden = !count;
      if (tokens.length) category.element.open = count > 0;
      else if (savedOpenState) category.element.open = savedOpenState[index];
      category.count.textContent = count;
      category.count.setAttribute('aria-label', 'Вопросов: ' + count);
      matches += count;
      if (count) groups++;
    });
    if (!tokens.length) savedOpenState = null;
    clear.hidden = !search.value;
    empty.hidden = matches > 0;
    status.textContent = tokens.length
      ? `Найдено вопросов: ${matches} · Категорий: ${groups}`
      : initialStatus;
    list.scrollTop = 0;
  }

  function dismiss(restoreFocus = false) {
    faq.open = false;
    if (restoreFocus) trigger.focus({ preventScroll: true });
  }

  search.addEventListener('input', filter);
  clear.addEventListener('click', () => {
    search.value = '';
    filter();
    search.focus({ preventScroll: true });
  });
  close.addEventListener('click', () => dismiss(true));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && faq.open) {
      event.preventDefault();
      dismiss(true);
    }
  });
  document.addEventListener('click', event => {
    if (faq.open && !faq.contains(event.target)) dismiss();
  });
  faq.addEventListener('focusout', event => {
    if (faq.open && event.relatedTarget && !faq.contains(event.relatedTarget)) dismiss();
  });
  faq.querySelector('.faq-search').hidden = false;
  close.hidden = false;
})();
